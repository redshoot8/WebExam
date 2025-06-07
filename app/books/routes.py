import hashlib
import os
import bleach
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Book, Review, Genre, Cover
from forms import BookForm, BookSearchForm, ReviewForm
from config import Config

bp = Blueprint('books', __name__, url_prefix='/books')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@bp.route('/')
def index():
    form = BookSearchForm(request.args, meta={'csrf': False})
    form.genres.choices = [(g.id, g.name) for g in Genre.query.all()]
    years = [year[0] for year in db.session.query(Book.year).distinct()]
    form.year.choices = [(y, y) for y in sorted(years, reverse=True)]

    query = Book.query

    if request.args:
        # Фильтрация по названию (частичное совпадение)
        if form.title.data:
            query = query.filter(Book.title.ilike(f'%{form.title.data}%'))

        # Фильтрация по жанрам
        if form.genres.data:
            query = query.join(Book.genres).filter(Genre.id.in_(form.genres.data))

        # Фильтрация по году
        if form.year.data:
            query = query.filter(Book.year.in_(form.year.data))

        # Фильтрация по объёму
        if form.pages_min.data is not None:
            query = query.filter(Book.pages >= form.pages_min.data)
        if form.pages_max.data is not None:
            query = query.filter(Book.pages <= form.pages_max.data)

        # Фильтрация по автору
        if form.author.data:
            query = query.filter(Book.author.ilike(f'%{form.author.data}%'))
    
    page = request.args.get('page', 1, type=int)
    books = query.order_by(Book.year.desc()).paginate(page=page, per_page=10)
    return render_template('index.html', books=books, form=form)


@bp.route('/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book_detail.html', book=book)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_book():
    if current_user.role.id not in [3]:
        abort(403)
    form = BookForm()
    form.genres.choices = [(g.id, g.name) for g in Genre.query.all()]
    if form.validate_on_submit():
        book = Book(
            title=form.title.data,
            description=bleach.clean(form.description.data),
            year=form.year.data,
            publisher=form.publisher.data,
            author=form.author.data,
            pages=form.pages.data
        )
        
        selected_genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()
        book.genres = selected_genres
        
        if not form.cover.data:
            flash('Загрузите обложку книги', 'danger')
            return render_template('book_form.html', form=form)
        
        file = form.cover.data
        if file and allowed_file(file.filename):
            md5 = hashlib.md5(file.read()).hexdigest()
            file.seek(0)
            existing_cover = Cover.query.filter_by(md5_hash=md5).first()
            if not existing_cover:
                filename = secure_filename(file.filename)
                cover = Cover(
                    filename=filename,
                    mime_type=file.mimetype,
                    md5_hash=md5
                )
                db.session.add(cover)
                book.cover = cover
                file.save(os.path.join(Config.UPLOAD_FOLDER, filename))
                
        db.session.add(book)
        db.session.commit()
        flash('Книга успешно добавлена', 'success')
        return redirect(url_for('books.book_detail', book_id=book.id))
    return render_template('book_form.html', form=form, title='Добавить книгу', is_edit=False)


@bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if current_user.role.id not in [2, 3]:
        abort(403)
    form = BookForm(obj=book)
    form.genres.choices = [(g.id, g.name) for g in Genre.query.all()]
    if form.validate_on_submit():
        book.title = form.title.data
        book.description = bleach.clean(form.description.data)
        book.year = form.year.data
        book.publisher = form.publisher.data
        book.author = form.author.data
        book.pages = form.pages.data
        selected_genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()
        book.genres = selected_genres
        db.session.commit()
        flash('Книга успешно обновлена', 'success')
        return redirect(url_for('books.book_detail', book_id=book.id))
    form.genres.data = [g.id for g in book.genres]
    return render_template('book_form.html', form=form, title='Редактировать книгу', is_edit=True)


@bp.route('/<int:book_id>/delete', methods=['POST'])
@login_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if current_user.role.id not in [3]:
        abort(403)
    db.session.delete(book)
    db.session.commit()
    flash('Книга успешно удалена', 'success')
    return redirect(url_for('books.index'))


@bp.route('/<int:book_id>/reviews/create', methods=['GET', 'POST'])
@login_required
def create_review(book_id):
    if current_user.role.name not in ['Пользователь', 'Модератор', 'Администратор']:
        abort(403)
    
    book = Book.query.get_or_404(book_id)
    
    # Проверка существующей рецензии
    existing_review = Review.query.filter_by(
        book_id=book.id, 
        user_id=current_user.id
    ).first()
    
    if existing_review:
        flash('Вы уже оставили рецензию на эту книгу', 'warning')
        return redirect(url_for('books.book_detail', book_id=book.id))
    
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            rating=form.rating.data,
            text=bleach.clean(form.text.data),
            book_id=book.id,
            user_id=current_user.id
        )
        db.session.add(review)
        db.session.commit()
        flash('Рецензия успешно сохранена', 'success')
        return redirect(url_for('books.book_detail', book_id=book.id))
    
    return render_template('review_form.html', form=form, book=book)

@bp.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id and current_user.role.id not in [2, 3]:
        abort(403)
    db.session.delete(review)
    db.session.commit()
    flash('Рецензия удалена', 'success')
    return redirect(url_for('books.book_detail', book_id=review.book_id))

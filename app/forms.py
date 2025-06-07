from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, SelectMultipleField, SelectField, FileField, 
    TextAreaField, PasswordField, BooleanField, validators
)
from wtforms.validators import EqualTo, ValidationError, DataRequired, InputRequired
from models import User


class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    

class RegistrationForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[
        DataRequired(), 
        EqualTo('password', message='Пароли должны совпадать')
    ])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    first_name = StringField('Имя', validators=[DataRequired()])
    middle_name = StringField('Отчество')
    
    def validate_login(self, field):
        if User.query.filter_by(login=field.data).first():
            raise ValidationError('Пользователь с таким логином уже существует')


class BookForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    year = IntegerField('Год', validators=[DataRequired()])
    publisher = StringField('Издательство', validators=[DataRequired()])
    author = StringField('Автор', validators=[DataRequired()])
    pages = IntegerField('Страницы', validators=[DataRequired()])
    genres = SelectMultipleField('Жанры', coerce=int, validators=[InputRequired(message='Выберите хотя бы один жанр')])
    cover = FileField('Обложка')
    

class BookSearchForm(FlaskForm):
    title = StringField('Название')
    genres = SelectMultipleField('Жанры', coerce=int)
    year = SelectMultipleField('Год', coerce=int)
    pages_min = IntegerField('Объём от')
    pages_max = IntegerField('до')
    author = StringField('Автор')


class ReviewForm(FlaskForm):
    rating = SelectField(
        'Оценка',
        choices=[
            (5, 'Отлично'), (4, 'Хорошо'), (3, 'Удовлетворительно'),
            (2, 'Неудовлетворительно'), (1, 'Плохо'), (0, 'Ужасно')
        ],
        coerce=int,
        default=5,
        validators=[validators.DataRequired()]
    )
    text = TextAreaField(
        'Текст рецензии', 
        validators=[validators.DataRequired()],
        render_kw={'rows': 10}
    )

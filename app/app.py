import markdown
from markupsafe import Markup
from flask import Flask, render_template
from flask_login import current_user, LoginManager
from config import Config
from models import db, User
from auth.routes import bp as auth_bp
from books.routes import bp as books_bp
from flask_migrate import Migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Для доступа к данной странице необходимо пройти процедуру аутентификации.'
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(User.load_user)
    login_manager.init_app(app)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    
    return app


app = create_app()
migrate = Migrate(app, db)


@app.template_filter('markdown')
def markdown_filter(text):
    extensions = ['nl2br', 'fenced_code', 'tables']
    html = markdown.markdown(text, extensions=extensions)
    return Markup(html)


# Инъекция пользователя
@app.context_processor
def inject_current_user():
    return dict(current_user=current_user)


# Обработчики ошибок
@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

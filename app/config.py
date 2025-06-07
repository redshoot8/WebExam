import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    BASE_DIR = Path(__file__).parent
    DB_PATH = os.path.join(BASE_DIR, 'instance', 'library.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = BASE_DIR / 'static' / 'covers'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

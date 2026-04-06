import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///red_dirt_utv.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Single-user password — set SHOP_PASSWORD env var in production
    SHOP_PASSWORD = os.environ.get('SHOP_PASSWORD', 'reddirt2024')
    SHOP_NAME = 'Red Dirt UTV Performance'
    SHOP_ADDRESS = 'Waller, TX'
    SHOP_PHONE = os.environ.get('SHOP_PHONE', '')
    SHOP_EMAIL = os.environ.get('SHOP_EMAIL', '')
    # Photo uploads
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

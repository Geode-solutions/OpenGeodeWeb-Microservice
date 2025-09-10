import os
from .database.connection import DATABASE_FILENAME


class Config:
    pass


class ProdConfig(Config):
    DATA_FOLDER_PATH = "/data"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.abspath(
        os.path.join(DATA_FOLDER_PATH, DATABASE_FILENAME)
        )}"


class DevConfig(Config):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER_PATH = os.path.join(BASE_DIR, "data")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(
        BASE_DIR, DATA_FOLDER_PATH, DATABASE_FILENAME
        )}"

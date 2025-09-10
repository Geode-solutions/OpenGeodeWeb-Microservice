"""Database connection management"""

from typing import Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from ..microservice.base import Base

DATABASE_FILENAME = "project.db"

db: Optional[SQLAlchemy] = None


def init_database(app: Flask, db_filename: str = DATABASE_FILENAME) -> SQLAlchemy:
    global db
    if db is None:
        db = SQLAlchemy(model_class=Base)
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return db


def get_database() -> Optional[SQLAlchemy]:
    return db


def get_session():
    if db is None:
        return None
    return db.session


def get_database_connection():
    return get_database()

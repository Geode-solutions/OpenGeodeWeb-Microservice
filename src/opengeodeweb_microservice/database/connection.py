"""Database connection management"""

from typing import Optional
from sqlalchemy.orm import scoped_session
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.session import Session
from .base import Base

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


def get_session() -> Optional[scoped_session[Session]]:
    return db.session if db else None

"""Database connection management"""

from typing import Optional
from sqlalchemy.orm import scoped_session
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.session import Session
from .base import Base

DATABASE_FILENAME = "project.db"
database: Optional[SQLAlchemy] = None


def init_database(app: Flask, db_filename: str = DATABASE_FILENAME) -> SQLAlchemy:
    global database
    if database is None:
        database = SQLAlchemy(model_class=Base)
    database.init_app(app)
    with app.app_context():
        database.create_all()
    return database


def get_database() -> Optional[SQLAlchemy]:
    return database


def get_session() -> Optional[scoped_session[Session]]:
    return database.session if database else None

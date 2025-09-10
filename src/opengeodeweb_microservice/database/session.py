from typing import Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .connection import DatabaseConnection

_database_connection = DatabaseConnection()


def init_database(app: Flask, database_filename: str = "project.db") -> SQLAlchemy:
    global _database_connection
    _database_connection.database_filename = database_filename
    return _database_connection.init_app(app)


def get_session() -> Optional[SQLAlchemy]:
    return _database_connection.get_database()


def get_database_connection() -> DatabaseConnection:
    return _database_connection

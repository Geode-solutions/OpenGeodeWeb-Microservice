"""Database connection management"""

from typing import Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from src.opengeodeweb_microservice.microservice.base import Base


class DatabaseConnection:

    def __init__(self, database_filename: str = "project.db"):
        self.database_filename = database_filename
        self.database: Optional[SQLAlchemy] = None

    def init_app(self, app: Flask) -> SQLAlchemy:
        if self.database is None:
            self.database = SQLAlchemy(model_class=Base)

        self.database.init_app(app)

        with app.app_context():
            self.database.create_all()

        return self.database

    def get_database(self) -> Optional[SQLAlchemy]:
        return self.database

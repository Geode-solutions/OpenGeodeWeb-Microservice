# # Standard library imports
# import time
# import shutil

# # Third party imports
# import os
# import pytest

# # Local application imports
# from app import app
# from src.opengeodeweb_microservice.database import initialize_database


# @pytest.fixture(scope="session", autouse=True)
# def copy_data():
#     app.config["DATA_FOLDER_PATH"] = "./data/"
#     BASE_DIR = os.path.abspath(os.path.dirname(__file__))
#     db_path = os.path.join(BASE_DIR, "data", "project.db")
#     app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
#     initialize_database(app)


# @pytest.fixture
# def client():
#     app.config["REQUEST_COUNTER"] = 0
#     app.config["LAST_REQUEST_TIME"] = time.time()
#     client = app.test_client()
#     client.headers = {"Content-type": "application/json", "Accept": "application/json"}
#     yield client


# @pytest.fixture
# def app_context():
#     with app.app_context():
#         yield

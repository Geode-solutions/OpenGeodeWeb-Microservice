# import os


# def test_database_uri_path(client):
#     app = client.application
#     with app.app_context():
#         base_dir = os.path.abspath(os.path.dirname(__file__))
#         expected_db_path = os.path.join(base_dir, "data", "project.db")
#         expected_uri = f"sqlite:///{expected_db_path}"

#         assert app.config["SQLALCHEMY_DATABASE_URI"] == expected_uri

#         assert os.path.exists(expected_db_path)

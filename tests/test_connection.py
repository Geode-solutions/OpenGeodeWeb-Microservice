from src.opengeodeweb_microservice.database.connection import get_session, get_database
from src.opengeodeweb_microservice.database.data import Data


def test_database_connection_basic(app_context):
    session = get_session()
    assert session is not None
    connection = get_database()
    assert connection is not None

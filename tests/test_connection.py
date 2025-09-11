from src.opengeodeweb_microservice.database.connection import (
    get_session,
    get_database_connection,
)
from src.opengeodeweb_microservice.microservice.data import Data


def test_database_connection_basic():
    session = get_session()
    assert session is not None
    connection = get_database_connection()
    assert connection is not None

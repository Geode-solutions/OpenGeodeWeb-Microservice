from sqlalchemy import String, JSON, select
from sqlalchemy.orm import Mapped, mapped_column
from .connection import get_session
from .base import Base
import uuid


class Data(Base):
    __tablename__ = "datas"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()).replace("-", "")
    )
    geode_object: Mapped[str] = mapped_column(String, nullable=False)
    viewer_object: Mapped[str] = mapped_column(String, nullable=False)

    native_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    viewable_filename: Mapped[str | None] = mapped_column(String, nullable=True)

    light_viewable_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    input_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    additional_filenames: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    @staticmethod
    def create(
        geode_object: str,
        viewer_object: str,
        input_filename: str | None = None,
        additional_filenames: list[str] | None = None,
    ) -> "Data":
        data_entry = Data(
            geode_object=geode_object,
            viewer_object=viewer_object,
            input_filename=input_filename,
            additional_filenames=additional_filenames,
        )

        session = get_session()
        session.add(data_entry)
        session.flush()
        return data_entry

    @staticmethod
    def get(data_id: str) -> "Data | None":
        session = get_session()
        data_query = select(Data).where(Data.id == data_id)
        return session.scalars(data_query).first()

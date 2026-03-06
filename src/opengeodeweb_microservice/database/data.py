from sqlalchemy import String, JSON, select
from sqlalchemy.orm import Mapped, mapped_column
from .connection import get_session
from .base import Base
from .data_types import GeodeObjectType, ViewerType, ViewerElementsType
import uuid


class Data(Base):
    __tablename__ = "datas"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()).replace("-", "")
    )
    geode_object: Mapped[GeodeObjectType] = mapped_column(String, nullable=False)
    viewer_object: Mapped[ViewerType] = mapped_column(String, nullable=False)
    viewer_elements_type: Mapped[ViewerElementsType] = mapped_column(
        String, nullable=False
    )
    native_file: Mapped[str | None] = mapped_column(String, nullable=True)
    viewable_file: Mapped[str | None] = mapped_column(String, nullable=True)
    light_viewable_file: Mapped[str | None] = mapped_column(String, nullable=True)

    @staticmethod
    def create(
        geode_object: GeodeObjectType,
        viewer_object: ViewerType,
        viewer_elements_type: ViewerElementsType,
    ) -> "Data":
        data_entry = Data(
            geode_object=geode_object,
            viewer_object=viewer_object,
            viewer_elements_type=viewer_elements_type,
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

from typing import List
from src.api.utils.database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String


class Category(db.Model):
    __bind_key__ = 'IMS_db'
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    raw_materials: Mapped[List['RawMaterial']] = relationship(  # type: ignore
        'RawMaterial',
        back_populates='category'
    )

    def __init__(self, name):
        self.name = name

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

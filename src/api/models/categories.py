from src.api.utils.database import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class Category(db.Model):
    __bind_key__ = 'IMS_db'
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    def __init__(self, name):
        self.name = name

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

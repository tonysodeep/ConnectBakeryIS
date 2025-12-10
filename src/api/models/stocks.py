from src.api.utils.database import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer


class Stock(db.Model):
    __bind_key__ = 'IMS_db'
    __tablename__ = 'stocks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(60), nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)

    def __init__(self, code, max_capacity=None, location=None):
        self.code = code
        self.max_capacity = max_capacity
        self.location = location

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

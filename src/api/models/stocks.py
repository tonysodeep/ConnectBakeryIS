from typing import List
from src.api.utils.database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer


class Stock(db.Model):
    __bind_key__ = 'IMS_db'
    __tablename__ = 'stocks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(60), nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    receipts: Mapped[List['Receipt']] = relationship(  # type: ignore
        'Receipt',
        back_populates='stock'
    )

    def __init__(self, stock_code, max_capacity=None, location=None):
        self.stock_code = stock_code
        self.max_capacity = max_capacity
        self.location = location

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

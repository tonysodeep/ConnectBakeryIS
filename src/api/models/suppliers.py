from typing import List
from src.api.utils.database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String


class Supplier (db.Model):
    __tablename__ = 'suppliers'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(60), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    goods: Mapped[List['Goods']] = relationship(  # type: ignore
        'Goods',
        back_populates='supplier',
        cascade="all, delete-orphan"
    )

    def __init__(self, name, email=None, phone_number=None, address=None):
        self.name = name
        self.email = email
        self.phone_number = phone_number
        self.address = address

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

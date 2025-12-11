from typing import List
from src.api.utils.database import db
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Date, func


class Receipt(db.Model):
    __bind_key__ = 'IMS_db'
    __tablename__ = 'receipts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    receipt_code: Mapped[str] = mapped_column(
        String(60), nullable=False, unique=True)
    request_code: Mapped[str] = mapped_column(String(60), nullable=True)
    created_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=func.now()
    )
    stock_id: Mapped[int] = mapped_column(
        ForeignKey('stocks.id'), nullable=False
    )
    stock: Mapped['Stock'] = relationship(  # type: ignore
        'Stock',
        back_populates='receipts'
    )
    list_of_raw_materials: Mapped[List['ReceiptRawMaterial']] = relationship(  # type: ignore
        back_populates='receipt',
        cascade="all, delete-orphan"
    )

    def __init__(self, receipt_code, stock_id, created_date, request_code=None):
        self.receipt_code = receipt_code
        self.stock_id = stock_id
        self.created_date = created_date
        self.request_code = request_code

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

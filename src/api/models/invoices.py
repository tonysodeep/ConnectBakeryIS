from typing import List
from datetime import date
from src.api.utils.database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, ForeignKey, func


class Invoice (db.Model):
    __tablename__ = 'invoices'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    created_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=func.now()
    )
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey('suppliers.id'), nullable=False)
    supplier: Mapped['Supplier'] = relationship(  # type: ignore
        'Supplier',
        back_populates="invoices")
    list_of_bought_goods: Mapped[List['InvoiceGoods']] = relationship(  # type: ignore
        back_populates="invoice",
        cascade="all, delete-orphan"
    )

    def __init__(self, code, created_date, supplier_id):
        self.code = code
        self.created_date = created_date
        self.supplier_id = supplier_id

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

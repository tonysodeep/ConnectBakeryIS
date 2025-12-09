from src.api.utils.database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DECIMAL
from decimal import Decimal


class InvoiceGoods(db.Model):
    __tablename__ = 'invoices_goods'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey('invoices.id'))
    goods_id: Mapped[int] = mapped_column(ForeignKey('goods.id'))
    buy_quantity: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=5, scale=3), nullable=False)
    buying_price_per_unit: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=13, scale=0), nullable=False)
    vat_precentage: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=5, scale=3), nullable=True)
    invoice: Mapped['Invoice'] = relationship(  # type: ignore
        back_populates='invoice_associations',
        overlaps="list_of_goods,list_of_invoices"
    )
    goods: Mapped['Goods'] = relationship(  # type: ignore
        back_populates='goods_associations',
        overlaps="list_of_goods,list_of_invoices"
    )

    def __init__(self, invoice_id, goods_id, buy_quantity, buying_price_per_unit, vat_precentage=None):
        self.invoice_id = invoice_id
        self.goods_id = goods_id
        self.buy_quantity = buy_quantity
        self.buying_price_per_unit = buying_price_per_unit
        self.vat_precentage = vat_precentage

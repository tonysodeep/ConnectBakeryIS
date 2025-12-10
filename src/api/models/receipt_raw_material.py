
from src.api.utils.database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DECIMAL
from decimal import Decimal


class ReceiptRawMaterial(db.Model):
    __bind_key__ = 'IMS_db'
    __tablename__ = 'receipt_raw_material'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey('receipts.id'))
    raw_material_id: Mapped[int] = mapped_column(
        ForeignKey('raw_materials.id'))
    quantity: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=3), nullable=False)

    def __init__(self, receipt_id, raw_material_id, quantity):
        self.receipt_id = receipt_id
        self.raw_material_id = raw_material_id
        self.quantity = quantity

from src.api.utils.database import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Float, ForeignKey


class Goods (db.Model):
    __tablename__ = 'goods'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    material_code: Mapped[str] = mapped_column(String(60), nullable=False)
    convert_rate: Mapped[str] = mapped_column(Float(10, 3), nullable=False)
    goods_unit: Mapped[str] = mapped_column(
        String(10), nullable=False)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey('suppliers.id'), nullable=False)
    supplier: Mapped['Supplier'] = relationship(  # type: ignore
        'Supplier',
        back_populates="goods")

    def __init__(self, name, material_code, convert_rate, goods_unit, supplier_id):
        self.name = name
        self.material_code = material_code
        self.convert_rate = convert_rate
        self.goods_unit = goods_unit
        self.supplier_id = supplier_id

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

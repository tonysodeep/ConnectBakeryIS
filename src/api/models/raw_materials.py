from src.api.utils.database import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey


class RawMaterial(db.Model):
    __bind_key__ = 'IMS_db'
    __tablename__ = 'raw_materials'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    default_unit: Mapped[str] = mapped_column(String(10), nullable=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey('categories.id'), nullable=True, ondelete="SET NULL"
    )

    def __init__(self, code, name, default_unit, category_id=None):
        self.code = code
        self.name = name
        self.default_unit = default_unit
        self.category_id = category_id

    def create(self):
        db.session.add(self)
        db.session.commit()
        return self

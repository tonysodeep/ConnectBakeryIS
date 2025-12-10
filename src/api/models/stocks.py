from src.api.utils.database import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class Stock(db.Model):
    __bind_key__ = 'IMS_db'
    __tablename__ = 'stocks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100))

    def __init__(self, code,):
        self.code = code

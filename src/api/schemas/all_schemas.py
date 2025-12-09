# Imports the models only AFTER they are all registered via models.__init__
from src.api.models import Supplier, Goods
from src.api.utils.database import db
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import EXCLUDE, fields


class GoodsSchema(SQLAlchemyAutoSchema):
    supplier = fields.Nested(
        'SupplierSchema',
        only=['name', 'phone_number']
    )

    class Meta:
        ordered = True
        model = Goods
        load_instance = True
        fields = ('id', 'name', 'material_code', 'convert_rate',
                  'goods_unit', 'supplier')
        dump_only = ('id',)
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE


class SupplierSchema(SQLAlchemyAutoSchema):
    goods = fields.Nested(
        GoodsSchema,
        many=True,
        only=['name', 'material_code']
    )

    class Meta:
        ordered = True
        model = Supplier
        load_instance = True
        fields = ('id', 'name', 'email', 'phone_number', 'address', 'goods')
        dump_only = ('id',)
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE


supplier_schema = SupplierSchema()
suppliers_schema = SupplierSchema(many=True)
goods_schema = GoodsSchema()
list_goods_schema = GoodsSchema(many=True)

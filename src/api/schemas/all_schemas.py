# Imports the models only AFTER they are all registered via models.__init__
from src.api.models import Supplier, Goods, Invoice, InvoiceGoods, Stock, RawMaterial, Category, Receipt, ReceiptRawMaterial
from src.api.utils.database import db
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import EXCLUDE, fields


class DecimalToString(fields.Decimal):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return str(value)


class GoodsSchema(SQLAlchemyAutoSchema):
    convert_rate = DecimalToString(as_string=True)
    supplier = fields.Nested(
        'SupplierSchema',
        only=['name', 'phone_number']
    )
    purchased_history = fields.List(fields.Nested(
        'InvoiceGoodsSchema',
        only=['invoice', 'buy_quantity',
              'buying_price_per_unit', 'vat_precentage']
    ))

    class Meta:
        ordered = True
        model = Goods
        load_instance = True
        fields = ('id', 'name', 'material_code', 'convert_rate',
                  'goods_unit', 'supplier_id', 'supplier', 'purchased_history')
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
    invoices = fields.List(fields.Nested(
        'InvoiceSchema',
        only=['code', 'created_date', 'list_of_bought_goods']
    ))

    class Meta:
        ordered = True
        model = Supplier
        load_instance = True
        fields = ('id', 'name', 'email', 'phone_number',
                  'address', 'goods', 'invoices')
        dump_only = ('id',)
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE


class InvoiceSchema(SQLAlchemyAutoSchema):
    supplier = fields.Nested(
        SupplierSchema,
        only=['name']
    )

    list_of_bought_goods = fields.List(fields.Nested(
        'InvoiceGoodsSchema',
        only=['goods', 'buy_quantity',
              'buying_price_per_unit', 'vat_precentage']
    ))

    class Meta:
        ordered = True
        model = Invoice
        load_instance = True
        fields = ('id', 'code', 'created_date',
                  'supplier_id', 'supplier', 'list_of_bought_goods')
        dump_only = ('id',)
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE


class InvoiceGoodsSchema(SQLAlchemyAutoSchema):
    buy_quantity = DecimalToString(as_string=True)
    buying_price_per_unit = DecimalToString(as_string=True)
    vat_precentage = DecimalToString(as_string=True)
    invoice_id = fields.Integer(required=False, load_only=True)
    invoice = fields.Nested(
        InvoiceSchema,
        only=['code', 'created_date']
    )
    goods = fields.Nested(
        GoodsSchema,
        only=['name', 'material_code']
    )

    class Meta:
        ordered = True
        model = InvoiceGoods
        load_instance = True
        fields = ('id', 'invoice_id', 'goods_id',
                  'buy_quantity', 'buying_price_per_unit', 'vat_precentage', 'invoice', 'goods')
        dump_only = ('id',)
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE


class StockSchema(SQLAlchemyAutoSchema):
    receipts = fields.List(fields.Nested(
        'ReceiptSchema',
        only=['receipt_code', 'created_date', 'list_of_raw_materials']
    ))

    class Meta:
        ordered = True
        model = Stock
        load_instance = True
        fields = ('id', 'stock_code', 'max_capacity', 'location', 'receipts')
        dump_only = ('id',)
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE


class CategorySchema(SQLAlchemyAutoSchema):
    raw_materials = fields.List(fields.Nested(
        'RawMaterialSchema',
        only=['code', 'name']
    ))

    class Meta:
        ordered = True
        model = Category
        load_instance = True
        fields = ('id', 'name', 'raw_materials')
        dump_only = ('id',)
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE


class ReceiptSchema(SQLAlchemyAutoSchema):
    stock = fields.Nested(
        'StockSchema',
        only=['stock_code']
    )
    list_of_raw_materials = fields.List(fields.Nested(
        'ReceiptRawMaterialSchema',
        only=['raw_material', 'quantity']
    ))

    class Meta:
        ordered = True
        model = Receipt
        load_instance = True
        fields = ('id', 'receipt_code', 'request_code',
                  'created_date', 'stock_id', 'stock', 'list_of_raw_materials')
        dump_only = ('id',)
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE


class ReceiptRawMaterialSchema(SQLAlchemyAutoSchema):
    receipt = fields.Nested(
        'ReceiptSchema',
        only=['receipt_code', 'created_date', 'stock']
    )
    raw_material = fields.Nested(
        'RawMaterialSchema',
        only=['code', 'name', 'category']
    )

    class Meta:
        ordered = True
        model = ReceiptRawMaterial
        load_instance = True
        fields = ('id', 'receipt_id', 'raw_material_id',
                  'quantity', 'receipt', 'raw_material')
        dump_only = ('id',)
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE


class RawMaterialSchema(SQLAlchemyAutoSchema):
    category = fields.Nested(
        'CategorySchema',
        only=['name']
    )
    movement_history = fields.List(fields.Nested(
        'ReceiptRawMaterialSchema',
        only=['receipt', 'quantity']
    ))

    class Meta:
        ordered = True
        model = RawMaterial
        load_instance = True
        fields = ('id', 'code', 'name',
                  'default_unit', 'category_id', 'category', 'movement_history')
        dump_only = ('id',)
        include_fk = True
        sqla_session = db.session
        unknown = EXCLUDE


supplier_schema = SupplierSchema()
suppliers_schema = SupplierSchema(many=True)
goods_schema = GoodsSchema()
list_goods_schema = GoodsSchema(many=True)
invoice_schema = InvoiceSchema()
invoices_schema = InvoiceSchema(many=True)
invoice_goods_schema = InvoiceGoodsSchema()
list_invoice_goods_schema = InvoiceGoodsSchema(many=True)
stock_schema = StockSchema()
stocks_schema = StockSchema(many=True)

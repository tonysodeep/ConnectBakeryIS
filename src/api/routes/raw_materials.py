from flask import Blueprint, request
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.models import Goods, InvoiceGoods, RawMaterial
from sqlalchemy import func, Float
from src.api.utils.database import db
from src.api.schemas.all_schemas import raw_material_schema, raw_materials_schema
from marshmallow import ValidationError


raw_material_routes = Blueprint("raw_material_routes", __name__)


@raw_material_routes.route('/rm-invoice-prices/', methods=['GET'])
def get_raw_materials_buying_prices():
    try:
        results = db.session.execute(
            db.select(
                Goods.material_code,
                func.avg(InvoiceGoods.buying_price_per_unit.cast(
                    Float)).label('average_price')
            )
            .join(InvoiceGoods, Goods.id == InvoiceGoods.goods_id, isouter=True)
            .group_by(Goods.material_code)
        ).all()
        response_data = []
        for code, avg_price in results:
            response_data.append({
                "material_code": code,
                "average_buying_price": str(avg_price) if avg_price is not None else None
            })
        output = response_data
        return output, 200

    except Exception as e:
        print(f"Database query error: {e}")
        return response_with(resp.SERVER_ERROR_500, message="An error occurred during price calculation.")


@raw_material_routes.route('/rm-invoices-stock/', methods=['GET'])
def get_raw_materials_invoice_stock():
    try:
        results = db.session.execute(
            db.select(
                Goods.material_code,
                func.round(
                    func.sum(
                        InvoiceGoods.buy_quantity.cast(
                            Float) * Goods.convert_rate.cast(Float())
                    ),
                    3
                ).label('invoice_stock')
            )
            .join(InvoiceGoods, Goods.id == InvoiceGoods.goods_id, isouter=True)
            .group_by(Goods.material_code)
        ).all()
        response_data = []
        for code, invoice_stock in results:
            response_data.append({
                "material_code": code,
                "invoice_stock": str(invoice_stock) if invoice_stock is not None else None
            })
        output = response_data
        return output, 200

    except Exception as e:
        print(f"Database query error: {e}")
        return response_with(resp.SERVER_ERROR_500, message="An error occurred during stock calculation.")


@raw_material_routes.route('/', methods=['POST'])
def create_raw_material():
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    is_many = isinstance(json_data, list)
    schema_to_use = raw_materials_schema if is_many else raw_material_schema
    try:
        loaded_data = schema_to_use.load(json_data)
    except ValidationError as err:
        print(err.messages)
        return response_with(resp.INVALID_INPUT_422, message="Validation error")
    except Exception as err:
        print(f"Unexpected error during schema load: {err}")
        return response_with(resp.INVALID_INPUT_422, message="Internal processing error")

    raw_materials_to_create = loaded_data if is_many else [loaded_data]
    created_raw_materials = []
    try:
        for raw_material in raw_materials_to_create:
            raw_material.create()
            created_raw_materials.append(raw_material)
    except Exception as e:
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")
    return raw_materials_schema.dump(created_raw_materials), 201


@raw_material_routes.route('/', methods=['GET'])
def get_raw_materials_list():
    fetched = db.session.execute(db.select(RawMaterial)).scalars().all()
    output = raw_materials_schema.dump(fetched)
    return output, 201

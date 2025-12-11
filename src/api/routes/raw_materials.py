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
def get_raw_materials():
    fetched = db.session.execute(db.select(RawMaterial)).scalars().all()
    output = raw_materials_schema.dump(fetched)
    return output, 201


@raw_material_routes.route('/<int:id>', methods=['GET'])
def get_raw_material_by_id(id):
    raw_material = db.session.get(RawMaterial, id)
    if raw_material is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Raw Material with id {id} not found")

    output = raw_material_schema.dump(raw_material)
    return output, 200


@raw_material_routes.route('/<int:id>', methods=['PUT'])
def update_raw_material_by_id(id):
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    existing_raw_material = db.session.get(RawMaterial, id)
    if existing_raw_material is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Raw material with id {id} not found")

    try:
        updated_raw_material_instance = raw_material_schema.load(
            json_data,
            instance=existing_raw_material,
            partial=True
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")

    output = raw_material_schema.dump(updated_raw_material_instance)
    return output, 200


@raw_material_routes.route('/', methods=['PUT'])
def update_raw_material_by_list():
    json_data = request.get_json()
    if not isinstance(json_data, list):
        return response_with(resp.INVALID_INPUT_422, message="Expected a list of raw material for bulk update.")

    if not json_data:
        return response_with(resp.INVALID_INPUT_422, message="Input list is empty.")

    updated_raw_material_list = []
    try:
        for item_data in json_data:
            raw_material_id = item_data.get('id')
            if raw_material_id is None:
                db.session.rollback()
                return response_with(resp.INVALID_INPUT_422, message=f"Missing 'id' field in one of the raw material objects.")

            existing_raw_materials = db.session.get(
                RawMaterial, raw_material_id)
            if existing_raw_materials is None:
                db.session.rollback()
                return response_with(resp.SERVER_ERROR_404,
                                     message=f"raw material with id {raw_material_id} not found, aborting bulk update.")

            updated_raw_materials = raw_material_schema.load(
                item_data,
                instance=existing_raw_materials,
                partial=True
            )
            updated_raw_material_list.append(updated_raw_materials)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during bulk update: {e}")
        return response_with(resp.INVALID_INPUT_422, message=f"Database update error: {str(e)}")

    output = raw_materials_schema.dump(updated_raw_material_list)
    return output, 200

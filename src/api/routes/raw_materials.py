import logging
from flask import Blueprint, request
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.models import Goods, InvoiceGoods, RawMaterial, ReceiptRawMaterial
from sqlalchemy import func, Float, select, Integer
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
                func.cast(
                    func.round(
                        func.avg(InvoiceGoods.buying_price_per_unit.cast(
                            Float)).label('average_price'),
                    ),
                    Integer
                )
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
    fetched_raw_materials = db.session.execute(
        db.select(RawMaterial)).scalars().all()
    try:
        results = db.session.execute(
            db.select(
                RawMaterial.code,
                func.round(func.sum(ReceiptRawMaterial.quantity.cast(
                    Float)).label('total_stock_quantity'), 3)
            )
            .join(ReceiptRawMaterial, RawMaterial.id == ReceiptRawMaterial.raw_material_id, isouter=True)
            .group_by(RawMaterial.code)
        ).all()
    except Exception as e:
        logging.error(
            f"Error fetching aggregated stock for raw materials: {e}")
        results = []

    # { "BAKINGSODA": "0.954", "BOLAT-0001": "1.0", ... }
    stock_map = {}
    for code, total_quantity in results:
        quantity_str = str(
            total_quantity) if total_quantity is not None else None
        stock_map[code] = quantity_str

    final_output = []
    for raw_material in fetched_raw_materials:
        # Dump the base data using the single item schema
        raw_material_data = raw_material_schema.dump(raw_material)
        # Get the code from the dumped data (or directly from raw_material.code)
        material_code = raw_material_data.get('code')
        # Look up the quantity using the code. Default to None if no receipts were found.
        stock_qty = stock_map.get(material_code, None)
        # --- CRITICAL FIX 2: Assign the single value found in the map ---
        raw_material_data['total_stock_quantity'] = stock_qty
        final_output.append(raw_material_data)

    return final_output, 200


@raw_material_routes.route('/<int:id>', methods=['GET'])
def get_raw_material_by_id(id):
    raw_material = db.session.get(RawMaterial, id)
    if raw_material is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Raw Material with id {id} not found")
    stock_qty = None
    try:
        result_row = db.session.execute(
            select(
                func.round(func.sum(ReceiptRawMaterial.quantity.cast(Float)), 3).label(
                    'total_stock_quantity')
            )
            .join(RawMaterial, RawMaterial.id == ReceiptRawMaterial.raw_material_id, isouter=True)
            .where(RawMaterial.id == id)
            # Grouping is technically unnecessary here but doesn't hurt
            .group_by(RawMaterial.code)
        ).scalar_one_or_none()  # Executes and gets the single calculated value
        if result_row is not None:
            # result_row is the scalar value (the rounded sum)
            stock_qty = str(result_row)
    except Exception as e:
        logging.error(
            f"Error fetching aggregated stock for raw materials: {e}")

    raw_material_data = raw_material_schema.dump(raw_material)
    raw_material_data['total_stock_quantity'] = stock_qty
    return raw_material_data, 200


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

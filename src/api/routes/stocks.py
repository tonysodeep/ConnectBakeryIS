import logging
from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.utils.database import db
from sqlalchemy import func, Float, select
from src.api.models import Stock, RawMaterial, ReceiptRawMaterial, Receipt
from src.api.schemas.all_schemas import stock_schema, stocks_schema


stocks_routes = Blueprint("stocks_routes", __name__)


@stocks_routes.route('/', methods=['POST'])
def create_stock():
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    is_many = isinstance(json_data, list)
    schema_to_use = stocks_schema if is_many else stock_schema
    try:
        loaded_data = schema_to_use.load(json_data)
    except ValidationError as err:
        print(err.messages)
        return response_with(resp.INVALID_INPUT_422, message="Validation error")
    except Exception as err:
        print(f"Unexpected error during schema load: {err}")
        return response_with(resp.INVALID_INPUT_422, message="Internal processing error")

    stocks_to_create = loaded_data if is_many else [loaded_data]
    created_stock = []
    try:
        for stock in stocks_to_create:
            stock.create()
            created_stock.append(stock)
    except Exception as e:
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")
    return stocks_schema.dump(created_stock), 201


@stocks_routes.route('/', methods=['GET'])
def get_stocks():
    fetched_stocks = db.session.execute(db.select(Stock)).scalars().all()
    try:
        results = db.session.execute(
            select(
                Stock.stock_code,
                RawMaterial.code.label('material_code'),
                func.round(
                    func.sum(ReceiptRawMaterial.quantity.cast(Float)),
                    3
                ).label('total_stock_quantity')
            )
            .join(RawMaterial, RawMaterial.id == ReceiptRawMaterial.raw_material_id, isouter=True)
            .join(Receipt, Receipt.id == ReceiptRawMaterial.receipt_id)
            .join(Stock, Stock.id == Receipt.stock_id)
            .group_by(Stock.stock_code, RawMaterial.code)
        ).all()
    except Exception as e:
        logging.error(f"Error fetching aggregated stock: {e}")

    stock_quantities_map = {}
    for stock_code, material_code, total_quantity in results:
        quantity_str = str(
            total_quantity) if total_quantity is not None else None
        if stock_code not in stock_quantities_map:
            stock_quantities_map[stock_code] = []
        stock_quantities_map[stock_code].append({
            "material_code": material_code,
            "total_stock_quantity": quantity_str
        })

    final_output = []
    for stock in fetched_stocks:
        print(f'stock {stock}')
        stock_data = stock_schema.dump(stock)
        stock_code = stock_data.get('stock_code')
        stock_data['stock_item'] = stock_quantities_map.get(stock_code, [])
        final_output.append(stock_data)

    return final_output, 200


@stocks_routes.route('/<int:id>', methods=['GET'])
def get_stock_by_id(id):
    stock = db.session.get(Stock, id)
    if stock is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Stock with id {id} not found")

    stock_items_list = []
    try:
        results = db.session.execute(
            select(
                RawMaterial.code.label('material_code'),
                func.round(
                    func.sum(ReceiptRawMaterial.quantity.cast(Float)),
                    3
                ).label('total_stock_quantity')
            )
            .join(RawMaterial, RawMaterial.id == ReceiptRawMaterial.raw_material_id, isouter=True)
            .join(Receipt, Receipt.id == ReceiptRawMaterial.receipt_id)
            .join(Stock, Stock.id == Receipt.stock_id)
            .where(Stock.id == id)
            .group_by(RawMaterial.code)
        ).all()
        for material_code, total_quantity in results:
            quantity_str = str(
                total_quantity) if total_quantity is not None else None

            stock_items_list.append({
                "material_code": material_code,
                "total_stock_quantity": quantity_str
            })
    except Exception as e:
        logging.error(f"Error fetching aggregated stock for ID {id}: {e}")

    stock_data = stock_schema.dump(stock)
    stock_data['stock_item'] = stock_items_list
    return stock_data, 200


@stocks_routes.route('/<int:id>', methods=['PUT'])
def update_stock_by_id(id):
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    existing_stock = db.session.get(Stock, id)
    if existing_stock is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Stock with id {id} not found")

    try:
        updated_stock_instance = stock_schema.load(
            json_data,
            instance=existing_stock,
            partial=True
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")

    output = stock_schema.dump(updated_stock_instance)
    return output, 200


@stocks_routes.route('/', methods=['PUT'])
def update_stock_by_list():
    json_data = request.get_json()
    if not isinstance(json_data, list):
        return response_with(resp.INVALID_INPUT_422, message="Expected a list of stocks for bulk update.")

    if not json_data:
        return response_with(resp.INVALID_INPUT_422, message="Input list is empty.")

    updated_stocks_list = []
    try:
        for item_data in json_data:
            stock_id = item_data.get('id')
            if stock_id is None:
                db.session.rollback()
                return response_with(resp.INVALID_INPUT_422, message=f"Missing 'id' field in one of the stock objects.")

            existing_stocks = db.session.get(
                Stock, stock_id)
            if existing_stocks is None:
                db.session.rollback()
                return response_with(resp.SERVER_ERROR_404,
                                     message=f"Stock with id {stock_id} not found, aborting bulk update.")

            updated_stock = stock_schema.load(
                item_data,
                instance=existing_stocks,
                partial=True
            )
            updated_stocks_list.append(updated_stock)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during bulk update: {e}")
        return response_with(resp.INVALID_INPUT_422, message=f"Database update error: {str(e)}")

    output = stocks_schema.dump(updated_stocks_list)
    return output, 200

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
    fetched = db.session.execute(db.select(Stock)).scalars().all()
    output = stocks_schema.dump(fetched)
    return output, 201


@stocks_routes.route('/<int:id>', methods=['GET'])
def get_stock_by_id(id):
    stock = db.session.get(Stock, id)
    if stock is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Stock with id {id} not found")

    output = stock_schema.dump(stock)
    return output, 200


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


@stocks_routes.route('/raw-material-stock/', methods=['GET'])
def get_raw_materials_stock():
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
            # --- JOIN 1: RawMaterial to Association Table ---
            # We start the joins from the association table or a central table
            # Since the goal is Stock Quantity PER Raw Material PER Stock
            .join(
                RawMaterial,
                RawMaterial.id == ReceiptRawMaterial.raw_material_id,  # Use raw_material_id
                isouter=True
            )
            # --- JOIN 2: Association Table to Receipt (The Receipt has the Stock FK) ---
            .join(Receipt, Receipt.id == ReceiptRawMaterial.receipt_id)

            # --- JOIN 3: Receipt to Stock (The Stock has the Receipt relationship) ---
            # Assuming Receipt model has a 'stock_id' column
            .join(Stock, Stock.id == Receipt.stock_id)

            # --- CRITICAL FIX: Group by ALL selected non-aggregate fields ---
            .group_by(
                Stock.stock_code,
                RawMaterial.code
            )
        ).all()
        grouped_stock = {}
        for stock_code, material_code, total_quantity in results:
            # Convert quantity to string or None immediately
            quantity_str = str(
                total_quantity) if total_quantity is not None else None

            # Define the item structure
            stock_item = {
                "material_code": material_code,
                "total_stock_quantity": quantity_str
            }

            # If the stock_code is not yet a key in the dictionary, initialize it
            if stock_code not in grouped_stock:
                grouped_stock[stock_code] = {
                    "stock_code": stock_code,
                    "stock_item": []  # Array to hold the list of materials
                }

            # Append the material details to the corresponding stock_code's array
            grouped_stock[stock_code]["stock_item"].append(stock_item)

        # 3. Final Response Formatting
        # Convert the dictionary values back into a list for the final JSON array
        response_data = list(grouped_stock.values())
        return response_data, 200

    except Exception as e:
        print(f"Database query error: {e}")
        return response_with(resp.SERVER_ERROR_500, message="An error occurred during stock calculation.")

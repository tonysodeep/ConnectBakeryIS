from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.utils.database import db
from src.api.models import Stock
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

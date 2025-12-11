from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
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

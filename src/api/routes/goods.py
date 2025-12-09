from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.models.goods import Goods
from src.api.schemas.all_schemas import goods_schema, list_goods_schema


goods_routes = Blueprint("goods_routes", __name__)


@goods_routes.route('/', methods=['POST'])
def create_goods():
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")
    is_many = isinstance(json_data, list)
    schema_to_use = list_goods_schema if is_many else goods_schema
    try:
        loaded_data = schema_to_use.load(json_data)
    except ValidationError as err:
        print(err.messages)
        return response_with(resp.INVALID_INPUT_422, message="Validation error")
    except Exception as err:
        print(f"Unexpected error during schema load: {err}")
        return response_with(resp.INVALID_INPUT_422, message="Internal processing error")

    goods_to_create = loaded_data if is_many else [loaded_data]
    created_goods = []
    try:
        for goods in goods_to_create:
            goods.create()
            created_goods.append(goods)

    except Exception as e:
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")
    return list_goods_schema.dump(created_goods), 201

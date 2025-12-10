from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.models import Goods
from src.api.schemas.all_schemas import goods_schema, list_goods_schema
from src.api.utils.database import db


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


@goods_routes.route('/', methods=['GET'])
def get_goods_list():
    fetched = db.session.execute(db.select(Goods)).scalars().all()
    output = list_goods_schema.dump(fetched)
    return output, 201


@goods_routes.route('/<int:id>', methods=['GET'])
def get_goods_by_id(id):
    goods = db.session.get(Goods, id)
    if goods is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Goods with id {id} not found")

    output = goods_schema.dump(goods)
    return output, 200


# goods va goods khac cai model va schema con lai update route the same
@goods_routes.route('/<int:id>', methods=['PUT'])
def update_goods_by_id(id):
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    existing_goods = db.session.get(Goods, id)
    if existing_goods is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Goods with id {id} not found")

    try:
        updated_goods_instance = goods_schema.load(
            json_data,
            instance=existing_goods,
            partial=True
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")

    output = goods_schema.dump(updated_goods_instance)
    return output, 200


@goods_routes.route('/', methods=['PUT'])
def update_goods_by_list():
    json_data = request.get_json()
    if not isinstance(json_data, list):
        return response_with(resp.INVALID_INPUT_422, message="Expected a list of goods for bulk update.")

    if not json_data:
        return response_with(resp.INVALID_INPUT_422, message="Input list is empty.")

    updated_goods_list = []
    try:
        for item_data in json_data:
            goods_id = item_data.get('id')
            if goods_id is None:
                db.session.rollback()
                return response_with(resp.INVALID_INPUT_422, message=f"Missing 'id' field in one of the goods objects.")

            existing_goods = db.session.get(Goods, goods_id)
            if existing_goods is None:
                db.session.rollback()
                return response_with(resp.SERVER_ERROR_404,
                                     message=f"goods with id {goods_id} not found, aborting bulk update.")

            updated_goods = goods_schema.load(
                item_data,
                instance=existing_goods,
                partial=True
            )
            updated_goods_list.append(updated_goods)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during bulk update: {e}")
        return response_with(resp.INVALID_INPUT_422, message=f"Database update error: {str(e)}")

    output = list_goods_schema.dump(updated_goods_list)
    return output, 200


@goods_routes.route('/<int:id>', methods=['DELETE'])
def delete_goods_by_id(id):
    existing_goods = db.session.get(Goods, id)
    if existing_goods is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Goods with id {id} not found")

    try:
        db.session.delete(existing_goods)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during delete: {e}")
        return response_with(resp.INVALID_INPUT_422, message=f"Database delete error: {str(e)}")

    return response_with(resp.SUCCESS_204, message=f'Delete succeess goods with id {id}')

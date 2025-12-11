from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.utils.database import db
from src.api.models import Receipt
from src.api.schemas.all_schemas import receipt_schema, receipts_schema


receipts_routes = Blueprint("receipts_routes", __name__)


@receipts_routes.route('/', methods=['POST'])
def create_receipts():
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    is_many = isinstance(json_data, list)
    schema_to_use = receipts_schema if is_many else receipt_schema
    try:
        loaded_data = schema_to_use.load(json_data)
    except ValidationError as err:
        print(err.messages)
        return response_with(resp.INVALID_INPUT_422, message="Validation error")
    except Exception as err:
        print(f"Unexpected error during schema load: {err}")
        return response_with(resp.INVALID_INPUT_422, message="Internal processing error")

    receipts_to_create = loaded_data if is_many else [loaded_data]
    created_receipts = []
    try:
        for receipt in receipts_to_create:
            receipt.create()
            created_receipts.append(receipt)
    except Exception as e:
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")
    return receipts_schema.dump(created_receipts), 201


@receipts_routes.route('/', methods=['GET'])
def get_receipt_list():
    fetched = db.session.execute(db.select(Receipt)).scalars().all()
    output = receipts_schema.dump(fetched)
    return output, 201

from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.utils.database import db
from src.api.models import Receipt
from src.api.schemas.all_schemas import receipt_schema, receipts_schema, receipt_raw_material_schema, list_receipt_raw_material_schema


receipts_routes = Blueprint("receipts_routes", __name__)


@receipts_routes.route('/', methods=['POST'])
def create_receipts():
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    receipt_data = json_data.get('receipt')
    list_of_raw_materials = json_data.get('list_of_raw_materials')
    if not receipt_data or not list_of_raw_materials:
        return response_with(response_with(resp.INVALID_INPUT_422, message="Missing 'receipt_data' or 'list_of_raw_materials' data"))

    try:
        loaded_receipt_data = receipt_schema.load(receipt_data)
        loaded_receipt_raw_materials_data = list_receipt_raw_material_schema.load(
            list_of_raw_materials
        )
    except ValidationError as err:
        print(err.messages)
        return response_with(resp.INVALID_INPUT_422, message=f"Validation error: {err.messages}")
    except Exception as err:
        print(f"Unexpected error during schema load: {err}")
        return response_with(resp.INVALID_INPUT_422, message="Internal processing error")

    try:
        db.session.begin_nested()
        db.session.add(loaded_receipt_data)
        db.session.flush()
        new_receipt_id = loaded_receipt_data.id
        for receipt_raw_material in loaded_receipt_raw_materials_data:
            receipt_raw_material.receipt_id = new_receipt_id
            db.session.add(receipt_raw_material)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")

    return response_with(resp.SUCCESS_201, value=receipt_raw_material_schema.dump(loaded_receipt_data))


@receipts_routes.route('/', methods=['GET'])
def get_receipt_list():
    fetched = db.session.execute(db.select(Receipt)).scalars().all()
    output = receipts_schema.dump(fetched)
    return output, 201

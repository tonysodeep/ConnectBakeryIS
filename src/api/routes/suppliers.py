from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.schemas.all_schemas import supplier_schema, suppliers_schema


supplier_routes = Blueprint("supplier_routes", __name__)


@supplier_routes.route('/', methods=['POST'])
def create_supplier():
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    is_many = isinstance(json_data, list)
    schema_to_use = suppliers_schema if is_many else supplier_schema
    try:
        loaded_data = schema_to_use.load(json_data)
    except ValidationError as err:
        print(err.messages)
        return response_with(resp.INVALID_INPUT_422, message="Validation error")
    except Exception as err:
        print(f"Unexpected error during schema load: {err}")
        return response_with(resp.INVALID_INPUT_422, message="Internal processing error")

    suppliers_to_create = loaded_data if is_many else [loaded_data]
    created_suppliers = []
    try:
        for supplier in suppliers_to_create:
            supplier.create()
            created_suppliers.append(supplier)
    except Exception as e:
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")
    return suppliers_schema.dump(created_suppliers), 201

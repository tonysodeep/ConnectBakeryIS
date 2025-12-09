from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.schemas.all_schemas import supplier_schema, suppliers_schema
from src.api.utils.database import db
from src.api.models.suppliers import Supplier


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


@supplier_routes.route('/', methods=['GET'])
def get_supplier_list():
    # SQLAlchemy 2.0 style query execution
    # db.select(Supplier) creates the SELECT statement object
    # db.session.execute runs it
    # .scalars() gets the results as model objects
    # .all() gets all results in a list
    fetched = db.session.execute(db.select(Supplier)).scalars().all()
    output = suppliers_schema.dump(fetched)
    return output, 201


@supplier_routes.route('/<int:id>', methods=['GET'])
def get_supplier_by_id(id):
    supplier = db.session.get(Supplier, id)
    if supplier is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Supplier with id {id} not found")

    output = supplier_schema.dump(supplier)
    return output, 200


@supplier_routes.route('/<int:id>', methods=['PUT'])
def update_supplier_by_id(id):
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    existing_supplier = db.session.get(Supplier, id)
    if existing_supplier is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Supplier with id {id} not found")

    try:
        updated_supplier_instance = supplier_schema.load(
            json_data,
            instance=existing_supplier,
            partial=True
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")

    output = supplier_schema.dump(updated_supplier_instance)
    return output, 201


@supplier_routes.route('/', methods=['PUT'])
def update_supplier_by_list():
    json_data = request.get_json()
    if not isinstance(json_data, list):
        return response_with(resp.INVALID_INPUT_422, message="Expected a list of suppliers for bulk update.")

    if not json_data:
        return response_with(resp.INVALID_INPUT_422, message="Input list is empty.")

    updated_suppliers_list = []
    try:
        for item_data in json_data:
            supplier_id = item_data.get('id')
            if supplier_id is None:
                db.session.rollback()
                return response_with(resp.INVALID_INPUT_422, message=f"Missing 'id' field in one of the supplier objects.")

            existing_supplier = db.session.get(Supplier, supplier_id)
            if existing_supplier is None:
                db.session.rollback()
                return response_with(resp.SERVER_ERROR_404,
                                     message=f"Supplier with id {supplier_id} not found, aborting bulk update.")

            updated_supplier = supplier_schema.load(
                item_data,
                instance=existing_supplier,
                partial=True
            )
            updated_suppliers_list.append(updated_supplier)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during bulk update: {e}")
        return response_with(resp.INVALID_INPUT_422, message=f"Database update error: {str(e)}")

    output = suppliers_schema.dump(updated_suppliers_list)
    return output, 200

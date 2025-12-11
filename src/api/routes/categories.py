from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.utils.database import db
from src.api.models import Category
from src.api.schemas.all_schemas import categories_schema, category_schema


categories_routes = Blueprint("categories_routes", __name__)


@categories_routes.route('/', methods=['POST'])
def create_categories():
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    is_many = isinstance(json_data, list)
    schema_to_use = categories_schema if is_many else category_schema
    try:
        loaded_data = schema_to_use.load(json_data)
    except ValidationError as err:
        print(err.messages)
        return response_with(resp.INVALID_INPUT_422, message="Validation error")
    except Exception as err:
        print(f"Unexpected error during schema load: {err}")
        return response_with(resp.INVALID_INPUT_422, message="Internal processing error")

    categories_to_create = loaded_data if is_many else [loaded_data]
    created_categories = []
    try:
        for category in categories_to_create:
            category.create()
            created_categories.append(category)
    except Exception as e:
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")
    return categories_schema.dump(created_categories), 201


@categories_routes.route('/', methods=['GET'])
def get_categories():
    fetched = db.session.execute(db.select(Category)).scalars().all()
    output = categories_schema.dump(fetched)
    return output, 201


@categories_routes.route('/<int:id>', methods=['GET'])
def get_category_by_id(id):
    category = db.session.get(Category, id)
    if category is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Category with id {id} not found")

    output = category_schema.dump(category)
    return output, 200


@categories_routes.route('/<int:id>', methods=['PUT'])
def update_category_by_id(id):
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    existing_category = db.session.get(Category, id)
    if existing_category is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Category with id {id} not found")

    try:
        updated_category_instance = category_schema.load(
            json_data,
            instance=existing_category,
            partial=True
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")

    output = category_schema.dump(updated_category_instance)
    return output, 200


@categories_routes.route('/', methods=['PUT'])
def update_category_by_list():
    json_data = request.get_json()
    if not isinstance(json_data, list):
        return response_with(resp.INVALID_INPUT_422, message="Expected a list of categories for bulk update.")

    if not json_data:
        return response_with(resp.INVALID_INPUT_422, message="Input list is empty.")

    updated_categories_list = []
    try:
        for item_data in json_data:
            category_id = item_data.get('id')
            if category_id is None:
                db.session.rollback()
                return response_with(resp.INVALID_INPUT_422, message=f"Missing 'id' field in one of the category objects.")

            existing_category = db.session.get(
                Category, category_id)
            if existing_category is None:
                db.session.rollback()
                return response_with(resp.SERVER_ERROR_404,
                                     message=f"Category with id {category_id} not found, aborting bulk update.")

            updated_stock = category_schema.load(
                item_data,
                instance=existing_category,
                partial=True
            )
            updated_categories_list.append(updated_stock)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during bulk update: {e}")
        return response_with(resp.INVALID_INPUT_422, message=f"Database update error: {str(e)}")

    output = categories_schema.dump(updated_categories_list)
    return output, 200

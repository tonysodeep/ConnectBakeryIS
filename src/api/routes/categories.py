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
def get_categories_list():
    fetched = db.session.execute(db.select(Category)).scalars().all()
    output = categories_schema.dump(fetched)
    return output, 201

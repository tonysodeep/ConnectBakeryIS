from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.schemas.all_schemas import invoice_schema, list_invoice_goods_schema
from src.api.utils.database import db


invoice_routes = Blueprint("invoice_routes", __name__)


@invoice_routes.route('/', methods=['POST'])
def create_invoice():
    json_data = request.get_json()
    if json_data is None:
        return response_with(resp.INVALID_INPUT_422, message="No input data provided")

    invoice_data = json_data.get('invoice')
    list_of_bought_goods = json_data.get('list_of_bought_goods')

    if not invoice_data or not list_of_bought_goods:
        return response_with(resp.INVALID_INPUT_422, message="Missing 'invoice' or 'list_of_bought_goods' data")

    try:
        loaded_invoice_data = invoice_schema.load(invoice_data)
        loaded_invoice_goods_data = list_invoice_goods_schema.load(
            list_of_bought_goods)

    except ValidationError as err:
        print(err.messages)
        return response_with(resp.INVALID_INPUT_422, message=f"Validation error: {err.messages}")
    except Exception as err:
        print(f"Unexpected error during schema load: {err}")
        return response_with(resp.INVALID_INPUT_422, message="Internal processing error")

    try:
        # Start a database transaction
        db.session.begin_nested()  # Use nested for safety, or just remove your .create() commit

        # 1. Create the Invoice and get the object with the new ID
        # Assuming you change .create() to NOT commit, or you handle commits manually.
        db.session.add(loaded_invoice_data)
        db.session.flush()  # Forces the database to generate the ID

        new_invoice_id = loaded_invoice_data.id

        # 2. Iterate, assign the new ID, and add to the session
        for invoice_goods in loaded_invoice_goods_data:
            # Assign the FK from the newly created Invoice
            invoice_goods.invoice_id = new_invoice_id
            db.session.add(invoice_goods)

        # 3. Commit the entire transaction
        db.session.commit()

    except Exception as e:
        db.session.rollback()  # Rollback if anything fails
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")

    return response_with(resp.SUCCESS_201, value=invoice_schema.dump(loaded_invoice_data))

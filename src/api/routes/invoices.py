from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.schemas.all_schemas import invoice_schema, list_invoice_goods_schema, invoices_schema, invoice_goods_schema
from src.api.utils.database import db
from src.api.models import Invoice


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
        db.session.begin_nested()
        db.session.add(loaded_invoice_data)
        db.session.flush()
        new_invoice_id = loaded_invoice_data.id
        for invoice_goods in loaded_invoice_goods_data:
            invoice_goods.invoice_id = new_invoice_id
            db.session.add(invoice_goods)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during creation: {e}")
        return response_with(resp.INVALID_INPUT_422, message="Database creation error")

    return response_with(resp.SUCCESS_201, value=invoice_schema.dump(loaded_invoice_data))


@invoice_routes.route('/', methods=['GET'])
def get_inoivces():
    fetched = db.session.execute(db.select(Invoice)).scalars().all()
    output = invoices_schema.dump(fetched)
    return output, 201


@invoice_routes.route('/<int:id>', methods=['GET'])
def get_inoivce_by_id(id):
    invoice = db.session.get(Invoice, id)
    if invoice is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Goods with id {id} not found")

    output = invoice_schema.dump(invoice)
    return output, 200


@invoice_routes.route('/<int:id>', methods=['PUT'])
def update_invoice_by_id(id):
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
        return response_with(resp.INVALID_INPUT_422, message=f"Validation error: {err.messages}")
    except Exception as err:
        print(f"Unexpected error during schema load: {err}")
        return response_with(resp.INVALID_INPUT_422, message="Internal processing error")

    existing_invoice = db.session.get(Invoice, id)
    if existing_invoice is None:
        return response_with(resp.SERVER_ERROR_404, message=f"Invoice with id {id} not found")

    try:
        db.session.begin_nested()  # Start a transaction
        existing_invoice = invoice_schema.load(
            invoice_data,
            instance=existing_invoice,
            partial=True
        )
        existing_invoice.list_of_bought_goods.clear()
        db.session.flush()
        for new_item in loaded_invoice_goods_data:
            new_item.invoice_id = id
            db.session.add(new_item)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Database error during update: {e}")
        return response_with(resp.INVALID_INPUT_422, message=f"Database update error: {e}")
    output = invoice_schema.dump(existing_invoice)
    return output, 201

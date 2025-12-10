from flask import Blueprint, request
from marshmallow import ValidationError
from src.api.utils.responses import response_with
from src.api.utils import responses as resp


stocks_routes = Blueprint("stocks_routes", __name__)


@stocks_routes.route('/', methods=['get'])
def get_stock():
    output = {'text': 'hello world'}
    return output, 201

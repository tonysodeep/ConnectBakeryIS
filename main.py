import os
import logging
from flask import Flask
from src.api.utils.database import db
from src.api.config.config import ProductionConfig, DevelopmentConfig, TestingConfig
from src.api.utils.responses import response_with
import src.api.utils.responses as resp
from src.api.routes import supplier_routes, goods_routes, invoice_routes, raw_material_routes, stocks_routes, categories_routes, receipts_routes

app = Flask(__name__)
log_file_path = 'app_activity.log'

if os.environ.get('WORK_ENV') == 'PROD':
    app_config = ProductionConfig
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
        filename=log_file_path,
        filemode='a'
    )
elif os.environ.get('WORK_ENV') == 'TEST':
    app_config = TestingConfig
    logging.basicConfig(level=logging.INFO)
else:
    app_config = DevelopmentConfig
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

app.config.from_object(app_config)
db.init_app(app)
with app.app_context():
    db.create_all()

app.register_blueprint(supplier_routes, url_prefix='/api/suppliers')
app.register_blueprint(goods_routes,
                       url_prefix='/api/goods')
app.register_blueprint(invoice_routes, url_prefix='/api/invoices')

app.register_blueprint(raw_material_routes, url_prefix='/api/raw-materials')
app.register_blueprint(stocks_routes, url_prefix='/api/stocks')
app.register_blueprint(categories_routes, url_prefix='/api/categories')
app.register_blueprint(receipts_routes, url_prefix='/api/receipts')


@app.after_request
def add_header(response):
    return response


@app.errorhandler(400)
def bad_request(e):
    logging.error(f"Bad Request: {e}")
    return response_with(resp.BAD_REQUEST_400)


@app.errorhandler(500)
def server_error(e):
    logging.exception(f"Server Error: {e}")
    return response_with(resp.SERVER_ERROR_500)


@app.errorhandler(404)
def not_found(e):
    logging.warning(f"Not Found: {e}")
    return response_with(resp.SERVER_ERROR_404)

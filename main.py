import os
from flask import Flask
from flask import jsonify
from src.api.utils.database import db
from src.api.config.config import ProductionConfig, DevelopmentConfig, TestingConfig
from src.api.utils.responses import response_with
import src.api.utils.responses as resp
from src.api.routes.suppliers import supplier_routes
from src.api.routes.goods import goods_routes
from src.api.routes.invoices import invoice_routes
from src.api.routes.raw_materials import raw_material_routes

app = Flask(__name__)

if os.environ.get('WORK_ENV') == 'PROD':
    app_config = ProductionConfig
elif os.environ.get('WORK_ENV') == 'TEST':
    app_config = TestingConfig
else:
    app_config = DevelopmentConfig

app.config.from_object(app_config)

db.init_app(app)
with app.app_context():
    db.create_all()
app.register_blueprint(supplier_routes, url_prefix='/api/suppliers')
app.register_blueprint(goods_routes,
                       url_prefix='/api/goods')
app.register_blueprint(invoice_routes, url_prefix='/api/invoices')
app.register_blueprint(raw_material_routes, url_prefix='/api/raw-materials')


@app.after_request
def add_header(response):
    return response


@app.errorhandler(400)
def bad_request(e):
    print.error(e)
    return response_with(resp.BAD_REQUEST_400)


@app.errorhandler(500)
def server_error(e):
    print.error(e)
    return response_with(resp.SERVER_ERROR_500)


@app.errorhandler(404)
def not_found(e):
    print.error(e)
    return response_with(resp.SERVER_ERROR_404)

from flask import Blueprint, request
from src.api.utils.responses import response_with
from src.api.utils import responses as resp
from src.api.models.goods import Goods
from src.api.models.invoices_goods import InvoiceGoods
from sqlalchemy import func, Float
from src.api.utils.database import db


raw_material_routes = Blueprint("raw_material_routes", __name__)


@raw_material_routes.route('/prices/', methods=['GET'])
def get_raw_materials_buying_prices():
    try:
        results = db.session.execute(
            db.select(
                Goods.material_code,
                func.avg(InvoiceGoods.buying_price_per_unit.cast(
                    Float)).label('average_price')
            )
            .join(InvoiceGoods, Goods.id == InvoiceGoods.goods_id, isouter=True)
            .group_by(Goods.material_code)
        ).all()
        response_data = []
        for code, avg_price in results:
            response_data.append({
                "material_code": code,
                "average_buying_price": str(avg_price) if avg_price is not None else None
            })
        output = response_data
        return output, 200

    except Exception as e:
        print(f"Database query error: {e}")
        return response_with(resp.SERVER_ERROR_500, message="An error occurred during price calculation.")


@raw_material_routes.route('/stock/', methods=['GET'])
def get_raw_materials_invoice_stock():
    try:
        results = db.session.execute(
            db.select(
                Goods.material_code,
                func.sum(InvoiceGoods.buy_quantity.cast(
                    Float)).label('invoice_stock')
            )
            .join(InvoiceGoods, Goods.id == InvoiceGoods.goods_id, isouter=True)
            .group_by(Goods.material_code)
        ).all()
        response_data = []
        for code, invoice_stock in results:
            response_data.append({
                "material_code": code,
                "invoice_stock": str(invoice_stock) if invoice_stock is not None else None
            })
        output = response_data
        return output, 200

    except Exception as e:
        print(f"Database query error: {e}")
        return response_with(resp.SERVER_ERROR_500, message="An error occurred during stock calculation.")

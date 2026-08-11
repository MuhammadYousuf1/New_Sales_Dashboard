from datetime import date

from app import db


class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.Date, nullable=False, index=True)
    product = db.Column(db.String(100), nullable=False, index=True)
    region = db.Column(db.String(100), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    customer = db.Column(db.String(150), nullable=False)

    @property
    def revenue(self) -> float:
        return self.quantity * self.unit_price

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_date": self.order_date.isoformat(),
            "product": self.product,
            "region": self.region,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "revenue": round(self.revenue, 2),
            "customer": self.customer,
        }

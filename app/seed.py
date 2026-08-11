import random
from datetime import date, timedelta

from app import db
from app.models import Sale

PRODUCTS = [
    ("Laptop Pro", 1299.99),
    ("Wireless Mouse", 49.99),
    ("Mechanical Keyboard", 149.99),
    ("4K Monitor", 399.99),
    ("USB-C Hub", 79.99),
    ("Webcam HD", 89.99),
    ("Noise-Cancel Headphones", 249.99),
    ("External SSD 1TB", 119.99),
]

REGIONS = [
    "North America",
    "Europe",
    "Asia Pacific",
    "Latin America",
    "Middle East",
]

CUSTOMERS = [
    "Acme Corp",
    "Globex Inc",
    "Initech",
    "Umbrella Co",
    "Stark Industries",
    "Wayne Enterprises",
    "Oscorp",
    "Cyberdyne Systems",
    "Soylent Corp",
    "Hooli",
    "Pied Piper",
    "Massive Dynamic",
]


def seed_database() -> None:
    if Sale.query.first() is not None:
        return

    today = date.today()
    start_date = today - timedelta(days=365)
    sales = []

    for _ in range(500):
        days_offset = random.randint(0, 365)
        order_date = start_date + timedelta(days=days_offset)
        product_name, base_price = random.choice(PRODUCTS)
        quantity = random.randint(1, 5)
        unit_price = round(base_price * random.uniform(0.9, 1.1), 2)

        sales.append(
            Sale(
                order_date=order_date,
                product=product_name,
                region=random.choice(REGIONS),
                quantity=quantity,
                unit_price=unit_price,
                customer=random.choice(CUSTOMERS),
            )
        )

    db.session.add_all(sales)
    db.session.commit()

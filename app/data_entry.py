import csv
import io
from datetime import date
from typing import Optional

from dateutil.parser import parse as parse_date

from app import db
from app.models import Sale
from app.seed import CUSTOMERS, PRODUCTS, REGIONS


def get_form_options() -> dict:
    products = [name for name, _ in PRODUCTS]
    return {
        "regions": REGIONS,
        "products": products,
        "customers": CUSTOMERS,
    }


def _parse_order_date(value: str) -> date:
    if not value or not value.strip():
        raise ValueError("Order date is required.")
    return parse_date(value.strip()).date()


def _parse_quantity(value: str) -> int:
    try:
        quantity = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Quantity must be a whole number.") from exc
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")
    return quantity


def _parse_unit_price(value: str) -> float:
    try:
        unit_price = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Unit price must be a number.") from exc
    if unit_price <= 0:
        raise ValueError("Unit price must be greater than 0.")
    return round(unit_price, 2)


def _clean_text(value: str, field_name: str, max_length: int) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    if len(cleaned) > max_length:
        raise ValueError(f"{field_name} must be {max_length} characters or fewer.")
    return cleaned


def build_sale_from_fields(
    order_date: str,
    product: str,
    region: str,
    quantity: str,
    unit_price: str,
    customer: str,
) -> Sale:
    return Sale(
        order_date=_parse_order_date(order_date),
        product=_clean_text(product, "Product", 100),
        region=_clean_text(region, "Region", 100),
        quantity=_parse_quantity(quantity),
        unit_price=_parse_unit_price(unit_price),
        customer=_clean_text(customer, "Customer", 150),
    )


def create_sale_from_form(form_data) -> Sale:
    return build_sale_from_fields(
        order_date=form_data.get("order_date", ""),
        product=form_data.get("product", ""),
        region=form_data.get("region", ""),
        quantity=form_data.get("quantity", ""),
        unit_price=form_data.get("unit_price", ""),
        customer=form_data.get("customer", ""),
    )


def save_sale(sale: Sale) -> None:
    db.session.add(sale)
    db.session.commit()


REQUIRED_CSV_COLUMNS = {
    "order_date",
    "product",
    "region",
    "quantity",
    "unit_price",
    "customer",
}


def import_sales_from_csv(file_stream) -> tuple[int, list[str], date | None, date | None]:
    content = file_stream.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV file is empty or missing a header row.")

    normalized_fieldnames = {name.strip().lower() for name in reader.fieldnames if name}
    missing_columns = REQUIRED_CSV_COLUMNS - normalized_fieldnames
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV is missing required columns: {missing}")

    sales: list[Sale] = []
    errors: list[str] = []

    for row_number, row in enumerate(reader, start=2):
        normalized_row = {
            (key or "").strip().lower(): (value or "").strip()
            for key, value in row.items()
        }

        if not any(normalized_row.values()):
            continue

        try:
            sales.append(
                build_sale_from_fields(
                    order_date=normalized_row["order_date"],
                    product=normalized_row["product"],
                    region=normalized_row["region"],
                    quantity=normalized_row["quantity"],
                    unit_price=normalized_row["unit_price"],
                    customer=normalized_row["customer"],
                )
            )
        except ValueError as exc:
            errors.append(f"Row {row_number}: {exc}")

    if not sales and not errors:
        raise ValueError("CSV file contains no data rows.")

    if sales:
        db.session.add_all(sales)
        db.session.commit()

    min_date = min(sale.order_date for sale in sales) if sales else None
    max_date = max(sale.order_date for sale in sales) if sales else None
    return len(sales), errors, min_date, max_date

from datetime import date, timedelta

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app.data_entry import create_sale_from_form, get_form_options, import_sales_from_csv, save_sale
from app.services import (
    default_date_range,
    get_filter_options,
    get_metrics,
    get_sales_page,
    parse_filter_date,
)

main_bp = Blueprint("main", __name__)


def _parse_filters():
    default_start, default_end = default_date_range()
    start_date = parse_filter_date(request.args.get("start_date"), default_start)
    end_date = parse_filter_date(request.args.get("end_date"), default_end)
    region = request.args.get("region", "").strip()
    product = request.args.get("product", "").strip()
    return start_date, end_date, region, product


def _dashboard_redirect(start_date: date, end_date: date, region: str = "", product: str = ""):
    return redirect(
        url_for(
            "main.dashboard",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            region=region,
            product=product,
            updated="1",
        )
    )


def _date_range_for_sale(order_date: date) -> tuple[date, date]:
    end_date = max(order_date, date.today())
    start_date = min(order_date, end_date - timedelta(days=30))
    return start_date, end_date


@main_bp.route("/")
def dashboard():
    default_start, default_end = default_date_range()
    start_date = parse_filter_date(request.args.get("start_date"), default_start)
    end_date = parse_filter_date(request.args.get("end_date"), default_end)
    options = get_filter_options()
    return render_template(
        "dashboard.html",
        default_start=start_date.isoformat(),
        default_end=end_date.isoformat(),
        default_region=request.args.get("region", "").strip(),
        default_product=request.args.get("product", "").strip(),
        data_updated=request.args.get("updated") == "1",
        regions=options["regions"],
        products=options["products"],
    )


@main_bp.route("/api/metrics")
def api_metrics():
    start_date, end_date, region, product = _parse_filters()
    return jsonify(get_metrics(start_date, end_date, region, product))


@main_bp.route("/api/sales")
def api_sales():
    start_date, end_date, region, product = _parse_filters()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 25, type=int)))
    sort_by = request.args.get("sort_by", "order_date")
    sort_dir = request.args.get("sort_dir", "desc")
    return jsonify(get_sales_page(start_date, end_date, region, product, page, per_page, sort_by, sort_dir))


@main_bp.route("/add-sale", methods=["GET", "POST"])
def add_sale():
    options = get_form_options()
    form_data = {
        "order_date": request.form.get("order_date", ""),
        "product": request.form.get("product", ""),
        "region": request.form.get("region", ""),
        "quantity": request.form.get("quantity", ""),
        "unit_price": request.form.get("unit_price", ""),
        "customer": request.form.get("customer", ""),
    }

    if request.method == "POST":
        try:
            sale = create_sale_from_form(request.form)
            save_sale(sale)
            flash(f"Added sale for {sale.customer} ({sale.product}). Live database updated.", "success")
            start_date, end_date = _date_range_for_sale(sale.order_date)
            return _dashboard_redirect(start_date, end_date, sale.region, sale.product)
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template("add_sale.html", options=options, form_data=form_data)


@main_bp.route("/import", methods=["GET", "POST"])
def import_csv():
    if request.method == "POST":
        uploaded_file = request.files.get("csv_file")
        if not uploaded_file or not uploaded_file.filename:
            flash("Please choose a CSV file to upload.", "danger")
            return redirect(url_for("main.import_csv"))

        if not uploaded_file.filename.lower().endswith(".csv"):
            flash("Only .csv files are supported.", "danger")
            return redirect(url_for("main.import_csv"))

        try:
            imported_count, row_errors, min_date, max_date = import_sales_from_csv(uploaded_file.stream)
            if imported_count:
                flash(f"Imported {imported_count} sale(s) into the live database.", "success")
            if row_errors:
                preview = "; ".join(row_errors[:3])
                extra = f" (+{len(row_errors) - 3} more)" if len(row_errors) > 3 else ""
                flash(f"Skipped {len(row_errors)} row(s): {preview}{extra}", "warning")
            if imported_count and min_date and max_date:
                return _dashboard_redirect(min_date, max_date)
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template("import.html")

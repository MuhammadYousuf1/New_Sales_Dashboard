# Sales Dashboard

A Flask sales dashboard with KPI cards, interactive charts, and a filterable sales table backed by a live SQL database or local SQLite.

## Features

- KPI cards: total revenue, order count, average order value, revenue change vs prior period
- Charts: revenue over time, revenue by region, top products
- Filterable sales table with pagination and sorting
- Add individual sales through a web form
- Bulk import sales from CSV
- Writes directly to your configured live SQL database
- Dashboard auto-refreshes after add/import with filters adjusted to show new rows

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Connect to a live SQL database

1. Copy [`.env.example`](.env.example) to `.env`
2. Set `DATABASE_URL` to your live server connection string
3. Restart the app

### MySQL example

```env
DATABASE_URL=mysql+pymysql://username:password@your-server-host:3306/sales_db
SEED_SAMPLE_DATA=false
```

### PostgreSQL example

```env
DATABASE_URL=postgresql+psycopg2://username:password@your-server-host:5432/sales_db
SEED_SAMPLE_DATA=false
```

On first run against a live database, the app creates the `sales` table automatically. Sample data is **not** inserted unless you set `SEED_SAMPLE_DATA=true`.

If `DATABASE_URL` is not set, the app falls back to local SQLite at `app/instance/sales.db`.

## Add data

- **Single sale:** [http://127.0.0.1:5000/add-sale](http://127.0.0.1:5000/add-sale)
- **CSV import:** [http://127.0.0.1:5000/import](http://127.0.0.1:5000/import)
- **Sample CSV:** [`sample_sales.csv`](sample_sales.csv)

When you add or import data, it is committed immediately to the live database and the dashboard reloads with updated charts and table rows.

CSV columns:

```text
order_date,product,region,quantity,unit_price,customer
```

## API

- `GET /api/metrics?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&region=&product=`
- `GET /api/sales?page=1&per_page=25&sort_by=order_date&sort_dir=desc`

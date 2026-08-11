-- MySQL setup for Sales Dashboard
-- Run: mysql -u root -p < mysql_setup.sql

CREATE DATABASE IF NOT EXISTS sales_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE sales_db;

DROP TABLE IF EXISTS sales;

CREATE TABLE sales (
    id INT NOT NULL AUTO_INCREMENT,
    order_date DATE NOT NULL,
    product VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    unit_price DOUBLE NOT NULL,
    customer VARCHAR(150) NOT NULL,
    PRIMARY KEY (id),
    INDEX ix_sales_order_date (order_date),
    INDEX ix_sales_product (product),
    INDEX ix_sales_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- After creating the table, import your SQLite data with:
--   python scripts/export_sqlite_to_mysql.py
-- Then run the generated mysql_data.sql file:
--   mysql -u root -p sales_db < mysql_data.sql

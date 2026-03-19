# FinLedger Backend

A production-ready Django REST API powering the FinLedger accounting suite. Covers multi-company support, double-entry bookkeeping, a full sales pipeline, purchase management, and inventory tracking.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [1. Clone & Create Virtual Environment](#1-clone--create-virtual-environment)
  - [2. Install Dependencies](#2-install-dependencies)
  - [3. Configure Settings](#3-configure-settings)
  - [4. Run Migrations](#4-run-migrations)
  - [5. Seed Demo Data](#5-seed-demo-data)
  - [6. Start the Server](#6-start-the-server)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
  - [SQLite (default)](#sqlite-default)
  - [PostgreSQL (recommended for production)](#postgresql-recommended-for-production)
- [Apps & Models](#apps--models)
  - [company](#company)
  - [accounts](#accounts)
  - [sales](#sales)
  - [purchase](#purchase)
  - [inventory](#inventory)
- [API Reference](#api-reference)
  - [Authentication](#authentication)
  - [Dashboard](#dashboard)
  - [Company](#company-1)
  - [Accounts — Groups](#accounts--groups)
  - [Accounts — Ledgers](#accounts--ledgers)
  - [Accounts — Journal Entries](#accounts--journal-entries)
  - [Sales — Customers](#sales--customers)
  - [Sales — Documents](#sales--documents)
  - [Purchase — Vendors](#purchase--vendors)
  - [Purchase — Orders](#purchase--orders)
  - [Purchase — Invoices](#purchase--invoices)
  - [Purchase — Returns](#purchase--returns)
  - [Inventory — Categories](#inventory--categories)
  - [Inventory — Products](#inventory--products)
  - [Inventory — Stock Movements](#inventory--stock-movements)
- [Request & Response Examples](#request--response-examples)
- [Common Query Parameters](#common-query-parameters)
- [Management Commands](#management-commands)
- [Admin Panel](#admin-panel)
- [CORS Configuration](#cors-configuration)
- [Deployment](#deployment)
  - [Gunicorn + Nginx](#gunicorn--nginx)
  - [Docker](#docker)
- [Troubleshooting](#troubleshooting)

---

## Overview

FinLedger Backend is a RESTful API built with Django and Django REST Framework. It supports:

- **Multi-company** architecture — one database, multiple companies, role-based user access
- **Double-entry bookkeeping** — journal entries validated for Dr = Cr balance
- **Full sales pipeline** — Quotation → Proforma → Order → Challan → Invoice with one-click stage conversion
- **Purchase management** — POs, vendor invoices, partial receipts, purchase returns
- **Inventory** — product catalog, stock adjustments, immutable movement audit trail
- **Token-based authentication** — Django REST Framework token auth

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **Framework** | Django 4.2 |
| **API** | Django REST Framework 3.14 |
| **Auth** | DRF Token Authentication |
| **CORS** | django-cors-headers |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Image handling** | Pillow (company logo upload) |
| **Server (prod)** | Gunicorn + Nginx |

---

## Project Structure

```
finledger_backend/
│
├── manage.py                          # Django management entry point
├── requirements.txt                   # Python dependencies
├── db.sqlite3                         # SQLite database (dev only)
│
├── finledger_backend/                 # Project config package
│   ├── settings.py                    # Django settings
│   ├── urls.py                        # Root URL configuration
│   ├── auth_urls.py                   # Login / logout / profile endpoints
│   ├── dashboard_urls.py              # Dashboard aggregation endpoints
│   └── wsgi.py                        # WSGI entry point
│
├── company/                           # Multi-company app
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py           # Demo data seeder ← run this first
│   ├── models.py                      # Company, CompanyUser
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── accounts/                          # Chart of accounts, ledgers, journal entries
│   ├── models.py                      # AccountGroup, Ledger, JournalEntry, JournalLine
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── sales/                             # Sales pipeline
│   ├── models.py                      # Customer, SalesDocument, SalesDocumentLine
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── purchase/                          # Purchase management
│   ├── models.py                      # Vendor, PurchaseOrder, PurchaseOrderLine,
│   │                                  # PurchaseInvoice, PurchaseReturn
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
└── inventory/                         # Inventory & stock
    ├── models.py                      # Category, Product, StockMovement
    ├── serializers.py
    ├── views.py
    ├── urls.py
    └── admin.py
```

---

## Getting Started

### 1. Clone & Create Virtual Environment

```bash
git clone <your-repo-url>
cd finledger_backend

# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` contains:

```
Django>=4.2,<5.0
djangorestframework>=3.14,<4.0
django-cors-headers>=4.3,<5.0
Pillow>=10.0
```

### 3. Configure Settings

Open `finledger_backend/settings.py` and review:

```python
# Change this before going to production
SECRET_KEY = 'django-insecure-change-this-in-production-use-env-var'

# Set to False in production
DEBUG = True

# Add your domain/IP in production
ALLOWED_HOSTS = ['*']
```

### 4. Run Migrations

```bash
# Always run from the directory that contains manage.py
cd finledger_backend   # the outer folder with manage.py

python manage.py migrate
```

Expected output:
```
Operations to perform:
  Apply all migrations: accounts, admin, auth, company, contenttypes, inventory, purchase, sales, sessions, token_auth
Running migrations:
  Applying accounts.0001_initial... OK
  ...
```

### 5. Seed Demo Data

```bash
python manage.py seed_data
```

This creates:
- Superuser: **admin / admin123**
- 1 company (ACME Industries Pvt. Ltd.)
- 10 account groups + 8 ledgers
- 5 journal entries
- 7 customers + 7 sales documents
- 4 vendors + 4 purchase orders
- 4 categories + 5 products

Safe to run multiple times — uses `get_or_create` throughout.

> **Important:** `seed_data.py` must be located at `company/management/commands/seed_data.py`. If you see `Unknown command: 'seed_data'`, the file is in the wrong location. See [Troubleshooting](#troubleshooting).

### 6. Start the Server

```bash
python manage.py runserver
```

The API is now available at **http://localhost:8000/api/**

---

## Environment Variables

For production, move sensitive values out of `settings.py` using environment variables. Install `python-decouple`:

```bash
pip install python-decouple
```

Create a `.env` file in the same directory as `manage.py`:

```env
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=finledger
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

Then update `settings.py`:

```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
```

---

## Database Setup

### SQLite (default)

No configuration needed. A `db.sqlite3` file is created automatically in the project root when you run `migrate`. Suitable for development and light testing.

### PostgreSQL (recommended for production)

**1. Create the database:**

```sql
CREATE DATABASE finledger;
CREATE USER finledger_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE finledger TO finledger_user;
```

**2. Install the PostgreSQL adapter:**

```bash
pip install psycopg2-binary
```

**3. Update `settings.py`:**

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'finledger',
        'USER': 'finledger_user',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**4. Re-run migrations:**

```bash
python manage.py migrate
python manage.py seed_data
```

---

## Apps & Models

### company

| Model | Key Fields |
|---|---|
| `Company` | name, short_name, gstin, pan, address, phone, email, fy_start, fy_end, base_currency, gst_scheme |
| `CompanyUser` | company (FK), user (FK), role (owner/admin/accountant/viewer) |

### accounts

| Model | Key Fields |
|---|---|
| `AccountGroup` | company, code, name, group_type (Primary/Sub-Group), nature (Asset/Liability/Income/Expense), parent (self FK) |
| `Ledger` | company, ledger_id, name, group (FK→AccountGroup), balance, balance_type (Dr/Cr), opening_balance |
| `JournalEntry` | company, voucher_number, voucher_type, date, reference, narration, is_posted |
| `JournalLine` | entry (FK), ledger (FK), entry_type (Dr/Cr), amount, narration |

### sales

| Model | Key Fields |
|---|---|
| `Customer` | company, name, email, phone, gstin, billing_address, shipping_address, credit_limit |
| `SalesDocument` | company, doc_type (Quotation/Proforma/Order/Challan/Invoice), doc_number, date, customer (FK), status, subtotal, total_gst, total_amount, parent_document (self FK) |
| `SalesDocumentLine` | document (FK), line_number, product_name, quantity, unit, rate, gst_rate, discount_pct |

### purchase

| Model | Key Fields |
|---|---|
| `Vendor` | company, name, email, phone, gstin, payment_terms |
| `PurchaseOrder` | company, po_number, date, vendor (FK), status, subtotal, total_gst, total_amount |
| `PurchaseOrderLine` | purchase_order (FK), product_name, quantity, received_quantity, rate, gst_rate |
| `PurchaseInvoice` | company, invoice_number, purchase_order (FK), vendor (FK), total_amount, paid_amount, status |
| `PurchaseReturn` | company, return_number, purchase_invoice (FK), vendor (FK), reason, total_amount |

### inventory

| Model | Key Fields |
|---|---|
| `Category` | company, name, description, parent (self FK) |
| `Product` | company, sku, name, category (FK), unit, cost_price, selling_price, mrp, gst_rate, hsn_code, stock_quantity, min_stock_level |
| `StockMovement` | company, product (FK), movement_type (IN/OUT/ADJUST/OPENING/RETURN_IN/RETURN_OUT), quantity, balance_after, unit_cost, reference, date |

---

## API Reference

All endpoints require the `Authorization: Token <token>` header unless stated otherwise.

Base URL: `http://localhost:8000/api`

---

### Authentication

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/auth/login/` | No | Obtain token |
| `POST` | `/auth/logout/` | Yes | Invalidate token |
| `GET` | `/auth/profile/` | Yes | Current user info |

**Login request:**
```json
POST /auth/login/
{
  "username": "admin",
  "password": "admin123"
}
```

**Login response:**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

Use this token in all subsequent requests:
```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

---

### Dashboard

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/dashboard/overview/` | Aggregated stats: revenue, expenses, receivables, net profit, recent invoices, pipeline counts, top ledgers |
| `GET` | `/dashboard/low-stock/` | Products where `stock_quantity < min_stock_level` |

**Overview response structure:**
```json
{
  "stats": {
    "total_revenue": "1245000.00",
    "total_expenses": "780000.00",
    "receivables": "234800.00",
    "net_profit": "465000.00"
  },
  "recent_invoices": [...],
  "sales_pipeline": {
    "Quotation": 2,
    "Proforma": 1,
    "Order": 1,
    "Challan": 1,
    "Invoice": 2
  },
  "top_ledgers": [...]
}
```

---

### Company

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/company/` | List all companies |
| `POST` | `/company/` | Create a company |
| `GET` | `/company/{id}/` | Retrieve company |
| `PUT` | `/company/{id}/` | Full update |
| `PATCH` | `/company/{id}/` | Partial update |
| `DELETE` | `/company/{id}/` | Delete |
| `GET` | `/company/{id}/users/` | List users in this company |

---

### Accounts — Groups

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/accounts/groups/` | List all groups |
| `POST` | `/accounts/groups/` | Create group |
| `GET` | `/accounts/groups/{id}/` | Retrieve group |
| `PUT` | `/accounts/groups/{id}/` | Update |
| `DELETE` | `/accounts/groups/{id}/` | Delete |
| `GET` | `/accounts/groups/tree/` | Full parent → children tree structure |
| `GET` | `/accounts/groups/{id}/ledgers/` | All ledgers under this group |

**Filter parameters:** `?company=1&nature=Asset&group_type=Primary`

---

### Accounts — Ledgers

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/accounts/ledgers/` | List ledgers |
| `POST` | `/accounts/ledgers/` | Create ledger |
| `GET` | `/accounts/ledgers/{id}/` | Retrieve |
| `PUT` | `/accounts/ledgers/{id}/` | Update |
| `DELETE` | `/accounts/ledgers/{id}/` | Delete |
| `GET` | `/accounts/ledgers/{id}/statement/` | Full account statement with running balance |

**Filter parameters:** `?company=1&nature=Asset&balance_type=Dr`

**Statement response:**
```json
{
  "ledger": { "id": 2, "name": "Bank - HDFC", ... },
  "opening_balance": "892500.00",
  "opening_balance_type": "Dr",
  "statement": [
    {
      "date": "2026-03-10",
      "voucher": "JV-001",
      "narration": "Sales received from XYZ Corp",
      "debit": 52000.0,
      "credit": 0,
      "balance": 944500.0,
      "balance_type": "Dr"
    }
  ],
  "closing_balance": "944500.00",
  "closing_balance_type": "Dr"
}
```

---

### Accounts — Journal Entries

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/accounts/entries/` | List entries |
| `POST` | `/accounts/entries/` | Create entry with lines (validates Dr = Cr) |
| `GET` | `/accounts/entries/{id}/` | Retrieve with all lines |
| `PUT` | `/accounts/entries/{id}/` | Update |
| `DELETE` | `/accounts/entries/{id}/` | Delete |
| `POST` | `/accounts/entries/{id}/post_entry/` | Mark as posted |
| `POST` | `/accounts/entries/{id}/unpost/` | Revert to draft |

**Filter parameters:** `?company=1&voucher_type=Payment&is_posted=true&date_from=2026-03-01&date_to=2026-03-31`

**Create entry request:**
```json
{
  "company": 1,
  "voucher_number": "JV-006",
  "voucher_type": "Receipt",
  "date": "2026-03-15",
  "reference": "INV-0042",
  "narration": "Payment received from Apex Technologies",
  "lines": [
    { "ledger": 2, "entry_type": "Dr", "amount": "75000.00" },
    { "ledger": 4, "entry_type": "Cr", "amount": "75000.00" }
  ]
}
```

> If debit total ≠ credit total, the API returns `400 Bad Request` with an error message.

---

### Sales — Customers

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/sales/customers/` | List customers |
| `POST` | `/sales/customers/` | Create customer |
| `GET` | `/sales/customers/{id}/` | Retrieve |
| `PUT` | `/sales/customers/{id}/` | Update |
| `DELETE` | `/sales/customers/{id}/` | Delete |
| `GET` | `/sales/customers/{id}/documents/` | All sales documents for this customer |
| `GET` | `/sales/customers/{id}/outstanding/` | Unpaid invoices + total outstanding amount |

---

### Sales — Documents

Handles all 5 document types via a single endpoint, filtered by `doc_type`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/sales/documents/` | List documents |
| `POST` | `/sales/documents/` | Create with line items |
| `GET` | `/sales/documents/{id}/` | Retrieve with lines |
| `PUT` | `/sales/documents/{id}/` | Update (replaces all lines) |
| `PATCH` | `/sales/documents/{id}/` | Partial update |
| `DELETE` | `/sales/documents/{id}/` | Delete |
| `POST` | `/sales/documents/{id}/convert/` | Convert to next pipeline stage |
| `POST` | `/sales/documents/{id}/change_status/` | Update status |
| `GET` | `/sales/documents/pipeline_summary/` | Count + total amount per stage |

**Filter parameters:** `?company=1&doc_type=Invoice&status=Paid&date_from=2026-03-01&date_to=2026-03-31`

**doc_type values:** `Quotation` `Proforma` `Order` `Challan` `Invoice`

**status values:** `Draft` `Pending` `Approved` `Confirmed` `Dispatched` `Paid` `Overdue` `Converted` `Cancelled`

**Pipeline conversion** (`POST /sales/documents/{id}/convert/`):

Automatically determines the next stage, creates a new document with all line items copied, and marks the original as `Converted`.

| From | To |
|---|---|
| Quotation | Proforma |
| Proforma | Order |
| Order | Challan |
| Challan | Invoice |

**Create document request:**
```json
{
  "company": 1,
  "doc_type": "Invoice",
  "doc_number": "INV-2026-0100",
  "date": "2026-03-15",
  "due_date": "2026-04-14",
  "customer": 1,
  "status": "Pending",
  "gst_type": "CGST+SGST",
  "lines": [
    {
      "product_name": "Industrial Pump A200",
      "product_sku": "SKU-001",
      "quantity": "2.000",
      "unit": "pcs",
      "rate": "18000.00",
      "gst_rate": "18.00",
      "discount_pct": "0.00"
    }
  ]
}
```

---

### Purchase — Vendors

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/purchase/vendors/` | List vendors |
| `POST` | `/purchase/vendors/` | Create vendor |
| `GET` | `/purchase/vendors/{id}/` | Retrieve |
| `PUT` | `/purchase/vendors/{id}/` | Update |
| `DELETE` | `/purchase/vendors/{id}/` | Delete |

---

### Purchase — Orders

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/purchase/orders/` | List purchase orders |
| `POST` | `/purchase/orders/` | Create PO with lines |
| `GET` | `/purchase/orders/{id}/` | Retrieve with lines |
| `PUT` | `/purchase/orders/{id}/` | Update |
| `DELETE` | `/purchase/orders/{id}/` | Delete |
| `POST` | `/purchase/orders/{id}/receive/` | Mark items as received |
| `POST` | `/purchase/orders/{id}/change_status/` | Update status |
| `POST` | `/purchase/orders/{id}/create_invoice/` | Auto-generate purchase invoice from this PO |

**Receive items request:**
```json
{
  "receipts": [
    { "line_id": 1, "received_quantity": 5 },
    { "line_id": 2, "received_quantity": 10 }
  ]
}
```

The PO status automatically updates to `Partial` or `Received` based on whether all quantities are fulfilled.

---

### Purchase — Invoices

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/purchase/invoices/` | List purchase invoices |
| `POST` | `/purchase/invoices/` | Create invoice |
| `GET` | `/purchase/invoices/{id}/` | Retrieve |
| `PUT` | `/purchase/invoices/{id}/` | Update |
| `DELETE` | `/purchase/invoices/{id}/` | Delete |
| `POST` | `/purchase/invoices/{id}/pay/` | Record payment |

**Pay request:**
```json
{ "amount": 28500 }
```

The `paid_amount` increments and status updates to `Partial` or `Paid` automatically.

---

### Purchase — Returns

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/purchase/returns/` | List returns |
| `POST` | `/purchase/returns/` | Create return |
| `GET` | `/purchase/returns/{id}/` | Retrieve |
| `DELETE` | `/purchase/returns/{id}/` | Delete |

---

### Inventory — Categories

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/inventory/categories/` | List categories |
| `POST` | `/inventory/categories/` | Create category |
| `GET` | `/inventory/categories/{id}/` | Retrieve |
| `PUT` | `/inventory/categories/{id}/` | Update |
| `DELETE` | `/inventory/categories/{id}/` | Delete |

---

### Inventory — Products

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/inventory/products/` | List all products |
| `POST` | `/inventory/products/` | Create product |
| `GET` | `/inventory/products/{id}/` | Retrieve |
| `PUT` | `/inventory/products/{id}/` | Update |
| `DELETE` | `/inventory/products/{id}/` | Delete |
| `GET` | `/inventory/products/low_stock/` | Products below minimum stock level |
| `GET` | `/inventory/products/stock_valuation/` | Total stock value + breakdown by category |
| `POST` | `/inventory/products/{id}/adjust_stock/` | Manual stock adjustment |
| `GET` | `/inventory/products/{id}/movements/` | Stock movement history for this product |

**Filter parameters:** `?company=1&category=2&low_stock=true`

**Adjust stock request:**
```json
{
  "movement_type": "IN",
  "quantity": "50.000",
  "unit_cost": "12500.00",
  "reference": "PO-2026-0019",
  "notes": "Received from ABC Suppliers",
  "date": "2026-03-15"
}
```

**movement_type values:**

| Value | Effect |
|---|---|
| `IN` | Adds quantity to current stock |
| `OUT` | Subtracts quantity (returns 400 if insufficient) |
| `ADJUST` | Sets stock to the exact quantity provided |

Every adjustment creates an immutable `StockMovement` record.

**Stock valuation response:**
```json
{
  "total_stock_value": 2461650.00,
  "total_products": 5,
  "low_stock_count": 2,
  "by_category": [
    { "category__name": "Components", "product_count": 2, "total_qty": "67.000" },
    { "category__name": "Machinery",  "product_count": 1, "total_qty": "24.000" }
  ]
}
```

---

### Inventory — Stock Movements

Read-only. Use `POST /inventory/products/{id}/adjust_stock/` to create movements.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/inventory/movements/` | List all movements |
| `GET` | `/inventory/movements/{id}/` | Retrieve single movement |

**Filter parameters:** `?company=1&product=1&movement_type=IN&date_from=2026-03-01&date_to=2026-03-31`

---

## Request & Response Examples

### Create a Journal Entry

```bash
curl -X POST http://localhost:8000/api/accounts/entries/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "company": 1,
    "voucher_number": "JV-006",
    "voucher_type": "Receipt",
    "date": "2026-03-15",
    "narration": "Payment received",
    "lines": [
      { "ledger": 2, "entry_type": "Dr", "amount": "50000.00" },
      { "ledger": 4, "entry_type": "Cr", "amount": "50000.00" }
    ]
  }'
```

### Convert a Quotation to Proforma

```bash
curl -X POST http://localhost:8000/api/sales/documents/1/convert/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Adjust Stock

```bash
curl -X POST http://localhost:8000/api/inventory/products/1/adjust_stock/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{
    "movement_type": "IN",
    "quantity": "10.000",
    "date": "2026-03-15",
    "reference": "PO-2026-0019"
  }'
```

---

## Common Query Parameters

All list endpoints support:

| Parameter | Example | Description |
|---|---|---|
| `search` | `?search=HDFC` | Text search across searchable fields |
| `page` | `?page=2` | Page number (25 results per page) |
| `ordering` | `?ordering=-date` | Sort field, prefix `-` for descending |
| `company` | `?company=1` | Filter by company ID |
| `date_from` | `?date_from=2026-03-01` | Filter records on or after this date |
| `date_to` | `?date_to=2026-03-31` | Filter records on or before this date |

---

## Management Commands

### `seed_data`

```bash
python manage.py seed_data
```

Populates the database with demo data. Safe to run multiple times. Creates:
- Superuser (admin / admin123)
- Company, account groups, ledgers
- Journal entries, customers, sales documents
- Vendors, purchase orders, categories, products

> **File location:** `company/management/commands/seed_data.py`
>
> Django only discovers management commands inside installed app packages. If the file is inside `finledger_backend/management/` (the project config folder), the command will not be found.

### Built-in Django commands

```bash
# Apply database migrations
python manage.py migrate

# Create a new superuser manually
python manage.py createsuperuser

# Open interactive Python shell with Django loaded
python manage.py shell

# Collect static files (needed for production)
python manage.py collectstatic

# Check for common project issues
python manage.py check
```

---

## Admin Panel

Django's built-in admin is available at **http://localhost:8000/admin/**

Login with the superuser credentials (admin / admin123 if seeded).

All models are registered with sensible list displays, filters, and search fields:

- **Company** — list, search by name/GSTIN
- **AccountGroup** — list with nature/type filters
- **Ledger** — list with balance type filter, inline-editable
- **JournalEntry** — list with inline `JournalLine` editing
- **Customer / Vendor** — searchable by name, GSTIN
- **SalesDocument** — list with doc_type and status filters, inline lines
- **PurchaseOrder** — list with status filter, inline lines
- **Product** — list with category/active filters
- **StockMovement** — read-friendly list with date and type filters

---

## CORS Configuration

In `settings.py`, update `CORS_ALLOWED_ORIGINS` to match your frontend URL:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",    # Standalone HTML (python -m http.server)
    "http://localhost:5173",    # Vite dev server
    "https://yourdomain.com",   # Production frontend
]

# Development only — allows all origins (remove in production)
CORS_ALLOW_ALL_ORIGINS = DEBUG
```

---

## Deployment

### Gunicorn + Nginx

**1. Install Gunicorn:**

```bash
pip install gunicorn
```

**2. Test Gunicorn:**

```bash
gunicorn finledger_backend.wsgi:application --bind 0.0.0.0:8000
```

**3. Nginx config (`/etc/nginx/sites-available/finledger`):**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /var/www/finledger/staticfiles/;
    }

    location /media/ {
        alias /var/www/finledger/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**4. Production settings checklist:**

```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECRET_KEY = os.environ['SECRET_KEY']    # Never hardcode in production
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

**5. Collect static files:**

```bash
python manage.py collectstatic
```

### Docker

**`Dockerfile`:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn psycopg2-binary

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "finledger_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

**`docker-compose.yml`:**

```yaml
version: '3.9'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: finledger
      POSTGRES_USER: finledger_user
      POSTGRES_PASSWORD: yourpassword
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=your-secret-key
      - DB_ENGINE=django.db.backends.postgresql
      - DB_NAME=finledger
      - DB_USER=finledger_user
      - DB_PASSWORD=yourpassword
      - DB_HOST=db
      - DB_PORT=5432
    depends_on:
      - db
    command: >
      sh -c "python manage.py migrate &&
             python manage.py seed_data &&
             gunicorn finledger_backend.wsgi:application --bind 0.0.0.0:8000"

volumes:
  postgres_data:
```

```bash
docker-compose up --build
```

---

## Troubleshooting

**`Unknown command: 'seed_data'`**

The `seed_data.py` file is in the wrong location. It must be inside an installed app:

```
# Wrong ❌
finledger_backend/finledger_backend/management/commands/seed_data.py

# Correct ✅
finledger_backend/company/management/commands/seed_data.py
```

Also verify both `__init__.py` files exist:
```
company/management/__init__.py
company/management/commands/__init__.py
```

---

**`No module named 'corsheaders'`**

```bash
pip install django-cors-headers
```

---

**`django.db.utils.OperationalError: no such table`**

Migrations haven't been run yet:
```bash
python manage.py migrate
```

---

**`CORS policy: No 'Access-Control-Allow-Origin'`**

Add the frontend URL to `CORS_ALLOWED_ORIGINS` in `settings.py`. For development:
```python
CORS_ALLOW_ALL_ORIGINS = True   # development only
```

---

**`401 Unauthorized` on all requests**

The token is missing or wrong. Re-authenticate:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Then include the returned token in the `Authorization` header.

---

**`manage.py` not found / wrong directory**

Always run commands from the folder that contains `manage.py`:
```bash
# Correct
cd E:\saas\v1\finledger_backend
python manage.py runserver

# Wrong — one level too deep
cd E:\saas\v1\finledger_backend\finledger_backend
python manage.py runserver   # ❌ manage.py is not here
```

---

## Related

- [Frontend README](../finledger-ui/README.md) — UI setup, configuration, and deployment
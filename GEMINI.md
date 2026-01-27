# Pricing System (Precos) - Project Overview

## Project Description
This is a corporate pricing system designed to replace Excel spreadsheets. Its primary goal is to calculate and manage product prices across various sales channels (Marketplaces) while ensuring margin protection and maintaining a strict audit trail of all price changes.

**Core Philosophy:** "No price can be overwritten without being historized."

## Technology Stack
- **Language:** Python 3.13
- **Framework:** Django 6.0.1
- **Database:**
    - Development: SQLite (`db.sqlite3`)
    - Production: PostgreSQL (`psycopg2`)
- **Frontend:** Django Templates with Bootstrap (inferred).
- **Key Libraries:** `django-decouple` (configuration), `dj-database-url`.

## Project Structure

### Core Apps
1.  **`produtos`**:
    - Manages product definitions (SKU, Dimensions, Physical Weight).
    - **Logic:** Calculates Cubic Weight and determines "Product Weight" (max of physical vs cubic) for freight calculations.
    - **Ficha Técnica (BOM):** Manages the "Kit" structure (Items, Qty, Unit Cost, Type, Multiplier) to calculate the base `Product Cost`.
    - **Pricing Logic:** Implements the core formula: `Price = (Markup_Frete * Freight) + (Cost * Markup_Sale)`.
    - **History:** Stores immutable snapshots of price calculations (`HistoricoPreco`).

2.  **`canais_vendas`**:
    - Manages Sales Channels (e.g., "ML Clássico", "Shopee 20%").
    - Defines channel-specific parameters: Tax, Operation Cost, Profit, Ads, Commission.
    - **Freight Logic:** Supports Fixed Freight or Conditional Freight Tables (Weight/Price based rules).

3.  **`grupo_vendas`**:
    - Organizes channels into "Ecosystems" (Groups).
    - Allows mass management of parameters that cascade to belonging channels.

### Key Directories
- `app/`: Project configuration (`settings.py`, `urls.py`).
- `templates/`: HTML templates for the UI.
- `static/`: CSS/JS assets.
- `manage.py`: Django command-line utility.

## Setup and Running

### Prerequisites
- Python 3.13+
- PostgreSQL (optional for dev, required for prod)

### Installation
1.  Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure Environment:
    - Set `USE_SQLITE=True` for local development to avoid PostgreSQL connection errors if not set up.
    - Or configure `DATABASE_URL` for PostgreSQL.

### Database Setup
1.  Apply migrations:
    ```bash
    export USE_SQLITE=True
    python manage.py migrate
    ```
2.  (Optional) Create a superuser:
    ```bash
    python manage.py createsuperuser
    ```

### Running the Server
```bash
export USE_SQLITE=True
python manage.py runserver
```
Access the application at `http://127.0.0.1:8000`.

## Development Conventions
- **Price History:** CRITICAL. Any change to a parameter that affects price (Cost, Tax, Freight, etc.) MUST trigger a history save before the new value is applied.
- **Freight Calculation:** Always uses the greater of Physical Weight vs Cubic Weight (`(L*A*P)/6000`).
- **Ficha Técnica:** Now supports 3 categories: Raw Material (MP), Outsourced (TR), Packaging (EM). Items have a `multiplicador` field.
- **Formulas:**
    - `Markup_Frete = 100 * (1 / (100 - (Imposto + Ads + Comissao)))`
    - `Markup_Venda = 100 * (1 / (100 - (Imposto + Operacao + Lucro + Ads + Comissao)))`

## Current Status
- Basic structure implemented.
- Product and Ficha Técnica (BOM) management active.
- Recent Fixes: Solved validation issues in "Ficha Técnica" form (handling of empty/ghost rows and data persistence on error).

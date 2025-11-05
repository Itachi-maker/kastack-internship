# Olist End-to-End Data Project

This repository contains a complete, end-to-end data engineering project built to analyze the Olist e-commerce dataset.

## The project includes:
- **ETL pipeline (Python, Pandas)** to load CSV data into Postgres.
- **Data Warehouse (Postgres)** storing raw and analytical tables.
- **REST API (FastAPI)** to serve analytics.
- **Dashboard (Grafana)** for visualization.
- **Orchestrator (Prefect)** to schedule the ETL.

## Project Structure
```
olist-data-project/
├── docker-compose.yml      # Runs Postgres & Grafana
├── grafana/
│   ├── dashboards/
│   │   └── olist_overview.json   # (Extra Credit) Dashboard export
│   └── provisioning/
│       ├── dashboards.yml      # Auto-loads dashboard
│       └── datasources.yml     # Auto-connects Grafana to Postgres
├── screenshots/
│   └── README.md             # Placeholder for your screenshots
├── src/
│   ├── etl/
│   │   ├── etl_pipeline.py     # Core ETL logic (Extract, Transform, Load)
│   │   └── run_etl.py          # Executable script for ETL
│   ├── api/
│   │   ├── crud.py             # Database query functions
│   │   ├── database.py         # DB connection logic
│   │   ├── main.py             # FastAPI app and endpoints
│   │   └── models.py           # Pydantic models for API
│   └── prefect/
│       ├── flow.py             # Prefect flow definition
│       └── deployment.yml      # Prefect deployment config
├── data/
│   └── README.md             # (Manual Step) Place Olist CSVs here
├── frontend/
│   └── index.html            # (Extra Credit) Simple HTML/JS frontend
├── .env.example              # Example environment variables
├── .gitignore
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## How to Run (Local Setup)
Follow these steps precisely to get the entire stack running on your local machine.

### Prerequisites
- **Docker & Docker Compose**: Install [Docker](https://docs.docker.com/get-docker/)
- **Python 3.9+**: Install [Python](https://www.python.org/downloads/)
- **Prefect**: `pip install prefect`
- **Git**: (For cloning)

### Step 1: Setup Project
Clone the Repository:
```bash
git clone <your-repo-url>
cd olist-data-project
```

Download Datasets (Manual Step):
Place the following Olist CSV files in `data/`:
```
data/olist_customers_dataset.csv
data/olist_order_items_dataset.csv
data/olist_order_payments_dataset.csv
data/olist_orders_dataset.csv
```

Create `.env` file:
```bash
cp .env.example .env
```

Create Virtual Environment and Install Dependencies:
```bash
python -m venv venv
venv\Scripts\activate  # (Windows)
pip install -r requirements.txt
```

### Step 2: Start Services (Postgres & Grafana)
```bash
docker compose up -d
```

- Postgres: http://localhost:5432 (User: intern, Pass: internpass, DB: kastack)
- Grafana: http://localhost:3000 (User: admin, Pass: admin)

### Step 3: Run the ETL Pipeline
```bash
python src/etl/run_etl.py
```

**Expected Output:**
```
INFO:root:Starting ETL process...
INFO:root:Data extracted successfully.
INFO:root:Data transformed successfully.
INFO:root:Loaded table 'raw_orders' (115609 rows)
INFO:root:Loaded table 'sales_summary' (96096 rows)
INFO:root:Loaded table 'delivery_performance' (27 rows)
INFO:root:ETL process completed successfully.
```

### Step 4: Run the FastAPI Server
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Open:
- API Docs → http://localhost:8000/docs  
- Health Check → http://localhost:8000/  
- Sales Summary → http://localhost:8000/sales_summary  

### Step 5: Deploy the Prefect Flow
```bash
prefect deployment apply src/prefect/deployment.yml
prefect agent start -q default
```

Prefect UI: http://127.0.0.1:4200

### Step 6: View Grafana Dashboard
http://localhost:3000 → Dashboards → **Olist Overview**

---
## Verification and SQL Queries
Includes checks for each component, Postgres validation, and Grafana SQL panels.

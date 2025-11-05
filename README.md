Olist End-to-End Data Project

This repository contains a complete, end-to-end data engineering project built to analyze the Olist e-commerce dataset.

The project includes:

An ETL pipeline (Python, Pandas) to load CSV data into Postgres.

A Data Warehouse (Postgres) storing raw and analytical tables.

A REST API (FastAPI) to serve analytics.

A Dashboard (Grafana) for visualization.

An Orchestrator (Prefect) to schedule the ETL.

Project Structure

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


How to Run (Local Setup)

Follow these steps precisely to get the entire stack running on your local machine.

Prerequisites

Docker & Docker Compose: Install Docker

Python 3.9+: Install Python

Prefect: Install Prefect (pip install prefect)

Git: (For cloning)

Step 1: Setup Project

Clone the Repository:

git clone <your-repo-url>
cd olist-data-project


Download Datasets (Manual Step):
Download the Olist CSV files and place them into the data/ directory. The ETL script expects these exact filenames:

data/olist_customers_dataset.csv

data/olist_order_items_dataset.csv

data/olist_order_payments_dataset.csv

data/olist_orders_dataset.csv

Create .env File:
Copy the example file. The default values are set for this project.

cp .env.example .env


Create Python Virtual Environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Python Dependencies:

pip install -r requirements.txt


Step 2: Start Services (Postgres & Grafana)

This command starts the database and dashboard containers in the background.

docker compose up -d


Postgres: Available at localhost:5432 (User: intern, Pass: internpass, DB: kastack)

Grafana: Available at http://localhost:3000 (User: admin, Pass: admin)

Step 3: Run the ETL Pipeline

This script will read from data/, process everything, and load the data into the Postgres container.

python src/etl/run_etl.py


Expected Output (Success):

INFO:root:Starting ETL process...
INFO:root:Data extracted successfully.
INFO:root:Data transformed successfully.
INFO:root:Loaded table 'raw_orders' (115609 rows)
INFO:root:Loaded table 'sales_summary' (96096 rows)
INFO:root:Loaded table 'delivery_performance' (27 rows)
INFO:root:ETL process completed successfully.


(Place your screenshot of this terminal output in screenshots/1_etl_success.png)

Step 4: Run the FastAPI Server

This starts the API server, which reads from the Postgres database.

uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload


API Docs: Open http://localhost:8000/docs in your browser.

Health Check: http://localhost:8000/

Data Endpoint: http://localhost:8000/sales_summary

(Place your screenshot of the API docs at http://localhost:8000/docs in screenshots/2_api_docs.png)

Step 5: Deploy the Prefect Flow

Apply the Deployment:
This command registers the flow with the Prefect API (a local server is started automatically if not running) and defines its schedule.

prefect deployment apply src/prefect/deployment.yml


Start a Prefect Agent:
In a new terminal, start an agent to pick up scheduled runs from the default work queue.

source venv/bin/activate  # Activate venv in new terminal
prefect agent start -q default


View in Prefect UI:

Run prefect server start if it's not already running.

Open the Prefect UI (usually http://127.0.0.1:4200).

Go to the "Deployments" tab. You will see the "Olist ETL Deployment" scheduled to run every hour.

(Place your screenshot of the Prefect UI showing the deployment in screenshots/3_prefect_flow.png)

Step 6: View the Grafana Dashboard

Open http://localhost:3000.

Log in with admin / admin. (You may be asked to change the password).

On the home page, go to Dashboards.

The "Olist Overview" dashboard will be pre-installed and connected to the "Olist Postgres" datasource.

(Place your screenshot of the complete Grafana dashboard in screenshots/4_grafana_dashboard.png)

Verification: How to Test Everything

After following the setup steps, use these commands to verify each component is working correctly.

1. Verify Docker Containers

Run docker ps to see the running containers.

Expected Output:

CONTAINER ID   IMAGE                    COMMAND                  CREATED       STATUS                 PORTS                    NAMES
...            grafana/grafana:latest   "/run.sh"                ...           Up 2 minutes (healthy)   0.0.0.0:3000->3000/tcp   olist_grafana
...            postgres:14              "docker-entrypoint.s..." ...           Up 2 minutes (healthy)   0.0.0.0:5432->5432/tcp   olist_postgres


(Look for (healthy) in the STATUS column).

2. Verify Postgres Data (psql)

You can directly query the Postgres container to see the tables.

Connect to the container:

docker exec -it olist_postgres psql -U intern -d kastack


List tables:

\dt


(You should see raw_orders, sales_summary, and delivery_performance)

Check row counts (approximate):

SELECT 
  (SELECT COUNT(*) FROM raw_orders) as raw_orders_count,
  (SELECT COUNT(*) FROM sales_summary) as sales_summary_count,
  (SELECT COUNT(*) FROM delivery_performance) as delivery_performance_count;


(This should match the logs from the ETL run, e.g., ~115k, ~96k, 27)

Exit psql:

\q


3. Verify FastAPI API

With the API server running (uvicorn src.api.main:app ...), test the endpoints in your browser or with curl.

Health Check (with DB connection):
curl http://localhost:8000/
Success: {"status":"ok"}
Failure (if DB is down): {"detail":"Service Unavailable: Database connection failed..."}

API Docs:
Open http://localhost:8000/docs in your browser.

Sales Summary Data:
curl http://localhost:8000/sales_summary?page_size=2
(You should see a JSON array with the first two sales summary records)

Delivery Performance Data:
curl http://localhost:8000/delivery_performance
(You should see a JSON array of all 27 regions and their stats)

4. Verify Grafana

Open http://localhost:3000.

Log in: admin / admin.

Navigate to Dashboards -> Olist Overview.

Verification: All 4 panels ("Monthly Sales Trend", "Top 10 Customers", "Revenue by Region", "Delivery Performance") should be populated with data and not show any errors.

5. Verify Prefect

Open the Prefect UI (e.g., http://127.0.0.1:4200).

Go to the Deployments tab.

Verification: You should see "olist-etl-deployment" with a schedule of "every hour". If you have an agent running, you can click "Run" to trigger a manual run and watch it succeed in the Flow Runs tab.

Grafana Panel SQL Queries

These are the SQL queries used in the auto-provisioned dashboard.

1. Monthly Sales Trend (Time Series)

SELECT
  DATE_TRUNC('month', order_purchase_timestamp)::date as "time",
  SUM(payment_value) as "total_sales"
FROM raw_orders
WHERE order_purchase_timestamp IS NOT NULL
GROUP BY 1
ORDER BY 1;


2. Top 10 Customers (Bar Chart)

SELECT
  customer_unique_id,
  total_sales
FROM sales_summary
ORDER BY total_sales DESC
LIMIT 10;


3. Revenue by Region (Pie Chart)

SELECT
  region,
  SUM(total_sales) as "total_sales"
FROM sales_summary
WHERE region IS NOT NULL
GROUP BY region
ORDER BY total_sales DESC;


4. Delivery Performance (Table)

SELECT
  region,
  delivered_count,
  pending_count,
  ROUND(avg_delivery_days::numeric, 1) as avg_delivery_days,
  ROUND(percent_late::numeric, 2) as percent_late,
  ROUND(percent_pending::numeric, 2) as percent_pending
FROM delivery_performance
ORDER BY delivered_count DESC;


Assumptions & Design Notes

Region: Assumed to be customer_state.

Total Sales: sales_summary total_sales is calculated by summing all payment_value entries for a customer.

Delivery Days: Calculated as order_delivered_customer_date - order_purchase_timestamp.

Pending Orders: Defined as orders that are not 'delivered', 'canceled', or 'unavailable' AND do not have a delivery date.

Data Duplicates: The ETL pipeline drops duplicates based on order_id and order_item_id in the raw_orders merge.

Error Handling: The ETL uses errors='coerce' for date parsing, turning un-parseable dates into NaT (Not a Time), which are handled in analytics (e.g., delivery_days will be NaN).

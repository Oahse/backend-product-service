#!/bin/bash


# Step 1: Copy the environment file
echo "Step 1: Copying the environment file..."
# cp .env.local .env

# Step 2: Run the Python script to generate the alembic.ini file
echo "Step 2: Running alembic_ini_generator to create alembic.ini..."
clickhouse-migrate init


# Step 3: Initialize Alembic (This creates the alembic directory with necessary files)
echo "Step 3: Initializing Alembic..."
alembic init -t async alembic # for asynchronous support


# Step 3.1: Run the Python script to update the alembic/env.py file
echo "Step 3.1: Running alembic_env_py_generator to update alembic/env.py..."
python3 -m alembic_env_py_generator

# Step 4: Generate a new migration (with an initial migration message)
echo "Step 4: Generating initial migration..."
clickhouse-migrate create create_tables


# Step 5: Apply the migrations (Upgrade to the latest revision)
echo "Step 5: Applying migrations (upgrading to the latest revision)..."
clickhouse-migrate apply



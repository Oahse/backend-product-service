Got it! Here's the updated version including a clear setup step before running the servers:

---

# backend-product-service

A robust backend service responsible for managing the lifecycle of products in an ecommerce platform. It handles product creation, updates, and deletion; manages product details such as pricing, inventory, categories, tags, and variants; and supports product availability and search functionality. The service ensures accurate inventory tracking and integrates with other systems like order management and pricing engines to provide seamless product data consistency across the platform.

---

## Setup and Run Local Server

### 1. Setup Local Environment and Database

* Create and activate a virtual environment:

  ```bash
  python3 -m venv venv
  source venv/bin/activate  # macOS/Linux
  # OR on Windows PowerShell:
  # .\venv\Scripts\Activate.ps1
  ```

* Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```

* Setup your local database (e.g., PostgreSQL) and configure your environment variables accordingly.

* Run database migrations if applicable (e.g., using Alembic):

  ```bash
  alembic upgrade head
  ```

### 2. Start Required Services (Redis, Celery, FastAPI)

Make sure Redis and any other dependencies are running, then start the servers:

```bash
chmod +x ./run_servers.sh
./run_servers.sh
```

### 3. Access the API

Visit these endpoints in your browser or API client:

* `http://localhost:8000/api/v1/`
* `http://localhost:8000/api/v1/search/`
* ...

---

Let me know if you'd like me to include instructions for Docker or environment variable setup too!

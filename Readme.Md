
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

**Setup and Run with Docker**

1. Clone the repository:

```
git clone https://github.com/Oahse/backend-product-service.git
cd backend-product-service
```

2. Run the Docker setup script:

Make sure Docker is installed and running, then:

```
chmod +x run_docker.sh
./run_docker.sh
```

This script will build and start the necessary containers (database, backend service, Redis, etc.).

3. Access the API endpoints:

```
http://localhost:8000/api/v1/
...
```

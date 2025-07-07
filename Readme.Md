# backend-product-service
A robust backend service responsible for managing the lifecycle of products in an ecommerce platform. It handles product creation, updating, and deletion, manages product details such as pricing, inventory, categories, tags, and variants, and supports product availability and search functionality. The service ensures accurate inventory tracking and integrates with other systems like order management and pricing engines to provide seamless product data consistency across the platform.

# Start Local Server
Use the command below to start
```bash 
uvicorn main:app --reload
```

# Setting up the Local Database
1. Create Virtual Environment and Install Python Dependencies
   create virtual environment
   ```bash
   python3 -m venv venv
   ```
   active virtual environment (Command for Macos check [here](https://docs.python.org/3/library/venv.html#how-venvs-work) for your os)
   ```bash
   source venv/bin/activate
   ```
   install dependencies
   ```bash
   pip install -r requirements.txt
   ```

2. Start the Servers(redi, celery and fastapi)
   ```bash
   chmod +x ./run_servers.sh && ./run_servers.sh

   ```

3. visit the url
   ```bash
   http://localhost:8000/api/v1/users/
   http://localhost:8000/api/v1/users/login/
   http://localhost:8000/api/v1/addresses/
   ```

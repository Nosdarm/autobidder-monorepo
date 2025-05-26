# Deployment Guide

This document provides instructions for deploying the application using Docker and Docker Compose.

## 1. Overview of Docker Setup

The Docker setup is designed to containerize the backend application and its PostgreSQL database, facilitating consistent deployment and development environments.

*   **`backend/Dockerfile`**: Defines the image for the backend FastAPI application. It:
    *   Uses a Python 3.10-slim base image.
    *   Sets up the working directory and environment variables.
    *   Installs Python dependencies from `backend/requirements.txt`.
    *   Copies the application code (FastAPI app, Alembic for migrations) into the image.
    *   Exposes the application port (default 8000).
    *   Sets a default command to run Uvicorn.
    *   **Note:** ML model artifacts (`app/ml_model/artifacts/`) are *not* copied into the image by the Dockerfile; they are managed via a volume mount defined in `docker-compose.yml`.

*   **`docker-compose.yml` (Project Root)**: Orchestrates the deployment of services:
    *   **`db` service:** Runs a PostgreSQL 13 database.
    *   **`backend` service:** Builds and runs the FastAPI application using the `backend/Dockerfile`.

*   **`.dockerignore` (in `backend/`)**: Lists files and directories to exclude from the Docker build context for the backend image, optimizing build times and image size.

## 2. Prerequisites

*   **Docker:** Install Docker Desktop (for Windows/macOS) or Docker Engine (for Linux). (Link: [https://www.docker.com/get-started](https://www.docker.com/get-started))
*   **Docker Compose:** Typically included with Docker Desktop. For Linux, it might require a separate installation. (Usually `docker compose` v2 CLI, or `docker-compose` v1).
*   **Environment Variables:**
    *   Create a `.env` file in the project root directory (where `docker-compose.yml` is located). This file is used by Docker Compose to inject environment variables into the services.
    *   A crucial variable to include in your `.env` file is `OPENAI_API_KEY`. Example:
        ```env
        # .env file content
        OPENAI_API_KEY="your_openai_api_key_here"
        
        # Optional: Override default scheduler cron times
        # ASSEMBLE_CRON_HOUR=1
        # ASSEMBLE_CRON_MINUTE=0
        # TRAIN_CRON_HOUR=2
        # TRAIN_CRON_MINUTE=0
        # STATS_UPDATE_CRON_HOUR=0
        # STATS_UPDATE_CRON_MINUTE=30

        # Optional: Override default model reload secret
        # MODEL_RELOAD_SECRET="a_stronger_secret_key"

        # Optional: Override ML probability threshold
        # ML_PROBABILITY_THRESHOLD=0.6
        ```
    *   Other environment variables defined in `docker-compose.yml` (like `DATABASE_URL`, `MODEL_PATH`) are typically configured for the containerized environment and may not need to be in the host's `.env` file unless you intend to override their defaults for specific reasons.

## 3. Building and Running the Application

1.  **Navigate to Project Root:** Open a terminal and change to the root directory of the project (where `docker-compose.yml` is located).

2.  **Build the Images:**
    ```bash
    docker-compose build
    ```
    This command builds the `backend` service image as defined in `backend/Dockerfile`. The PostgreSQL image for the `db` service will be pulled from Docker Hub if not already present.

3.  **Run the Application:**
    ```bash
    docker-compose up
    ```
    This command starts all services defined in `docker-compose.yml`.
    *   The `-d` flag can be added (`docker-compose up -d`) to run the containers in detached mode (in the background).
    *   Logs from all services can be viewed by running `docker-compose logs -f`.

## 4. Key Services in `docker-compose.yml`

*   **`db` service:**
    *   **Image:** `postgres:13-alpine`
    *   **Persistence:** Uses a named Docker volume (`postgres_data`) to persist database data across container restarts. This means your data will remain even if you stop and remove the `db` container.
    *   **Environment:** Configured with `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`. These are used by the `backend` service to connect.
    *   **Ports:** The database port `5432` inside the container is mapped to port `5433` on the host machine. This allows you to connect to the database from your host (e.g., using `psql` or a GUI tool) at `localhost:5433`.

*   **`backend` service:**
    *   **Build:** Uses the `backend/Dockerfile`.
    *   **Ports:** The application port `8000` inside the container is mapped to port `8000` on the host. The application will be accessible at `http://localhost:8000`.
    *   **Environment Variables:**
        *   `DATABASE_URL`: Set to connect to the `db` service within the Docker network.
        *   `PYTHONPATH=/app`: Ensures Python can correctly import modules, as the application code from `backend/app` is mounted to `/app/app` and `WORKDIR` is `/app`.
        *   `MODEL_PATH=/app/app/ml_model/artifacts/model.joblib`: Specifies the path *inside the container* where the application expects to find the trained ML model.
        *   Other variables like `OPENAI_API_KEY` are passed from the `.env` file on the host.
        *   Scheduler and ML endpoint configurations are also set, with defaults if not provided in the `.env` file.
    *   **Volumes:**
        *   `./backend/app:/app/app`: Mounts the local `backend/app` directory into the container at `/app/app`. This is primarily for development to allow live code changes without rebuilding the image. For production, you might remove this volume to use the code baked into the image.
        *   `./backend/alembic:/app/alembic` and `./backend/alembic.ini:/app/alembic.ini`: Mounts Alembic configuration and migration scripts.
        *   `./backend/app/ml_model/artifacts:/app/app/ml_model/artifacts`: **Crucially important.** This mounts the local `./backend/app/ml_model/artifacts` directory (on the host) to `/app/app/ml_model/artifacts` inside the container.
            *   **Purpose:**
                1.  When the scheduled `train_model.py` script runs inside the container, it saves the trained `model.joblib` and other artifacts to `/app/app/ml_model/artifacts/`. Due to the volume mount, these files will also appear on your host machine in `./backend/app/ml_model/artifacts/`.
                2.  When the FastAPI application starts (or reloads the model), it loads the model from `/app/app/ml_model/artifacts/model.joblib` inside the container. This ensures it picks up the model trained by the scheduler.
                3.  This also ensures model persistence even if the `backend` container is stopped and removed.
    *   **Database Migrations:**
        *   The `command` for the `backend` service is overridden in `docker-compose.yml`. It includes a step: `alembic -c /app/alembic.ini upgrade head`.
        *   This command runs database migrations automatically every time the `backend` service starts, ensuring the database schema is up-to-date with the models defined in the application.
        *   The command also includes a loop to wait for the database to be healthy before attempting migrations.
    *   **`depends_on`:** Ensures the `backend` service starts only after the `db` service is healthy.

## 5. Accessing the Application and Database

*   **FastAPI Application:** Once `docker-compose up` is running, the backend API should be accessible at `http://localhost:8000`. The OpenAPI documentation (Swagger UI) will be at `http://localhost:8000/docs`.
*   **PostgreSQL Database:** Accessible from your host machine at `localhost:5433`.
    *   User: `appuser`
    *   Password: `apppassword` (as set in `docker-compose.yml`)
    *   Database Name: `appdb`

## 6. Stopping the Application

*   If running in the foreground (without `-d`), press `Ctrl+C` in the terminal where `docker-compose up` is running.
*   If running in detached mode, use:
    ```bash
    docker-compose down
    ```
    This command stops and removes the containers. To also remove the named volume `postgres_data` (and thus delete all database data), use `docker-compose down -v`.

## 7. Environment Variable Configuration Summary

The `docker-compose.yml` file is configured to use environment variables from a `.env` file in the project root. Key variables include:

*   `OPENAI_API_KEY` (for OpenAI API access)
*   `DATABASE_URL` (typically set within `docker-compose.yml` for service-to-service communication)
*   `MODEL_PATH` (set within `docker-compose.yml` to point to the correct path inside the container)
*   Scheduler cron settings (e.g., `ASSEMBLE_CRON_HOUR`, `TRAIN_CRON_MINUTE`)
*   `MODEL_RELOAD_URL` and `MODEL_RELOAD_SECRET`
*   `ML_PREDICTION_ENDPOINT_URL` and `ML_PROBABILITY_THRESHOLD`

Ensure your `.env` file is populated with necessary secrets like `OPENAI_API_KEY` and any overrides for default cron times or secrets. The `.env` file should be added to `.gitignore` to prevent committing secrets.

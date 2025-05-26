# 1. Base Image
FROM python:3.10-slim

# 2. Set Environment Variables
ENV PYTHONUNBUFFERED=1
ENV APP_MODULE="app.main:app"
ENV PORT="8000"

# 3. Set Working Directory
WORKDIR /app

# 4. Install Dependencies
# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Application Code
# Copy local code to /app in the container
# The paths here are relative to the Docker build context (./backend)
COPY ./app ./app
COPY ./alembic ./alembic
COPY alembic.ini .
# Note: ML model artifacts are not copied here; they will be mounted via docker-compose.

# 6. Expose Port
EXPOSE ${PORT}

# 7. Command to Run Application
# The command in docker-compose.yml will override this if specified,
# potentially to include Alembic migrations.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

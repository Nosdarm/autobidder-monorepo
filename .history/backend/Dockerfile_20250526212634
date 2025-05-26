# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY ./requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the working directory
COPY ./app ./app
COPY ./alembic.ini ./alembic.ini # If alembic is used from within the app
COPY ./alembic ./alembic # If alembic is used from within the app

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# Assuming your FastAPI app instance is named 'app' in 'app/main.py'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

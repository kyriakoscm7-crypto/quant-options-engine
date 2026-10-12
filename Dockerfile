# Use Python 3.11
FROM python:3.11-slim

# Prevent Python from generating unnecessary cache files
ENV PYTHONDONTWRITEBYTECODE=1

# Make Python print logs immediately
ENV PYTHONUNBUFFERED=1

# Set the working directory inside Docker
WORKDIR /app

# Copy the dependency list
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy our application into Docker
COPY app/ ./app/

# Document the API port
EXPOSE 8000

# Start our FastAPI application
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
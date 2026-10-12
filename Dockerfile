FROM python:3.11-slim

# Prevent Python from writing .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Display Python logs immediately.
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container.
WORKDIR /app

# Copy dependency definitions.
COPY requirements.txt .

# Install Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code.
COPY app/ ./app/

# Document the default application port.
EXPOSE 8080

# Start FastAPI using the PORT environment variable.
CMD ["sh", "-c", "exec uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
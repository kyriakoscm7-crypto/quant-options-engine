FROM python:3.11-slim@sha256:db20d8506e2f15b6db39b40b6015ca46bae855dec6dd326d462cfe79ae972893

# Prevent Python from writing .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Display Python logs immediately.
ENV PYTHONUNBUFFERED=1
ENV QI_API_MODE=production
ARG BUILD_SHA=unknown
ENV QI_BUILD_SHA=$BUILD_SHA
LABEL org.opencontainers.image.revision=$BUILD_SHA

# Set the working directory inside the container.
WORKDIR /app

# Copy dependency definitions.
COPY requirements.txt requirements.lock ./

# Install Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code.
COPY app/ ./app/

# Calculators do not need root or a writable application directory.
USER 10001:10001

# Document the default application port.
EXPOSE 8080

# Start FastAPI using the PORT environment variable.
CMD ["sh", "-c", "exec uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8080} --limit-concurrency 8 --timeout-keep-alive 5"]
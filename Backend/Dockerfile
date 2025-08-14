FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for potential package builds
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y gcc \
    && apt-get autoremove -y

COPY . .

# Expose the port your FastAPI app runs on
EXPOSE 8000

# Set environment variables for production
ENV HOST=0.0.0.0
ENV PORT=8000

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Define the command to run your application
CMD ["python", "run.py"]
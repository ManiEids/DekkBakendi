FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Copy spider files to the correct location
RUN python copy_spiders.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run when container starts
CMD ["python", "Leita/run_all.py"]

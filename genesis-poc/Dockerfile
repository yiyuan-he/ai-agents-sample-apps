FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
COPY aws_opentelemetry_distro-0.9.0.dev0-py3-none-any.whl .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["opentelemetry-instrument", "python", "run_customer_support_console.py"]

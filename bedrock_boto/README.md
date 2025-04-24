# Setup

## Prerequisites

Before you begin, ensure that Transaction Search is enabled on your AWS Account.

https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-Lambda-TransactionSearch.html

## Environment Setup

1. Create a Python virtual environment:
```
$ python -m venv venv
```

2. Activate the virtual environment:
```
$ source venv/bin/activate
```

3. Install dependencies:
```
$ pip install -r requirements.txt
```

**Note**: The AWS Distro for OpenTelemetry (ADOT) Python SDK is already included in the `requirements.txt` file.

## Running the Application

Launch the application with the ADOT Python SDK using the following command:
```
$ env OTEL_METRICS_EXPORTER=none \
          OTEL_LOGS_EXPORTER=none \
          OTEL_PYTHON_DISTRO=aws_distro \
          OTEL_TRACES_EXPORTER=console \
          OTEL_PYTHON_CONFIGURATOR=aws_configurator \
          OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
          OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://xray.us-east-1.amazonaws.com/v1/traces \
          OTEL_RESOURCE_ATTRIBUTES="service.name=langchain-app" \
          OTEL_PYTHON_DISABLED_INSTRUMENTATIONS="http,sqlalchemy,psycopg2,pymysql,sqlite3,aiopg,asyncpg,mysql_connector,urllib3,requests" \
          PYTHONPATH="./../autoinstrumentation/opentelemetry/instrumentation/auto_instrumentation:$PYTHONPATH:./../autoinstrumentation" \
          python call_bedrock.py
```
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
          OTEL_PYTHON_CONFIGURATOR=aws_configurator \
          OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
          OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://xray.us-east-1.amazonaws.com/v1/traces \
          OTEL_RESOURCE_ATTRIBUTES="service.name=langchain-app" \
          OTEL_PYTHON_DISABLED_INSTRUMENTATIONS="http,sqlalchemy,psycopg2,pymysql,sqlite3,aiopg,asyncpg,mysql_connector,botocore,boto3,urllib3,requests" \
          opentelemetry-instrument python run_customer_support_console.py
```
**Note:** This sends the spans directly to the X-Ray OTLP endpoint so you don't need to set up the OpenTelemetry Collector or CloudWatch Agent.

## Viewing Spans in CloudWatch

After the application is finished running, you can view the generated spans in CloudWatch by following these steps:

1. Open the AWS CloudWatch console
2. Navigate to the "Log groups" section in the left sidebar.
3. Select the `aws/spans` log group to view your trace data.

You can use CloudWatch Logs Insights to query and analyze these spans for monitoring and troubleshooting purposes.

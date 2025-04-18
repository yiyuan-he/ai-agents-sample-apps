# Setup

## Prerequisites

Before you begin, ensure that Transaction Search is enabled on your AWS Account.

https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-Lambda-TransactionSearch.html

## Environment Setup

Set up a `.env` file with the following contents:
```
OPENAI_API_KEY="<your_api_key>"
```

Create a python virtual env with all the necessary dependencies:
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

Run the application with the ADOT Python SDK:
```
❯ env OTEL_METRICS_EXPORTER=none \
          OTEL_LOGS_EXPORTER=none \
          OTEL_PYTHON_DISTRO=aws_distro \
          OTEL_PYTHON_CONFIGURATOR=aws_configurator \
          OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
          OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://xray.us-east-1.amazonaws.com/v1/traces \
          OTEL_RESOURCE_ATTRIBUTES="service.name=langchain-app" \
          OTEL_PYTHON_DISABLED_INSTRUMENTATIONS="http,sqlalchemy,psycopg2,pymysql,sqlite3,aiopg,asyncpg,mysql_connector,botocore,boto3,urllib3,requests" \
          opentelemetry-instrument python app.py
```
**Note**: This sends the spans directly to the X-Ray OTLP endpoint so you don't need to set up an OpenTelemetry Collector.

## Viewing Spans in CloudWatch

After the application is finished running, you can view the generated spans in CloudWatch by following these steps:
    1. Open the AWS CloudWatch console
    2. Navigate to the "Logs groups" section in the left sidebar.
    3. Select the `aws/spans` log group to view your trace data.

![Screenshot 2025-04-18 at 4 36 13 PM](https://github.com/user-attachments/assets/d82e149e-9956-467d-8317-d83d2db1a160)

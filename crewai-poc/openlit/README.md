# Setup

## Prerequisites

Before you begin, ensure that Transaction Search is enabled on your AWS Account.

https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-Lambda-TransactionSearch.html

## Environment Setup

Create a python virtual env with all the necessary dependencies:
```
uv venv
source ./venv/bin/activate
uv pip install -r requirements.txt
```

## Running the Application

Run the application with the ADOT Python SDK:
```
env OTEL_PYTHON_DISTRO=aws_distro \
        OTEL_PYTHON_CONFIGURATOR=aws_configurator \
        OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
        OTEL_EXPORTER_OTLP_LOGS_HEADERS="x-aws-log-group=test/genesis,x-aws-log-stream=default,x-aws-metric-namespace=genesis" \
        OTEL_RESOURCE_ATTRIBUTES="service.name=crewai-openlit-app" \
        AGENT_OBSERVABILITY_ENABLED="true" \
        opentelemetry-instrument python server.py
```
**Note**: This sends the spans directly to the X-Ray OTLP endpoint so you don't need to set up an OpenTelemetry Collector.

## Viewing Spans in CloudWatch

After the application is finished running, you can view the generated spans in CloudWatch by following these steps:
    1. Open the AWS CloudWatch console
    2. Navigate to the "Logs groups" section in the left sidebar.
    3. Select the `aws/spans` log group to view your trace data.
    
![Screenshot 2025-04-18 at 4 36 13 PM](https://github.com/user-attachments/assets/2cd9b4a9-e6c4-4476-8f1f-7be51ac295d6)

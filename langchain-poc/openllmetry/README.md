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
export PYTHONPATH="./otel-init:$PYTHONPATH" # bash/zsh
set -x PYTHONPATH "./otel-init:$PYTHONPATH" # fish
python app.py
```
**Note**: This sends the spans directly to the X-Ray OTLP endpoint so you don't need to set up an OpenTelemetry Collector.

## Viewing Spans in CloudWatch

After the application is finished running, you can view the generated spans in CloudWatch by following these steps:
    1. Open the AWS CloudWatch console
    2. Navigate to the "Logs groups" section in the left sidebar.
    3. Select the `aws/spans` log group to view your trace data.

![Screenshot 2025-04-18 at 4 36 13 PM](https://github.com/user-attachments/assets/d82e149e-9956-467d-8317-d83d2db1a160)

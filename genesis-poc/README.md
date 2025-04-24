# Setup

## Prerequisites

Before you begin, ensure that Transaction Search is enabled on your AWS Account.

https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-Lambda-TransactionSearch.html

## Environment Setup

Set up a working directory:

```
$ mkdir $HOME/projects

$ set -x WORKDIR "$HOME/projects" # fish shell
$ export WORKDIR="$HOME/projects" # bash/zsh shell

$ cd $WORKDIR
```

Clone this parent repo:

```
$ git clone https://github.com/yiyuan-he/ai-agents-sample-apps.git
```

Clone the ADOT Python SDK repo:

```
$ git clone https://github.com/aws-observability/aws-otel-python-instrumentation.git 

$ cd aws-otel-python-instrumentation
```

Build and install the ADOT Python SDK into a directory called `autoinstrumentation`:

```
$ mkdir autoinstrumentation

$ pip install setuptools==75.2.0 urllib3==2.2.3 --target autoinstrumentation ./aws-opentelemetry-distro
```

Move this `autoinstrumentation` directory to this sample app's directory:

```
$ mv autoinstrumentation $WORKDIR/ai-agents-sample-apps/genesis-poc/autoinstrumentation
```

`cd` to this sample app:

```
$ cd $WORKDIR/ai-agents-sample-apps/genesis-poc
```

Set up a python virtual environment and install the sample app's dependencies:

```
$ python -m venv venv

$ source venv/bin/activate.fish # fish shell
$ source venv/bin/activate # bash/zsh shell

$ pip install -r requirements.txt
```

Set the `PYTHONPATH` to inject the ADOT SDK's components into the application at runtime:

```
$ set -x PYTHONPATH "$WORKDIR/ai-agents-sample-apps/genesis-poc/autoinstrumentation/opentelemetry/instrumentation/auto_instrumentation:$PYTHONPATH:$WORKDIR/ai-agents-sample-apps/genesis-poc/autoinstrumentation" # fish shell

$ export PYTHONPATH=$WORKDIR/ai-agents-sample-apps/genesis-poc/autoinstrumentation/opentelemetry/instrumentation/auto_instrumentation:$PYTHONPATH:$WORKDIR/ai-agents-sample-apps/genesis-poc/autoinstrumentation" # bash/zsh shell
```

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
    OTEL_PYTHON_DISABLED_INSTRUMENTATIONS="http,sqlalchemy,psycopg2,pymysql,sqlite3,aiopg,asyncpg,mysql_connector,botocore,boto3,urllib3,requests,starlette" \
    python run_customer_support_console.py
```
**Note:** This sends the spans directly to the X-Ray OTLP endpoint so you don't need to set up the OpenTelemetry Collector or CloudWatch Agent.

## Viewing Spans in CloudWatch

After the application is finished running, you can view the generated spans in CloudWatch by following these steps:

1. Open the AWS CloudWatch console

2. Navigate to the "Log groups" section in the left sidebar.
3. Select the `aws/spans` log group to view your trace data.

<img width="2543" alt="Screenshot 2025-04-17 at 11 47 15 AM" src="https://github.com/user-attachments/assets/b5560a47-4f2f-44a5-8ac7-e91c61ccd3e7" />

You can use CloudWatch Logs Insights to query and analyze these spans for monitoring and troubleshooting purposes.

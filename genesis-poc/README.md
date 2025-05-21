# Setup

## Prerequisites

Before you begin, ensure that Transaction Search is enabled on your AWS Account.

https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-Lambda-TransactionSearch.html

Include the following permissions in Genesis application IAM role/user or directly attach CloudWatchAgentServerPolicy policy.
```
"Statement" : [
    {
      "Sid" : "CWACloudWatchServerPermissions",
      "Effect" : "Allow",
      "Action" : [
        "cloudwatch:PutMetricData",
        "ec2:DescribeVolumes",
        "ec2:DescribeTags",
        "logs:PutLogEvents",
        "logs:PutRetentionPolicy",
        "logs:DescribeLogStreams",
        "logs:DescribeLogGroups",
        "logs:CreateLogStream",
        "logs:CreateLogGroup",
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords",
        "xray:GetSamplingRules",
        "xray:GetSamplingTargets",
        "xray:GetSamplingStatisticSummaries"
      ],
      "Resource" : "*"
    }
```
Set your AWS credentials with IAM role/user:
```
export AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID>
export AWS_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY>
export AWS_REGION=<AWS_REGION>
```

## Genesis ADOT SDK Enablement
**Note:** These steps have already been done for you in this directory. You can skip to the "Build and Run the Application" section.

1. Add ADOT SDK as a dependency for observability. Such as the example below, 
```
# requirements.txt
...
rest of dependencies
...
aws-opentelemetry-distro
```
ADOT SDK has been added in requirement.txt [here](https://github.com/yiyuan-he/ai-agents-sample-apps/blob/main/genesis-poc/requirements.txt#L41). 

2. Update your `Dockerfile` with the `opentelemetry-instrument` prefix command:
```
FROM python:3.12-slim

WORKDIR /app

# ...rest of Dockerfile

CMD ["opentelemetry-instrument",  "python", "chat_api_server.py"] # change this line
```

## Build and Run the Application

Build docker image:
```
docker build -t genesis-poc .
```

Run application in docker image:
```
docker run -p 8000:8000 \
       -e "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" \
       -e "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" \
       -e "AWS_REGION=$AWS_REGION" \
       -e "OTEL_METRICS_EXPORTER=awsemf" \
       -e "OTEL_TRACES_EXPORTER=otlp" \
       -e "OTEL_LOGS_EXPORTER=otlp" \
       -e "OTEL_PYTHON_DISTRO=aws_distro" \
       -e "OTEL_PYTHON_CONFIGURATOR=aws_configurator" \
       -e "OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf" \
       -e "OTEL_RESOURCE_ATTRIBUTES=service.name=ticketing-agent" \
       -e "OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true" \
       -e "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true" \
       -e "OTEL_AWS_APPLICATION_SIGNALS_ENABLED=false" \
       -e "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://xray.us-east-1.amazonaws.com/v1/traces" \
       -e "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=https://logs.us-east-1.amazonaws.com/v1/logs" \
       -e "OTEL_EXPORTER_OTLP_LOGS_HEADERS=x-aws-log-group=test/genesis,x-aws-log-stream=default,x-aws-metric-namespace=genesis" \
       -e "OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=http,sqlalchemy,psycopg2,pymysql,sqlite3,aiopg,asyncpg,mysql_connector,botocore,boto3,urllib3,requests,starlette" \
       -e "AGENT_OBSERVABILITY_ENABLED=true" \
       genesis-poc
```

From another terminal run:
```
λ  curl -X POST http://localhost:8000/chat \
           -H "Content-Type: application/json" \
           -d '{"message": "Hi there, what time is my flight?"}'
```

**Important:** Make sure the `log-group` and `log-stream` specified already exists in your account since we do utilize `CreateLogGroup` or `CreateLogStream` permissions yet.

## Viewing Spans in CloudWatch

After the application is finished running, you can view the generated spans in CloudWatch by following these steps:

1. Open the AWS CloudWatch console

2. Navigate to the "Log groups" section in the left sidebar.
3. Select the `aws/spans` log group to view your trace data.
4. Select the configured log group to view your logs and metrics data i.e. `test/genesis`.

<img width="2543" alt="Screenshot 2025-04-17 at 11 47 15 AM" src="https://github.com/user-attachments/assets/b5560a47-4f2f-44a5-8ac7-e91c61ccd3e7" />

You can use CloudWatch Logs Insights to query and analyze these spans for monitoring and troubleshooting purposes.

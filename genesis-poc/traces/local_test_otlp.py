import requests
import json
import uuid
import boto3
from datetime import datetime
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.exceptions import ClientError

def sign_request(url, body, headers, credentials, region):
    """Helper function to sign the request with AWS SigV4"""
    request = AWSRequest(
        method='POST',
        url=url,
        data=json.dumps(body),
        headers=headers
    )
    SigV4Auth(credentials, 'logs', region).add_auth(request)
    return dict(request.headers)

def ensure_log_stream_exists(client, log_group_name, log_stream_name):
    try:
        client.create_log_stream(
            logGroupName=log_group_name,
            logStreamName=log_stream_name
        )
        print(f"Created log stream: {log_stream_name}")
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
            print(f"Error creating log stream: {str(e)}")
            raise

def ensure_log_group_exists(client, log_group_name):
    try:
        client.create_log_group(logGroupName=log_group_name)
        print(f"Created log group: {log_group_name}")
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
            print(f"Error creating log group: {str(e)}")
            raise

def send_logs_via_otlp(region='us-west-2'):
    # Get AWS credentials from current session
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()

    # Print current identity for verification
    sts = session.client('sts')
    print(f"Current identity: {sts.get_caller_identity()}")

    # OTLP endpoint URL
    endpoint = f'https://logs.{region}.amazonaws.com/v1/logs'

    # Log group and stream names
    log_group_name = '/aws/otlp/logs'
    log_stream_name = f'otlp-stream-{datetime.now().strftime("%Y-%m-%d")}'

    client = session.client('logs')
    ensure_log_group_exists(client, log_group_name)
    ensure_log_stream_exists(client, log_group_name, log_stream_name)

    # Headers
    headers = {
        'Content-Type': 'application/json',
        'x-aws-log-group': log_group_name,
        'x-aws-log-stream': log_stream_name
    }

    # Log data in OTLP format
    log_data = {
        "resourceLogs": [{
            "resource": {
                "attributes": [{
                    "key": "service.name",
                    "value": {"stringValue": "my-service"}
                }]
            },
            "scopeLogs": [{
                "scope": {
                    "name": "CWOTELLogsExporter",
                    "version": "1.0.0"
                },
                "logRecords": [{
                    "timeUnixNano": str(int(datetime.now().timestamp() * 1e9)),
                    "severityText": "INFO",
                    "body": {
                        "stringValue": "Test log message via OTLP endpoint"
                    },
                    "traceId": str(uuid.uuid4()),
                    "spanId": "EEE19B7EC3C1B174",
                    "parentSpanId": "EEE19B7EC3C1B173",
                    "attributes": [{
                        "key": "custom_field",
                        "value": {"stringValue": "test_value"}
                    }, {
                        "key": "parentSpanId",
                        "value": {"stringValue": str(uuid.uuid4())}
                    }]
                }]
            }]
        }]
    }

    try:
        # Sign the request with SigV4
        signed_headers = sign_request(
            endpoint,
            log_data,
            headers,
            credentials,
            region
        )

        print("Sending request to OTLP endpoint...")
        print(f"Endpoint: {endpoint}")
        print(f"Headers: {signed_headers}")
        print(f"Body: {json.dumps(log_data, indent=2)}")

        # Send the request
        response = requests.post(
            endpoint,
            json=log_data,
            headers=signed_headers,
            verify=True  # Enable SSL verification
        )

        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text}")

    except Exception as e:
        print(f"Error sending logs: {str(e)}")
        raise e

if __name__ == "__main__":
    # Make sure you've run ada credentials update before running this
    send_logs_via_otlp()

from opentelemetry.sdk.trace.export import SpanExporter
import boto3
import json
import time
import requests
from datetime import datetime
from types import MappingProxyType
from botocore.exceptions import ClientError
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

class CloudWatchExporter(SpanExporter):
    def __init__(self, log_group_name, log_stream_name):
        self.client = boto3.client('logs')
        self.log_group_name = log_group_name
        self.log_stream_name = log_stream_name
        self._ensure_log_group_exists()
        self._ensure_log_stream_exists()
        self.sequence_token = None
        self.region='us-west-2'
    
    def _ensure_log_stream_exists(self):
        try:
            self.client.create_log_stream(
                logGroupName=self.log_group_name,
                logStreamName=self.log_stream_name
            )
            print(f"Created log stream: {self.log_stream_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                print(f"Error creating log stream: {str(e)}")
                raise
    
    def _ensure_log_group_exists(self):
        try:
            self.client.create_log_group(logGroupName=self.log_group_name)
            print(f"Created log group: {self.log_group_name}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                print(f"Error creating log group: {str(e)}")
                raise

    def _convert_attributes(self, attributes):
        if isinstance(attributes, MappingProxyType):
            return dict(attributes)
        return attributes

    def _sign_request(self, service, url, body, headers, credentials):
        """Helper function to sign the request with AWS SigV4"""
        request = AWSRequest(
            method='POST',
            url=url,
            data=json.dumps(body),
            headers=headers
        )
        SigV4Auth(credentials, service, self.region).add_auth(request)
        return dict(request.headers)


    def _convert_value(self, value):
        if isinstance(value, str):
            return {"stringValue": value}
        elif isinstance(value, bool):
            return {"boolValue": value}
        elif isinstance(value, int):
            return {"intValue": str(value)}
        elif isinstance(value, float):
            return {"doubleValue": value}
        elif isinstance(value, list):
            return {
                "arrayValue": {
                    "values": [{"stringValue": str(item)} for item in value]
                }
            }
        elif isinstance(value, dict):
            return {
                "kvlistValue": {
                    "values": [
                        {
                            "key": k,
                            "value": {"stringValue": str(v)}
                        }
                        for k, v in value.items()
                    ]
                }
            }
        return {"stringValue": str(value)}

    def _convert_dict_to_attributes(self, input_dict):
        attributes = []
        for key, value in input_dict.items():
            attributes.append({
                "key": key,
                "value": self._convert_value(value)
            })
        return attributes


    def _convert_spans_to_log_records(self, spans):
        log_events = []
        for span in spans:
            # Convert span to CloudWatch log event format
            event = {
                "timeUnixNano": str(int(datetime.now().timestamp() * 1e9)),  # current timestamp in milliseconds
                "severityText": "INFO",
                "traceId": hex(span.context.trace_id)[2:],
                "spanId": hex(span.context.span_id)[2:],
                "attributes": [{
                    "key": "parent_id",
                    "value": {"stringValue": hex(span.parent.span_id)[2:] if span.parent else None}
                }, {
                    "key": "name",
                    "value": {"stringValue": span.name}
                }, {
                    "key": "start_time",
                    "value": {"intValue": span.start_time}
                }, {
                    "key": "end_time",
                    "value": {"intValue": span.end_time}
                }, {
                    "key": "status",
                    "value": {
                        "kvlistValue": {
                            "values": [{
                                "key": "status_code",
                                "value": {
                                    "stringValue": span.status.status_code.name
                                }
                            }, {
                                "key": "status_code",
                                "value": {
                                    "stringValue": span.status.description
                                }
                            }]
                        }
                    }
                }] + self._convert_dict_to_attributes(self._convert_attributes(span.attributes))
            }
            log_events.append(event)
        return log_events

    def _convert_spans_to_OTEL_span_records(self, spans):
        log_events = []
        for span in spans:
            # Convert span to CloudWatch log event format
            event = {
                "timeUnixNano": str(int(datetime.now().timestamp() * 1e9)),  # current timestamp in milliseconds
                "severityText": "INFO",
                "traceId": hex(span.context.trace_id)[2:],
                "spanId": hex(span.context.span_id)[2:],
                "parentSpanId": hex(span.parent.span_id)[2:] if span.parent else None,
                "startTimeUnixNano": span.start_time,
                "endTimeUnixNano": span.end_time,
                "name": span.name,
                "attributes": [{
                    "key": "status",
                    "value": {
                        "kvlistValue": {
                            "values": [{
                                "key": "status_code",
                                "value": {
                                    "stringValue": span.status.status_code.name
                                }
                            }, {
                                "key": "status_code",
                                "value": {
                                    "stringValue": span.status.description
                                }
                            }]
                        }
                    }
                }] + self._convert_dict_to_attributes(self._convert_attributes(span.attributes))
            }
            log_events.append(event)
        return log_events
    
    def export_logs(self, spans):
        # Get AWS credentials from current session
        session = boto3.Session()
        credentials = session.get_credentials().get_frozen_credentials()

        # OTLP endpoint URL
        endpoint = f'https://logs.{self.region}.amazonaws.com/v1/logs'

        # Headers
        headers = {
            'Content-Type': 'application/json',
            'x-aws-log-group': self.log_group_name,
            'x-aws-log-stream': self.log_stream_name
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
                    "logRecords": self._convert_spans_to_log_records(spans)
                }]
            }]
        }

        try:
            # Sign the request with SigV4
            signed_headers = self._sign_request(
                endpoint,
                log_data,
                headers,
                credentials
            )

            print("Sending request to OTLP endpoint...")
            print(f"Endpoint: {endpoint}")
            # print(f"Headers: {signed_headers}")
            # print(f"Body: {json.dumps(log_data, indent=2)}")

            # Send the request
            response = requests.post(
                endpoint,
                json=log_data,
                headers=signed_headers,
                verify=True  # Enable SSL verification
            )

            # print(f"\nResponse status: {response.status_code}")
            # print(f"Response headers: {dict(response.headers)}")
            # print(f"Response body: {response.text}")

        except Exception as e:
            print(f"Error sending logs: {str(e)}")
            raise e

    def export(self, spans):
        # Get AWS credentials from current session
        session = boto3.Session()
        credentials = session.get_credentials().get_frozen_credentials()

        # OTLP endpoint URL
        endpoint = f'https://xray.{self.region}.amazonaws.com/v1/traces'

        # Headers
        headers = {
            'Content-Type': 'application/json'
        }

        # Log data in OTLP format
        log_data = {
            "resourceSpans": [{
                "resource": {
                    "attributes": [{
                        "key": "service.name",
                        "value": {"stringValue": "my-service"}
                    }]
                },
                "scopeSpans": [{
                    "scope": {
                        "name": "CWOTELLogsExporter",
                        "version": "1.0.0"
                    },
                    "spans": self._convert_spans_to_OTEL_span_records(spans)
                }]
            }]
        }

        try:
            # Sign the request with SigV4
            signed_headers = self._sign_request(
                'xray',
                endpoint,
                log_data,
                headers,
                credentials
            )

            print("Sending request to OTLP endpoint...")
            print(f"Endpoint: {endpoint}")
            print(f"Headers: {signed_headers}")
            # print(f"Body: {json.dumps(log_data, indent=2)}")

            # Send the request
            response = requests.post(
                endpoint,
                json=log_data,
                headers=signed_headers,
                verify=True  # Enable SSL verification
            )

            print(f"\nResponse status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            # print(f"Response body: {response.text}")

        except Exception as e:
            print(f"Error sending logs: {str(e)}")
            raise e
        
    def export_v1(self, spans):
        try:
            log_events = []
            for span in spans:
                # Convert span to CloudWatch log event format
                event = {
                    'timestamp': int(time.time() * 1000),  # current timestamp in milliseconds
                    'message': json.dumps({
                        'name': span.name,
                        'trace_id': hex(span.context.trace_id)[2:],  # convert to hex string
                        'span_id': hex(span.context.span_id)[2:],  # convert to hex string
                        'parent_id': hex(span.parent.span_id)[2:] if span.parent else None,
                        'start_time': span.start_time,
                        'end_time': span.end_time,
                        'attributes': self._convert_attributes(span.attributes),
                        'events': [
                            {
                                'name': event.name,
                                'timestamp': event.timestamp,
                                'attributes': self._convert_attributes(event.attributes)
                            }
                            for event in span.events
                        ],
                        'status': {
                            'status_code': span.status.status_code.name,
                            'description': span.status.description
                        }
                    }, default=str)  # handle any non-serializable types
                }
                log_events.append(event)

            if log_events:
                kwargs = {
                    'logGroupName': self.log_group_name,
                    'logStreamName': self.log_stream_name,
                    'logEvents': log_events
                }

                # Add sequence token if we have one
                if self.sequence_token:
                    kwargs['sequenceToken'] = self.sequence_token

                try:
                    response = self.client.put_log_events(**kwargs)
                    self.sequence_token = response.get('nextSequenceToken')
                    print(f"Successfully exported {len(log_events)} events to CloudWatch")
                except ClientError as e:
                    if e.response['Error']['Code'] == 'InvalidSequenceTokenException':
                        # Get the correct sequence token
                        streams = self.client.describe_log_streams(
                            logGroupName=self.log_group_name,
                            logStreamNamePrefix=self.log_stream_name
                        )
                        self.sequence_token = streams['logStreams'][0].get('uploadSequenceToken')
                        # Retry with correct sequence token
                        if self.sequence_token:
                            kwargs['sequenceToken'] = self.sequence_token
                        response = self.client.put_log_events(**kwargs)
                        self.sequence_token = response.get('nextSequenceToken')
                        print(f"Successfully exported {len(log_events)} events to CloudWatch after token refresh")
                    else:
                        print(f"Error exporting to CloudWatch: {str(e)}")
                        raise

        except Exception as e:
            print(f"Error in CloudWatch export: {str(e)}")
            raise

        return None
    
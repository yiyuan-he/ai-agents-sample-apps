import json
import boto3
import sys
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

print('Loading function')

# Initialize OpenTelemetry
resource = Resource.create({"service.name": "bedrock-lambda"})
trace.set_tracer_provider(TracerProvider(resource=resource))

# Set up the OTLP exporter
otlp_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Create a tracer
tracer = trace.get_tracer(__name__)

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    print("Context: " + str(context))
    input_str = event.get('input')
    model_str = event.get('model')

    # Initialize the Bedrock Runtime client
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    # Define the model ID and input text
    model_id = model_str or 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'
    input_text = input_str or "Please explain the concept of cloud computing."
    
    # Prepare the request body
    request_body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": input_text
                    }
                ]
            }
        ],
        "temperature": 0.5,
        "top_p": 1
    })
    
    try:
        # Invoke the Bedrock model
        with tracer.start_span("invoke_bedrock_model") as invoke_span:
            invoke_span.set_attribute("model_id", model_id)
            invoke_span.set_attribute("input_text", input_text)
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                contentType='application/json',
                accept='application/json',
                body=request_body
            )
            
            # Parse and return the response
            response_body = json.loads(response['body'].read())
            
            # Debug print to see the actual response structure
            print("Response body:", json.dumps(response_body, indent=2))
            
            return {
                'statusCode': 200,
                'body': json.dumps(response_body['content'][0]['text'])
            }
    except Exception as e:
        print(f"Error invoking Bedrock model: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }

def main():
	lambda_handler({}, {})


if __name__ == '__main__':
    sys.exit(main())  # next section explains the use of sys.exit

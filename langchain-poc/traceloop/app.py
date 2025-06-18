import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from traceloop.sdk import Traceloop

# Set up OpenTelemetry with BOTH exporters
tracer_provider = TracerProvider()

# Add Console exporter
console_exporter = ConsoleSpanExporter()
console_processor = BatchSpanProcessor(console_exporter)
tracer_provider.add_span_processor(console_processor)

# Add OTLP exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
otlp_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(otlp_processor)

# Set as global provider
trace.set_tracer_provider(tracer_provider)

Traceloop.init()

# Load environment variables from .env file
load_dotenv()

def main():
    # Initialize the LLM with AWS Bedrock
    # Using Claude 3 Haiku for fast responses
    llm = ChatBedrock(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        model_kwargs={
            "temperature": 0.7,
            "max_tokens": 500
        },
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-west-2")
    )

    # Create a prompt template
    prompt = ChatPromptTemplate.from_template(
        "You are a helpful assistant. The user says: {input}. Provide a helpful response."
    )

    # Create a chain
    chain = LLMChain(llm=llm, prompt=prompt)

    # Run the chain
    print("LangChain Sample App")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        # Process the input through the chain
        response = chain.invoke({"input": user_input})
        print(f"\nAI: {response['text']}\n")

if __name__ == "__main__":
    # AWS Bedrock uses AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    # or IAM roles/instance profiles - no API key needed
    print("Starting LangChain app with AWS Bedrock...")
    print("Make sure AWS credentials are configured via:")
    print("  - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
    print("  - AWS CLI configuration (~/.aws/credentials)")
    print("  - IAM instance profile (if running on EC2)")
    print()

    main()

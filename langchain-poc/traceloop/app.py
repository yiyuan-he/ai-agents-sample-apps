import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
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
    # Initialize the LLM
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",  # You can change to another model
        temperature=0.7,
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
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Create a .env file with your API key: OPENAI_API_KEY=your-key-here")
        exit(1)

    main()

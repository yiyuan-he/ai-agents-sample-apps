import os
import asyncio
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

import openlit

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

openlit.init()

# Load environment variables from .env file
load_dotenv()

async def run_chain(chain, user_input):
    # Use the asynchronous version to process the input
    response = await chain.ainvoke({"input": user_input})
    return response

def main():
    # Initialize the LLM with Ollama
    llm = ChatOllama(
        model="llama3.2",  # You can use other models like mistral, phi, etc.
        temperature=0.7,
        base_url="http://localhost:11434"  # Default Ollama URL
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

        # Process the input through the chain - run the async function in the event loop
        response = asyncio.run(run_chain(chain, user_input))
        print(f"\nAI: {response['text']}\n")

if __name__ == "__main__":
    # Check if Ollama is running
    print("Make sure Ollama is running locally.")
    print("Install Ollama from: https://ollama.ai")
    print("Then run: ollama pull llama3.2")
    print("")

    main()

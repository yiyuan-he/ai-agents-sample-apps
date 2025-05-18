import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from openinference.instrumentation.langchain import LangChainInstrumentor

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

# Instrument LangChain - this will automatically capture LLM prompts in spans
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)

# Load environment variables from .env file
load_dotenv()


def get_prompts():
    """Returns a list of predefined prompts to try"""
    return [
        "Tell me about quantum computing",
        "Explain the theory of relativity",
        "What is the difference between machine learning and deep learning?",
        "How does blockchain technology work?",
        "Describe the process of photosynthesis",
    ]


def main():
    # Initialize the LLM
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",  # You can change to another model
        temperature=0.7,
    )

    # Create a prompt template
    prompt_template = ChatPromptTemplate.from_template(
        "You are a helpful assistant. The user asks: {input}. Provide a concise response."
    )

    # Create a chain
    chain = LLMChain(llm=llm, prompt=prompt_template)

    # Run the chain with multiple prompts
    print("LangChain Sample App with Multiple Prompts")
    print("1. Use predefined prompts")
    print("2. Enter your own prompts")
    print("Type 'exit' to quit\n")

    choice = input("Choose option (1 or 2): ")

    if choice == "1":
        # Use predefined prompts
        prompts = get_prompts()

        for i, prompt_text in enumerate(prompts):
            print(f"\nProcessing prompt {i+1}: {prompt_text}")

            # Process the input through the chain
            # The LangChainInstrumentor will automatically capture and record the prompts
            response = chain.invoke({"input": prompt_text})
            print(f"\nAI: {response['text']}\n")

    else:
        # Manual prompt entry
        prompts_list = []

        while True:
            user_input = input(
                "\nEnter prompt (or 'done' to process all prompts, 'exit' to quit): "
            )

            if user_input.lower() == "exit":
                return

            if user_input.lower() == "done":
                break

            prompts_list.append(user_input)

        for i, prompt_text in enumerate(prompts_list):
            print(f"\nProcessing prompt {i+1}: {prompt_text}")

            # Process the input through the chain
            # The LangChainInstrumentor will automatically capture and record the prompts
            response = chain.invoke({"input": prompt_text})
            print(f"\nAI: {response['text']}\n")


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Create a .env file with your API key: OPENAI_API_KEY=your-key-here")
        exit(1)

    main()

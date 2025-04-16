import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.crewai import CrewAIInstrumentor

# Load environment variables from .env file
load_dotenv()

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

# Instrument CrewAI
CrewAIInstrumentor().instrument(tracer_provider=tracer_provider)

def main():
    # Initialize the LLM
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",  # You can change to another model
        temperature=0.7,
    )

    # Create an agent (equivalent to LangChain's chain)
    assistant_agent = Agent(
        role="Assistant",
        goal="Provide helpful responses to user queries",
        backstory="You are a helpful assistant that provides accurate and useful information.",
        verbose=True,
        llm=llm,
    )

    print("CrewAI Sample App")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        # Create a task for the agent with the user's input
        response_task = Task(
            description=f"The user says: {user_input}. Provide a helpful response.",
            expected_output="A helpful and informative response to the user's query",
            agent=assistant_agent
        )

        # Create a crew with just the assistant agent
        crew = Crew(
            agents=[assistant_agent],
            tasks=[response_task],
            verbose=True,
            process=Process.sequential  # Process tasks sequentially
        )

        # Run the crew to get a response
        result = crew.kickoff()
        print(f"\nAI: {result}\n")

if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Create a .env file with your API key: OPENAI_API_KEY=your-key-here")
        exit(1)

    main()

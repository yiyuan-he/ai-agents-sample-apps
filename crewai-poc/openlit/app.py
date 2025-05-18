import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
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

def main():
    # Initialize the chat agent
    chat_agent = Agent(
        role="Helpful Assistant",
        goal="Assist users by providing helpful and accurate responses",
        backstory="I'm an AI assistant designed to help users with their queries and provide informative responses.",
        verbose=True,
        allow_delegation=False
    )

    # Create a task for the agent
    chat_task = Task(
        description="Respond to user queries in a helpful and informative way.",
        expected_output="A helpful and informative response to the user's query.",
        agent=chat_agent,
        context=[]
    )

    # Create a crew with just one agent
    crew = Crew(
        agents=[chat_agent],
        tasks=[chat_task],
        verbose=True,
        process=Process.sequential,
    )

    # Run the chat interface
    print("CrewAI Chat Sample App")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        # Update the task with the current user input
        chat_task.description = f"Respond to the following user query in a helpful and informative way: {user_input}"
        chat_task.expected_output = "A helpful and informative response to the user's query."

        # Process the task and get the response
        response = crew.kickoff()

        print(f"\nAI: {response}\n")

if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Create a .env file with your API key: OPENAI_API_KEY=your-key-here")
        exit(1)

    main()

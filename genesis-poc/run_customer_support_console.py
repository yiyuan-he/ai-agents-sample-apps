import os
import uuid
from primitives.graph import ExecutionGraph 
from tools.tool_utils import _print_event
from opentelemetry.instrumentation.langchain import LangchainInstrumentor
from customer_support_assistant import CustomerSupportAssistant
from opentelemetry import trace
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

class Demo:

    def __init__(self):
        self.assistant = CustomerSupportAssistant()


langchain_project_id = "LangChain_AWS_" + str(uuid.uuid4())
# Set your LangSmith API key
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_TRACING_V2"] = "true"  # Enable tracing
os.environ["LANGCHAIN_PROJECT"] = langchain_project_id


# Example usage (testing the graph without Streamlit):
if __name__ == "__main__":
    # Let's create an example conversation a user might have with the assistant
    tutorial_questions = [
        "Hi there, what time is my flight?",
        # "Am i allowed to update my flight to something sooner? I want to leave later today.",
        # "Update my flight to sometime next week then",
        # "The next available option is great",
        # "what about lodging and transportation?",
        # "Yeah i think i'd like an affordable hotel for my week-long stay (7 days). And I'll want to rent a car.",
        # "OK could you place a reservation for your recommended hotel? It sounds nice.",
        # "yes go ahead and book anything that's moderate expense and has availability.",
        # "Now for a car, what are my options?",
        # "Awesome let's just get the cheapest option. Go ahead and book for 7 days",
        # "Cool so now what recommendations do you have on excursions?",
        # "Are they available while I'm there?",
        # "interesting - i like the museums, what options are there? ",
        # "OK great pick one and book it for my second day there.",
    ]

    tracer_provider = TracerProvider()

    otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
    otlp_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(otlp_processor)

    # Set as global provider
    trace.set_tracer_provider(tracer_provider)

    LangchainInstrumentor().instrument(tracer_provider=tracer_provider)

    _printed = set()
    customer_support_agent = Demo().assistant
    thread_id = None
    for question in tutorial_questions:
        try:
            events, thread_id = customer_support_agent.submit(
                query=question, thread_id=thread_id
            )
            _print_event(events, _printed)
        finally:
            pass

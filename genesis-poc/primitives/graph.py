import os
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from primitives.state import State 
from primitives.agent import Assistant 
from tools.tool_utils import create_tool_node_with_fallback
import uuid
from langgraph_checkpoint_aws.saver import BedrockSessionSaver

class ExecutionGraph:

    def __init__(self, assistant_runnable, assistant_tools):
        self.session_id = None
        self.graph = self.create_customer_support_graph(assistant_runnable, assistant_tools)
        self.config = None

    def create_customer_support_graph(self, assistant_runnable, assistant_tools):
        builder = StateGraph(State)

        # Define nodes: these do the work
        builder.add_node("assistant", Assistant(assistant_runnable))
        builder.add_node("tools", create_tool_node_with_fallback(assistant_tools))
        # Define edges: these determine how the control flow moves
        builder.add_edge(START, "assistant")
        builder.add_conditional_edges(
            "assistant",
            tools_condition,
        )
        builder.add_edge("tools", "assistant")

        # The checkpointer lets the graph persist its state
        # this is a complete memory for the entire graph.
        # Configure BedrockSessionSaver with region from environment variable
        session_saver = BedrockSessionSaver(
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        self.session_id = session_saver.session_client.create_session().session_id
        print("Session ID: ", self.session_id)
        return builder.compile(checkpointer=session_saver)

    def run(self, query, callbacks=None, thread_id=None, checkpoint_id=None, resume=False):
        thread_id = self.session_id or thread_id or str(uuid.uuid4())
        print("Thread ID: ", thread_id)
        self.config = {
            "configurable": {
                # The passenger_id is used in our flight tools to
                # fetch the user's flight information
                "passenger_id": "3442 587242",
                # Checkpoints are accessed by thread_id
                "thread_id": thread_id,
            }
        }
        if callbacks:
            self.config["callbacks"] = callbacks
        return self.graph.invoke(
            {"messages": ("user", query)}, self.config, stream_mode="values"
        ), thread_id

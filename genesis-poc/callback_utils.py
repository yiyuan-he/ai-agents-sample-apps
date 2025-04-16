from typing import Callable, TypeVar, Dict, Any
import inspect
import json
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
from streamlit.delta_generator import DeltaGenerator

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
import time
from typing import List
from customer_support_assistant import CustomerSupportAssistant

# Define a function to wrap and add context to Streamlit's integration with LangGraph
def get_streamlit_cb(parent_container: DeltaGenerator) -> BaseCallbackHandler:
    """
    Creates a Streamlit callback handler that integrates fully with any LangChain ChatLLM integration,
    updating the provided Streamlit container with outputs such as tokens, model responses,
    and intermediate steps. This function ensures that all callback methods run within
    the Streamlit execution context, fixing the NoSessionContext() error commonly encountered
    in Streamlit callbacks.

    Args:
        parent_container (DeltaGenerator): The Streamlit container where the text will be rendered
                                           during the LLM interaction.
    Returns:
        BaseCallbackHandler: An instance of StreamlitCallbackHandler configured for full integration
                             with ChatLLM, enabling dynamic updates in the Streamlit app.
    """

    # Define a custom callback handler class for managing and displaying stream events in Streamlit
    class StreamHandler(BaseCallbackHandler):
        """
        Custom callback handler for Streamlit that updates a Streamlit container with new tokens.
        """

        def __init__(self, container: st.delta_generator.DeltaGenerator, initial_text: str = ""):
            """
            Initializes the StreamHandler with a Streamlit container and optional initial text.
            Args:
                container (st.delta_generator.DeltaGenerator): The Streamlit container where text will be rendered.
                initial_text (str): Optional initial text to start with in the container.
            """
            self.container = container  # The Streamlit container to update
            self.thoughts_placeholder = self.container.container()  # container to hold tool_call renders
            self.tool_output_placeholder = None # placeholder for the output of the tool call to be in the expander
            self.status_placeholder = None
            self.token_placeholder = self.container.empty()  # for token streaming
            self.text = initial_text  # The text content to display, starting with initial text
            self.snapshot_value_placeholder = None  # Add this line
            self.debug_view = None # Placeholder for debug view
            self.replay_callback_proc = None
            self.snapshot = None
            self.current_llm_box = None

        def on_replay_clicked(self, callback_proc):
            print(f"Callback is registered with callback_proc {callback_proc}")
            self.replay_callback_proc = callback_proc


        def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
            """
            Callback method triggered when the language model starts processing.
            Args:
                serialized (Dict[str, Any]): The serialized model data.
                prompts (List[str]): The prompts sent to the model.
                **kwargs: Additional keyword arguments.
            """
            print(f"On LL Start : serialized={str(serialized)}, prompts={str(prompts)}, kwargs={str(kwargs)}")
            # self.text = ""  # Reset the text when a new LLM interaction starts
            # self.token_placeholder.write(self.text)  # Write an empty string to clear previous content
    
            # # Create a new expander for this LLM interaction
            # self.current_llm_box = self.container.expander("LLM Interaction", expanded=True)
            # with self.current_llm_box:
            #     st.write("**Input:**")
            #     st.code(prompts[0])
            #     st.write("**Output:**")


        def on_llm_end(self, response, **kwargs: Any) -> None:
            print(f"On LL end {response}, kwargs={str(kwargs)}")
            # with self.current_llm_box:
            #     st.code(self.token_stream)
                
            #     # Add token usage information if available
            #     if hasattr(response, 'llm_output') and response.llm_output:
            #         token_usage = response.llm_output.get('token_usage', {})
            #         st.write("**Token Usage:**")
            #         st.json(token_usage)


        def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
            """
            Run when the tool starts running.
            Args:
                serialized (Dict[str, Any]): The serialized tool.
                input_str (str): The input string.
                kwargs (Any): Additional keyword arguments.
            """
            print(f"On tool Start : serialized={str(serialized)}, input_str={input_str}, kwargs={str(kwargs)}")

            checkpoint_config = {}
            checkpoint_config["configurable"] = {}
            checkpoint_config["configurable"]["thread_id"] = kwargs["metadata"]["thread_id"]

            self.snapshot = CustomerSupportAssistant().get_orchestrator_graph().get_state(checkpoint_config)
            snapshot_id = self.snapshot.config["configurable"]["checkpoint_id"]
            print(f"Snapshot ID: {snapshot_id} and snapshot {str(self.snapshot)}")

            with self.thoughts_placeholder:
                self.status_placeholder = st.empty()   # Placeholder to show the tool's status
                with self.status_placeholder.status(f"Calling Tool...", expanded=True) as s:
                    tool_name = serialized["name"]
                    st.write("**Tool used:**", tool_name)  # Show which tool is being called
                    st.write("**Input:**")
                    st.code(input_str or "None")   # Display the input data sent to the tool
                    # Placeholder for tool output that will be updated later below
                    output_container = st.container()
                    with output_container:
                        st.write("**Output:**")
                        self.tool_output_placeholder = st.empty()
                    self.tool_output_placeholder = st.empty()
                    # Create placeholders for snapshot ID
                    self.debug_view = st.empty()
                    self.snapshot_value_placeholder = st.empty()  # Add this line
                    s.update(label=f"Called {tool_name} Tool!") 

        def on_tool_end(self, output: Any, **kwargs: Any) -> Any:
            """
            Run when the tool ends.
            Args:
                output (Any): The output from the tool.
                kwargs (Any): Additional keyword arguments.
            """
            print(f"On tool end {output}, kwargs={str(kwargs)}")

            # We assume that `on_tool_end` comes after `on_tool_start`, meaning output_placeholder exists
            with self.tool_output_placeholder:
                self.tool_output_placeholder.code(json.dumps(output))   # Display the tool's output

            # Display snapshot ID if available
            if self.snapshot:
                checkpoint_id = self.snapshot.config["configurable"]["checkpoint_id"]
                with self.debug_view:
                    st.write("Checkpoint Information")
                    # Create unique key for this instance
                    unique_key = f"replay_{checkpoint_id}_{int(time.time())}"   
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Checkpoint ID:** `{checkpoint_id}`")
                    with col2:
                        col2.button("Replay", key=unique_key, use_container_width=True, on_click=self.replay_callback_proc, args=(checkpoint_id,))

                with self.snapshot_value_placeholder:
                    st.code(f"""
Snapshot Value:
{self.snapshot}
""", language='json')


    # Define a type variable for generic type hinting in the decorator, ensuring the original
    # function and wrapped function maintain the same return type.
    fn_return_type = TypeVar('fn_return_type')

    # Decorator function to add Streamlit's execution context to a function
    def add_streamlit_context(fn: Callable[..., fn_return_type]) -> Callable[..., fn_return_type]:
        """
        Decorator to ensure that the decorated function runs within the Streamlit execution context.
        This is necessary for interacting with Streamlit components from within callback functions
        and prevents the NoSessionContext() error by adding the correct session context.

        Args:
            fn (Callable[..., fn_return_type]): The function to be decorated, typically a callback method.
        Returns:
            Callable[..., fn_return_type]: The decorated function that includes the Streamlit context setup.
        """
        # Retrieve the current Streamlit script execution context.
        # This context holds session information necessary for Streamlit operations.
        ctx = get_script_run_ctx()

        def wrapper(*args, **kwargs) -> fn_return_type:
            """
            Wrapper function that adds the Streamlit context and then calls the original function.
            If the Streamlit context is not set, it can lead to NoSessionContext() errors, which this
            wrapper resolves by ensuring that the correct context is used when the function runs.

            Args:
                *args: Positional arguments to pass to the original function.
                **kwargs: Keyword arguments to pass to the original function.
            Returns:
                fn_return_type: The result from the original function.
            """
            # Add the previously captured Streamlit context to the current execution.
            # This step fixes NoSessionContext() errors by ensuring that Streamlit knows which session
            # is executing the code, allowing it to properly manage session state and updates.
            add_script_run_ctx(ctx=ctx)
            return fn(*args, **kwargs)  # Call the original function with its arguments

        return wrapper

    # Create an instance of Streamlit's StreamHandler with the provided Streamlit container
    st_cb = StreamHandler(parent_container)

    # Iterate over all methods of the StreamHandler instance
    for method_name, method_func in inspect.getmembers(st_cb, predicate=inspect.ismethod):
        print(f"Processing method: {method_name}")
        if method_name.startswith('on_'):  # Identify callback methods that respond to LLM events
            # Wrap each callback method with the Streamlit context setup to prevent session errors
            setattr(st_cb, method_name,
                    add_streamlit_context(method_func))  # Replace the method with the wrapped version

    # Return the fully configured StreamHandler instance, now context-aware and integrated with any ChatLLM
    return st_cb
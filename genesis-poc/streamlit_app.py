import streamlit as st
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import json
from dotenv import load_dotenv
from customer_support_assistant import CustomerSupportAssistant
from callback_utils import get_streamlit_cb
import os
import uuid

load_dotenv()
# langchain_project_id = "LangChain_AWS_" + str(uuid.uuid4())
# # Set your LangSmith API key
# os.environ["LANGCHAIN_API_KEY"] = "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"
# os.environ["LANGCHAIN_TRACING_V2"] = "false"  # Enable tracing
# os.environ["LANGCHAIN_PROJECT"] = langchain_project_id

@st.cache_resource
def get_app_instance():
    return ArithmeticStreamlitApp()

class ArithmeticStreamlitApp:
    def __init__(self):
        self.initialize_session_state()
        self.agent = CustomerSupportAssistant()

    def initialize_session_state(self):
        if 'history' not in st.session_state:
            st.session_state.history = []
        if 'execution_in_progress' not in st.session_state:
            st.session_state.execution_in_progress = False
        if 'paused' not in st.session_state:
            st.session_state.paused = False
        if 'replay_checkpoint' not in st.session_state:
            st.session_state.replay_checkpoint = None
        if 'replay_requested' not in st.session_state:
            st.session_state.replay_requested = False
        if 'thread_id' not in st.session_state:
            st.session_state.thread_id = None
        if 'messages' not in st.session_state:
            st.session_state.messages = []

    def create_ui(self):
        # Input section
        query = st.text_input("Enter your query:", 
                            placeholder="How can I help you?")
        
        print(f"session state = {st.session_state}")
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
        with col1:
            submit = st.button("Submit")
        with col2:
            pause = st.button("Pause")
        with col3:
            resume = st.button("Resume")
        with col4:
            if st.button("Clear History"):
                st.session_state.execution_in_progress = False  # Reset this too
                st.session_state.paused = False
                st.session_state.replay_requested = False
                st.session_state.replay_checkpoint = None
                st.session_state.history = []

        # Loop through all messages in the session state and render them as a chat on every st.refresh mech
        for msg in st.session_state.get("messages", []):
            # https://docs.streamlit.io/develop/api-reference/chat/st.chat_message
            # we store them as AIMessage and HumanMessage as its easier to send to LangGraph
            if isinstance(msg, AIMessage):
                st.chat_message("assistant").write(msg.content)
            # elif isinstance(msg, ToolMessage):
            #     st.chat_message("tool").write(msg.content)
            elif isinstance(msg, HumanMessage):
                st.chat_message("user").write(msg.content)

        return query, submit, pause, resume

    def handle_replay_request(self, checkpoint_id: str):
        """Handle snapshot view button click"""
        print(f"Replay requested for checkpoint: {checkpoint_id}")
        st.session_state.replay_checkpoint = checkpoint_id
        st.session_state.replay_requested = True
        st.session_state.execution_in_progress = True
        
    def run_agent(self, query: str, resume=False, checkpoint_id=None):
        """Run the arithmetic agent with Streamlit callbacks"""
        try:        
            if not resume:
                st.session_state.execution_in_progress = True

            st.session_state.messages.append(HumanMessage(content=query))
            st.chat_message("user").write(query)

            with st.chat_message("assistant"):
                # Create Streamlit callback handler
                st_callback = get_streamlit_cb(st.container())
                st_callback.on_replay_clicked(self.handle_replay_request)

                # Execute the graph with callbacks
                result, thread_id = self.agent.submit(
                    query,
                    callbacks=[st_callback],
                    thread_id = st.session_state.thread_id if (st.session_state.replay_requested or resume) else None,
                    checkpoint_id=st.session_state.replay_checkpoint if st.session_state.replay_requested else (
                        checkpoint_id if resume else None
                    ),
                    resume=resume or st.session_state.replay_requested
                )

                print(f"result = {result}")
                last_message = result.get('messages')[-1]

                # tool_messages = [msg for msg in result.get('messages') if isinstance(msg, ToolMessage)]
                # st.session_state.messages.extend(tool_messages)
                ai_message = AIMessage(content=last_message.content)
                st.session_state.messages.append(ai_message)   # Add that last message to the st_message_state
            
                # Immediately display the AI's response
                st.write(ai_message.content)

                # Reset replay flags after execution
                if st.session_state.replay_requested:
                    st.session_state.replay_requested = False
                    st.session_state.replay_checkpoint = None

                print(f"Getting latest thread id {thread_id}")
                # Store the latest checkpoint ID
                st.session_state.current_checkpoint = thread_id
                st.session_state.thread_id = thread_id

            # Only reset execution_in_progress if we're not paused
            if not st.session_state.paused:
                st.session_state.execution_in_progress = False
        except Exception as e:
            st.session_state.execution_in_progress = False
            st.error(f"Error during calculation: {str(e)}")


def main():
    app = get_app_instance()
    query, submit, pause, resume = app.create_ui()
    
    print(f"In main again with session state {st.session_state} and query {query}")
    
    # Handle pause action
    if pause and st.session_state.execution_in_progress:
        st.session_state.paused = True
        st.session_state.execution_in_progress = False  # Set when resumed
        st.info("Execution paused. Click Resume to continue.")
    
    # Handle resume action
    if resume and st.session_state.paused:
        st.session_state.paused = False
        st.session_state.execution_in_progress = True  # Reset when paused
        st.info("Execution Resumed.")
        with st.spinner("Resuming calculation..."):
           app.run_agent(query, resume=True)

    if submit and query and not st.session_state.paused:
        with st.spinner("Fetching result..."):
            app.run_agent(query)
    elif st.session_state.replay_requested and query:
        with st.spinner("Replaying..."):
            app.run_agent(query, resume=True)


st.title("Trip Planning Assistant")

# st write magic
"""

---
"""

if __name__ == "__main__":
    main()

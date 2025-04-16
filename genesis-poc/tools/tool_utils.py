from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda

import json

def handle_tool_error(state) -> dict:
    print("Error in tool call: ", state)
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_name = self.tools_by_name[tool_call["name"]]
            tool_result = self.invoke(tool_call)
            print(f"Tool result: {tool_result}")
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

    def invoke(self, tool_call):
        tool_result = self.tools_by_name[tool_call["name"]].invoke(
            tool_call["args"]
        )
        return tool_result


def create_tool_node_with_fallback(tools: list) -> dict:
    try:
        return BasicToolNode(tools)
    except Exception as e:
        print("Error in tool node: ", e)
        return RunnableLambda(handle_tool_error)


def _print_event(event: dict, _printed: set, max_length=1500):
    messages = event.get("messages")
    for message in messages or []:
        if isinstance(message, ToolMessage):
            print(f"\n================================== Tool Message ==================================")
        elif isinstance(message, HumanMessage):
            print(f"\n================================== Human Message ==================================")
        elif isinstance(message, AIMessage):
            print(f"\n================================== Ai Message ==================================")
        print(message.content[:max_length])
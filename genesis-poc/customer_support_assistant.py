import shutil
import os
from primitives.graph import ExecutionGraph 
from langchain_aws import ChatBedrock
from tools.flight_tools import (
    fetch_user_flight_information,
    search_flights,
    update_ticket_to_new_flight,
    cancel_ticket,
)
from tools.hotel_tools import (
    search_hotels,
    book_hotel,
    update_hotel,
    cancel_hotel,
)
from tools.car_rental_tools import (
    search_car_rentals,
    book_car_rental,
    update_car_rental,
    cancel_car_rental,
)
from tools.excursions import search_trip_recommendations, book_excursion, update_excursion, cancel_excursion
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from tools.tool_utils import _print_event
from setup import CustomerSupportSetup
from typing import Dict, Any

class CustomerSupportAssistant:

    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(CustomerSupportAssistant, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        # setup db
        CustomerSupportSetup()

        self.llm = ChatBedrock(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            provider="anthropic",
            credentials_profile_name="default",
            region_name="us-west-2"
        )

        self.primary_assistant_prompt = ChatPromptTemplate.from_messages(
            [(
                "system",
                "You are a helpful customer support assistant for Swiss Airlines. "
                " Use the provided tools to search for flights, company policies, and other information to assist the user's queries. "
                " When searching, be persistent. Expand your query bounds if the first search returns no results. "
                " If a search comes up empty, expand your search before giving up."
                "\n\nCurrent user:\n<User>\n{user_info}\n</User>"
                "\nCurrent time: {time}.",
            ),(
                "placeholder", "{messages}"
            )]
        ).partial(time=datetime.now)
        
        assistant_tools = [
            fetch_user_flight_information,
            search_flights,
            update_ticket_to_new_flight,
            cancel_ticket,
            search_car_rentals,
            book_car_rental,
            update_car_rental,
            cancel_car_rental,
            search_hotels,
            book_hotel,
            update_hotel,
            cancel_hotel,
            search_trip_recommendations,
            book_excursion,
            update_excursion,
            cancel_excursion,
        ]
        assistant_runnable = self.primary_assistant_prompt | self.llm.bind_tools(assistant_tools)
        self.orchestrator = ExecutionGraph(assistant_runnable, assistant_tools)

    def get_orchestrator_graph(self):
        return self.orchestrator.graph

    def submit(self, query, callbacks=None, thread_id=None, checkpoint_id=None, resume=False):
        return self.orchestrator.run(query, callbacks, thread_id, checkpoint_id, resume)

    def invoke(self, request: Dict[str, Any]):
        if request["type"] == "submit":
            return self.submit(request["query"])
        elif request["type"] == "get_orchestrator_graph":
            return self.get_orchestrator_graph()
        else:
            raise ValueError(f"Unknown request type: {request['type']}")
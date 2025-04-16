from customer_support_assistant import CustomerSupportAssistant
from genai_platform.platform import GenAIPlatform

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

# Initialize the platform
platform = GenAIPlatform()

# Register Agent
platform.register_agent("customer_support_agent", CustomerSupportAssistant)

# Register Tools
platform.register_action("fetch_user_flight_information", fetch_user_flight_information)
platform.register_action("search_flights", search_flights)
platform.register_action("update_ticket_to_new_flight", update_ticket_to_new_flight)
platform.register_action("cancel_ticket", cancel_ticket)
platform.register_action("search_car_rentals", search_car_rentals)
platform.register_action("book_car_rental", book_car_rental)
platform.register_action("update_car_rental", update_car_rental)
platform.register_action("cancel_car_rental", cancel_car_rental)
platform.register_action("search_hotels", search_hotels)
platform.register_action("book_hotel", book_hotel)
platform.register_action("update_hotel", update_hotel)
platform.register_action("cancel_hotel", cancel_hotel)
platform.register_action("search_trip_recommendations", search_trip_recommendations)
platform.register_action("book_excursion", book_excursion)
platform.register_action("update_excursion", update_excursion)
platform.register_action("cancel_excursion", cancel_excursion)

# Run the server
platform.run(host="0.0.0.0", port=8000)
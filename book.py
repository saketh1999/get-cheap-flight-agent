import asyncio
import json
import os
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser, BrowserConfig, Controller, ActionResult
from pydantic import SecretStr
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please add it to your .env file.")

# Fixed dates (defaults)
DEFAULT_DEPARTURE_DATE = "2025-05-05"  # May 5, 2025
DEFAULT_RETURN_DATE = "2025-05-12"     # May 12, 2025 (one week later)

# Initialize browser configuration
browser = Browser(
    config=BrowserConfig(
        headless=False
    )
)

# Initialize the Gemini LLM
llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-exp',
    api_key=SecretStr(GEMINI_API_KEY)
)

# Initialize the controller
controller = Controller()

async def book_flight(origin: str, destination: str, departure_date: str, 
                     return_date: Optional[str] = None, round_trip: bool = True) -> Dict[str, Any]:
    """
    Visit Kayak and search for flights based on user input
    
    Args:
        origin: Origin airport code (e.g., "SFO")
        destination: Destination airport code (e.g., "JFK")
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date in YYYY-MM-DD format (None for one-way)
        round_trip: Whether this is a round-trip flight (default: True)
    """
    print(f"Starting Kayak flight search for {origin} to {destination}...")
    
    # Format trip type
    trip_type = "round-trip" if round_trip else "one-way"
    
    # Format dates for display
    departure_display = datetime.strptime(departure_date, "%Y-%m-%d").strftime("%B %d, %Y")
    return_display = datetime.strptime(return_date, "%Y-%m-%d").strftime("%B %d, %Y") if return_date else ""
    
    task_prompt = f"""
    Follow these steps precisely to search for flights on Kayak:
    ---IMPORTANT: DO NOT GO TO OTHER WEBSITES OTHER THAN KAYAK.COM---
    ---IMPORTANT: DO NOT CLICK ON least expensive FLIGHT, JUST SCROLL DOWN---
    
    1. Go to https://www.kayak.com/
    
    2. If any popups appear or cookie consent is requested, close them or accept as appropriate.
    
    --IMPORTANT: CLEAR THE INPUT FIELD BEFORE ENTERING THE ORIGIN AND DESTINATION by clicking on the X button--
    --IMPORTANT: CLOSE ANY POPUPS THAT APPEAR DURING THE PROCESS--
    
    3. Set up the flight search:
       - Select {trip_type} flight
       - Enter origin: {origin}
       - Enter destination: {destination}
       - Set departure date: {departure_date}
       - Set return date: {return_date} if given if it is empty just ignore it. If it not present then click on the next month till you get the required date.

    
    4. Then I want you to go to this website https://www.kayak.com/flights/PAR-SFO/2025-06-17?ucs=1jljdmu&sort=bestflight_a. (Get the WestJest Flight data) on the page.


    REPORTING:
    Provide a structured description that includes:
    - The flight search parameters used
    - Details of the least expensive flight option found
    - Any additional fees or important notes about the booking process
    - Format the information clearly for easy reading
    
    Remember to be precise, thorough, and focus only on the flight booking task.
    """
    extended_system_message="""
    You are an advanced flight booking assistant with expertise in navigating travel websites, particularly Kayak.com. Your goal is to find the best flight options based on user requirements and provide detailed, accurate information.

    CORE CAPABILITIES:
    1. Navigate Kayak.com efficiently and accurately
    2. Handle various UI elements including popups, calendars, and dropdown menus
    3. Extract and analyze flight information
    4. Provide organized, detailed reports on flight options
    5. Adapt to different search parameters (one-way/round-trip, different dates, etc.)

    IMPORTANT GUIDELINES:
    - ONLY visit Kayak.com, do not navigate to other websites
    - Always clear input fields before entering new information
    - Close any popups that appear during the process
    - Be thorough in your search but efficient in your actions
    - Do not enter any personal information or payment details
    - If you encounter an error or unexpected page, try to recover gracefully
    - If a search returns no results, note this clearly and suggest possible reasons

    SEARCH PROCESS DETAILS:
    1. Navigate to Kayak.com homepage
    2. Handle any initial popups or cookie consent requests
    3. Set up the flight search with the provided parameters:
       - Select correct trip type (one-way or round-trip)
       - Enter origin and destination codes
       - Set appropriate dates using the calendar interface
       - Configure any additional parameters as needed
    4. Execute the search and wait for results to load completely
    5. Analyze the results page to identify flight options
    6. Focus on finding the least expensive options while noting important details
    7. If requested, explore specific flight details by clicking for more information
    8. Note any additional fees, restrictions, or important booking information

    REPORTING STANDARDS:
    Provide a comprehensive report that includes:
    1. Search Parameters Summary:
       - Origin and destination airports
       - Dates of travel
       - Trip type and any other search criteria
    
    2. Best Flight Options:
       - Airline(s) and flight numbers if available
       - Departure and arrival times
       - Total duration
       - Number of stops/layovers and their locations
       - Price breakdown (base fare, taxes, fees)
       - Baggage allowance information if available
    
    3. Additional Information:
       - Any notable restrictions or policies
       - Comparison with other options if relevant
       - Booking process observations
    
    4. Format your report in a clear, structured way that prioritizes the most important information

    HANDLING CHALLENGES:
    - If the website layout changes, adapt your approach accordingly
    - If search results are limited or unavailable, provide clear explanation
    - If you encounter technical difficulties, describe the issue and attempt reasonable workarounds
    - If the requested dates are unavailable, note this and check nearby dates if possible

    Remember to be precise, thorough, and focus only on the flight booking task. Your goal is to provide the most accurate and helpful information possible about available flight options.
    """
    try:
        # Create and run the agent with browser configuration
        agent = Agent(
            task=task_prompt,
            llm=llm,
            browser=browser,
            extend_system_message=extended_system_message,
            controller=controller  # Pass the controller with custom actions
        )
        
        result = await agent.run()
        return {
            "status": "success",
            "details": result,
            "search_parameters": {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date if round_trip else None,
                "trip_type": trip_type
            }
        }
            
    except Exception as e:
        print(f"Error during Kayak flight search: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

async def main():
    try:
        # Display welcome message
        print("\n" + "="*70)
        print("  This AI Agent will help you find cheap flights on Kayak.com")
        print("="*70 + "\n")
        
        # Get user input for origin and destination
        origin = input("Enter origin airport code (e.g., SFO): ").strip().upper()
        destination = input("Enter destination airport code (e.g., JFK): ").strip().upper()
        
        # Ask if round trip
        round_trip_input = input("Is this a round trip? (y/n): ").strip().lower()
        round_trip = round_trip_input.startswith('y')
        
        # Get departure date in MM/DD format
        while True:
            departure_input = input("Enter departure date (MM/DD): ").strip()
            try:
                # Parse MM/DD format and convert to YYYY-MM-DD
                if '/' not in departure_input:
                    print("Invalid format. Please use MM/DD format (e.g., 05/15).")
                    continue
                    
                month, day = map(int, departure_input.split('/'))
                current_year = datetime.now().year
                
                # Use next year if the date has already passed this year
                target_date = datetime(current_year, month, day)
                if target_date < datetime.now():
                    current_year += 1
                
                departure_date = f"{current_year}-{month:02d}-{day:02d}"
                # Validate the date is valid
                datetime.strptime(departure_date, "%Y-%m-%d")
                break
            except ValueError:
                print("Invalid date. Please enter a valid date in MM/DD format (e.g., 05/15).")
        
        # Get return date if round trip
        return_date = None
        if round_trip:
            while True:
                return_input = input("Enter return date (MM/DD): ").strip()
                try:
                    # Parse MM/DD format and convert to YYYY-MM-DD
                    if '/' not in return_input:
                        print("Invalid format. Please use MM/DD format (e.g., 05/22).")
                        continue
                        
                    month, day = map(int, return_input.split('/'))
                    
                    # Use same year as departure date by default
                    departure_year = int(departure_date.split('-')[0])
                    return_date = f"{departure_year}-{month:02d}-{day:02d}"
                    
                    # Validate the date is valid
                    return_datetime = datetime.strptime(return_date, "%Y-%m-%d")
                    departure_datetime = datetime.strptime(departure_date, "%Y-%m-%d")
                    
                    # If return date is before departure date, try next year
                    if return_datetime < departure_datetime:
                        return_date = f"{departure_year + 1}-{month:02d}-{day:02d}"
                        return_datetime = datetime.strptime(return_date, "%Y-%m-%d")
                        
                        # Double check it's now after departure
                        if return_datetime <= departure_datetime:
                            print("Return date must be after departure date.")
                            continue
                    
                    break
                except ValueError:
                    print("Invalid date. Please enter a valid date in MM/DD format (e.g., 05/22).")
        
        # Run the Kayak flight search
        print(f"Starting Kayak flight search from {origin} to {destination}...")
        
        # Format dates for display
        departure_display = datetime.strptime(departure_date, "%Y-%m-%d").strftime("%B %d, %Y")
        return_display = datetime.strptime(return_date, "%Y-%m-%d").strftime("%B %d, %Y") if return_date else "N/A"
        
        print(f"Departure date: {departure_display}")
        if round_trip:
            print(f"Return date: {return_display}")
        
        search_results = await book_flight(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            round_trip=round_trip
        )
        
        # Save search results
        results_file = "kayak_search_results.json"
        with open(results_file, 'w') as f:
            json.dump(search_results, f, indent=2)
        
        # Print results
        if search_results["status"] == "success":
            print("Flight search completed successfully!")
            print(f"Search parameters: {search_results['search_parameters']}")
            print(f"Results saved to {results_file}")
        else:
            print(f"Flight search failed: {search_results['message']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
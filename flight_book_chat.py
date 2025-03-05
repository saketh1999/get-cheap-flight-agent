import asyncio
import json
import os
import sys
import time
import threading
from typing import Dict, Any, Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field
from book import book_flight  # Import the book_flight function from your book.py
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please add it to your .env file.")

# Initialize the Gemini LLM
llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-exp',
    api_key=GEMINI_API_KEY
)

# Define function schema for flight booking
class FlightBookingArgs(BaseModel):
    origin: str = Field(..., description="Origin airport code (e.g., SFO)")
    destination: str = Field(..., description="Destination airport code (e.g., JFK)")
    departure_date: str = Field(..., description="Departure date in MM/DD format (e.g., 05/15)")
    return_date: Optional[str] = Field(None, description="Return date in MM/DD format (e.g., 05/22), leave empty for one-way")

# Function to convert MM/DD to YYYY-MM-DD
def convert_date_format(date_str: str) -> str:
    """Convert MM/DD format to YYYY-MM-DD format."""
    if not date_str:
        return None
        
    from datetime import datetime
    
    month, day = map(int, date_str.split('/'))
    current_year = datetime.now().year
    
    # Use next year if the date has already passed this year
    target_date = datetime(current_year, month, day)
    if target_date < datetime.now():
        current_year += 1
    
    return f"{current_year}-{month:02d}-{day:02d}"

# Define the function that will be called by the LLM
async def search_flights(origin: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for flights on Kayak.com
    
    Args:
        origin: Origin airport code (e.g., SFO)
        destination: Destination airport code (e.g., JFK)
        departure_date: Departure date in MM/DD format
        return_date: Return date in MM/DD format (None for one-way)
    """
    # Convert dates to YYYY-MM-DD format
    departure_date_formatted = convert_date_format(departure_date)
    return_date_formatted = convert_date_format(return_date) if return_date else None
    
    # Determine if this is a round trip
    round_trip = return_date is not None
    
    # Call the book_flight function
    result = await book_flight(
        origin=origin,
        destination=destination,
        departure_date=departure_date_formatted,
        return_date=return_date_formatted,
        round_trip=round_trip
    )
    
    return result

# Define the chatbot class
class FlightBookingChatbot:
    def __init__(self):
        self.messages = [
            SystemMessage(content="""
            You are a helpful flight booking assistant powered by . You can help users find the cheapest flights 
            between destinations and answer general travel-related questions. Your primary function is to assist with 
            flight searches, but you can also provide travel tips and information.
            
            When a user asks about finding flights:
            1. Extract the origin, destination, and dates from their query
            2. If any information is missing, politely ask for it
            3. Convert city names to airport codes when needed
            4. Use the search_flights function to find flight options
            
            For airport codes, if the user provides a city name instead of an airport code, 
            use the primary airport code for that city (e.g., "New York" → "JFK", "San Francisco" → "SFO").
            
            Common airport codes:
            - New York: JFK or LGA
            - Los Angeles: LAX
            - Chicago: ORD
            - San Francisco: SFO
            - Miami: MIA
            - Dallas: DFW
            - Atlanta: ATL
            - Boston: BOS
            - Seattle: SEA
            - Denver: DEN
            - Las Vegas: LAS
            - London: LHR
            - Paris: CDG
            - Tokyo: NRT or HND
            - Sydney: SYD
            
            When analyzing flight search results:
            1. Extract the cheapest flight option (airline, price, times)
            2. Identify any layovers or connections
            3. Calculate total travel time if available
            4. Note any additional fees or restrictions
            5. Provide a recommendation based on price and convenience
            
            For general travel questions:
            - Provide helpful, accurate information
            - If you don't know something, admit it rather than making up information
            - Suggest related flight searches when appropriate
            
            For questions about using the assistant:
            - Explain that you can search for flights between destinations
            - Mention that users should provide origin, destination, and dates
            - Give examples of how to phrase flight search requests
            
            Always maintain a helpful, conversational tone and focus on providing accurate, 
            actionable information. Format your responses in a clear, organized way that's 
            easy for travelers to understand.
            
            If a search fails, politely ask the user to try again with different parameters.
            """)
        ]
        
        # Define the available functions
        self.functions = [
            {
                "name": "search_flights",
                "description": "Search for flights on Kayak.com",
                "parameters": FlightBookingArgs.schema()
            }
        ]
    
    async def process_message(self, user_input: str) -> str:
        """Process a user message and return a response."""
        # Add user message to history
        self.messages.append(HumanMessage(content=user_input))
        
        # Get response from LLM with function calling
        response = await llm.ainvoke(
            self.messages,
            functions=self.functions
        )
        
        # Check if function call is requested
        if hasattr(response, 'additional_kwargs') and 'function_call' in response.additional_kwargs:
            function_call = response.additional_kwargs['function_call']
            
            if function_call['name'] == 'search_flights':
                # Extract arguments
                args = json.loads(function_call['arguments'])
                
                # Add AI message explaining what it's doing
                processing_message = f"I'll search for flights from {args['origin']} to {args['destination']} for you. This might take a minute..."
                self.messages.append(AIMessage(content=processing_message))
                
                # Call the function
                flight_results = await search_flights(
                    origin=args['origin'],
                    destination=args['destination'],
                    departure_date=args['departure_date'],
                    return_date=args.get('return_date')
                )
                
                # Have Gemini analyze the results
                if flight_results['status'] == 'success':
                    # Create a prompt for Gemini to analyze the results
                    analysis_prompt = f"""
                    Analyze these flight search results and provide a concise summary:
                    
                    Search Parameters:
                    - Origin: {flight_results['search_parameters']['origin']}
                    - Destination: {flight_results['search_parameters']['destination']}
                    - Departure Date: {flight_results['search_parameters']['departure_date']}
                    - Return Date: {flight_results['search_parameters'].get('return_date', 'N/A')}
                    - Trip Type: {flight_results['search_parameters']['trip_type']}
                    
                    Raw Flight Details:
                    {flight_results['details']}
                    
                    Please extract and summarize:
                    1. The cheapest flight option (airline, price, times)
                    2. Any layovers or connections
                    3. Total travel time if available
                    4. Any notable fees or restrictions
                    5. Your recommendation based on price and convenience
                    
                    Format your response in a clear, organized way that's easy for a traveler to understand.
                    """
                    
                    # Add the analysis prompt to messages
                    self.messages.append(HumanMessage(content=analysis_prompt))
                    
                    # Get Gemini's analysis
                    analysis_response = await llm.ainvoke(self.messages)
                    
                    # Add the analysis to messages
                    self.messages.append(analysis_response)
                    return analysis_response.content
                else:
                    # If search failed, ask user to try again
                    error_message = f"I couldn't complete the flight search. Error: {flight_results['message']}. Please try again with different search parameters."
                    self.messages.append(AIMessage(content=error_message))
                    return error_message
        
        # If no function call, just return the response
        self.messages.append(response)
        return response.content

async def main():
    chatbot = FlightBookingChatbot()
    
    # Terminal colors
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"
    
    # Clear screen (works on most terminals)
    print("\033c", end="")
    
    # Display welcome banner
    print(f"\n{BOLD}{BLUE}{'='*70}{END}")
    print(f"{BOLD}{BLUE}║{' '*68}║{END}")
    print(f"{BOLD}{BLUE}║{' '*15}Flight Booking Assistant - powered by Gemini{' '*15}║{END}")
    print(f"{BOLD}{BLUE}║{' '*68}║{END}")
    print(f"{BOLD}{BLUE}{'='*70}{END}\n")
    
    print(f"{YELLOW}Welcome to your AI Flight Assistant!{END}")
    print(f"{YELLOW}I can help you find the cheapest flights between any destinations.{END}")
    print(f"{YELLOW}Just tell me where you want to go and when.{END}")
    print(f"{YELLOW}Type {BOLD}'exit'{END} {YELLOW}to quit the assistant.{END}\n")
    
    while True:
        # User input with prompt
        user_input = input(f"{BOLD}{GREEN}User:{END} ")
        
        # Check for exit command
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print(f"\n{BOLD}{BLUE}AI:{END} Goodbye! Have a great trip! ✈️\n")
            break
        
        # Show thinking indicator
        print(f"\n{BOLD}{BLUE}AI:{END} ", end="")
        
        # Process the message
        try:
            # Show a "thinking" animation
            thinking = True
            
            def animate():
                chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
                i = 0
                while thinking:
                    sys.stdout.write(f"\r{BOLD}{BLUE}AI:{END} Thinking {chars[i % len(chars)]}")
                    sys.stdout.flush()
                    time.sleep(0.1)
                    i += 1
            
            # Start the animation in a separate thread
            t = threading.Thread(target=animate)
            t.start()
            
            # Process the message
            response = await chatbot.process_message(user_input)
            
            # Stop the animation
            thinking = False
            t.join()
            
            # Clear the thinking line
            sys.stdout.write("\r" + " " * 50 + "\r")
            sys.stdout.flush()
            
            # Format and print the response
            print(f"{BOLD}{BLUE}AI:{END} {response}\n")
            
        except Exception as e:
            print(f"\n{RED}Error: {str(e)}{END}\n")
            print(f"{BOLD}{BLUE}AI:{END} Sorry, I encountered an error. Please try again.\n")

if __name__ == "__main__":
    asyncio.run(main())
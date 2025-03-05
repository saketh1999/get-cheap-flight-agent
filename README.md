
# Flight Booking AI Assistant

This project provides an AI-powered flight booking assistant that helps users find the cheapest flights between destinations using Kayak.com. The assistant uses Gemini AI to understand natural language queries and automates the process of searching for flights.

## Demo : [Link](https://drive.google.com/file/d/1rtn5mCHH7sBHaEeWiFTZgH0-dcWRHUXd/view?usp=sharing)

## Disclaimer

**IMPORTANT: This project is for educational and experimental purposes only.**

- This tool is not affiliated with, endorsed by, or connected to Kayak.com in any way
- The use of automated tools to scrape or interact with websites may violate terms of service. This is only for educational/demo purposes.
- No actual bookings or financial transactions are made through this tool
- Flight information may be inaccurate, outdated, or incomplete
- Use at your own risk and responsibility
- Always verify any flight information directly with airlines or official travel agencies before making travel plans
- The creators of this tool are not responsible for any consequences resulting from its use


## Features

- **Natural Language Interface**: Ask for flights in plain English
- **Automated Web Search**: Uses AI to navigate Kayak.com and find flight options
- **Price Comparison**: Identifies the cheapest flight options
- **Detailed Reports**: Provides comprehensive information about flight options
- **Interactive Terminal UI**: User-friendly colored interface with loading animations

## Components

The project consists of two main Python scripts:

1. **book.py**: Core functionality for automating flight searches on Kayak.com
2. **flight_book_chat.py**: Chatbot interface that uses Gemini AI to process user queries

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- Chrome or Chromium browser installed

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/flight-booking-assistant.git
   cd flight-booking-assistant
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project directory with your Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Usage

### Option 1: Using the Chatbot Interface

Run the chatbot interface for a conversational experience:

bash
python book.py


Follow the prompts to:
1. Enter origin airport code
2. Enter destination airport code
3. Specify if it's a round trip
4. Enter departure date (MM/DD format)
5. Enter return date if applicable (MM/DD format)

## How It Works

1. **User Input Processing**:
   - The chatbot uses Gemini AI to understand flight search requests
   - It extracts origin, destination, and dates from natural language
   - If information is missing, it asks follow-up questions

2. **Flight Search Automation**:
   - The system launches a browser and navigates to Kayak.com
   - It fills in search parameters and handles popups
   - It waits for search results to load

3. **Result Analysis**:
   - The AI analyzes the search results page
   - It identifies the cheapest flight options
   - It extracts details like airline, times, price, and layovers

4. **Report Generation**:
   - The system generates a structured report of flight options
   - Gemini AI summarizes the findings in a user-friendly format
   - Results are presented in the terminal and saved to a JSON file

## Requirements

The following Python packages are required:
- langchain-google-genai
- langchain-core
- pydantic
- python-dotenv
- browser-use (custom package for browser automation)
- selenium
- webdriver-manager

## Limitations

- The assistant can only search for flights on Kayak.com
- Flight availability and prices are subject to change
- The browser automation may break if Kayak.com changes its website structure
- The assistant does not book flights or handle payments

## Troubleshooting

- **API Key Issues**: Ensure your Gemini API key is correctly set in the `.env` file
- **Browser Issues**: Make sure Chrome/Chromium is installed and up to date
- **Search Failures**: Try different dates or airports if a search fails
- **Display Issues**: If terminal colors don't display correctly, try a different terminal

## Future Improvements

- Support for more travel websites beyond Kayak.com
- Advanced filtering options (airline preferences, time ranges, etc.)
- Price tracking and alerts for fare drops
- Integration with email for sending flight details
- Mobile app interface

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for natural language processing
- Kayak.com for flight data
- LangChain for AI framework components
- Browser_use for Framework

---

For questions or support, please open an issue on the GitHub repository.

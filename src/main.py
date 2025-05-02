"""
Main entry point for EmoJourney application.
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to the Python path to enable relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui_stream import UIStream, setup_page
from src.journey_manager import JourneyManager

def main():
    """Main application entry point."""
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        import streamlit as st
        st.error("""
        OpenAI API key is required to run this application.
        
        Please create a .env file in the project root with:
        OPENAI_API_KEY=your_api_key_here
        """)
        return
    
    # Set up the page
    setup_page()
    
    # Create journey manager
    journey_manager = JourneyManager(api_key=api_key)
    
    # Create and run UI
    ui = UIStream(journey_manager=journey_manager)
    ui.run()

if __name__ == "__main__":
    main() 
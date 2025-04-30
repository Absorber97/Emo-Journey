"""
UI Stream module for EmoJourney.
Implements Streamlit UI with chat, emotion badges, and reset functionality.
"""
import time
import streamlit as st
import os
import logging
from typing import Dict, List, Any, Optional, Callable

from journey_manager import JourneyManager
from emotion_api import EmotionAPI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("emojourney.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EmoJourney")

class UIStream:
    """Streamlit UI handler with streaming capabilities."""
    
    def __init__(self, journey_manager: Optional[JourneyManager] = None):
        """
        Initialize the UI Stream.
        
        Args:
            journey_manager: JourneyManager instance or None to create a new one
        """
        logger.info("Initializing UIStream")
        # Initialize session state if not already done
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if "journey_manager" not in st.session_state:
            api_key = os.getenv("OPENAI_API_KEY")
            st.session_state.journey_manager = journey_manager or JourneyManager(api_key=api_key)
        
        if "current_emotion" not in st.session_state:
            st.session_state.current_emotion = None
        
        if "goal_emotion" not in st.session_state:
            st.session_state.goal_emotion = None
        
        if "goal_options" not in st.session_state:
            st.session_state.goal_options = []
        
        if "suggestions" not in st.session_state:
            st.session_state.suggestions = []
        
        if "show_goal_buttons" not in st.session_state:
            st.session_state.show_goal_buttons = False
            
        self.journey_manager = st.session_state.journey_manager
    
    def reset_chat(self):
        """Reset the chat and all state."""
        logger.info("Resetting chat")
        st.session_state.messages = []
        st.session_state.current_emotion = None
        st.session_state.goal_emotion = None
        st.session_state.goal_options = []
        st.session_state.suggestions = []
        st.session_state.show_goal_buttons = False
        self.journey_manager.reset()
        
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! How are you feeling today?",
            "is_emotion": False
        })
    
    def format_emotion(self, emotion: str, emoji: str, color: str) -> str:
        """
        Format an emotion with emoji and colored badge.
        
        Args:
            emotion: Emotion name
            emoji: Emoji representing the emotion
            color: Color hex code
            
        Returns:
            Formatted HTML for the emotion badge
        """
        return f"""
        <div style="
            display: inline-block;
            padding: 5px 10px;
            margin: 5px 0;
            background-color: {color};
            color: white;
            border-radius: 15px;
            font-weight: bold;
        ">
            {emoji} {emotion.capitalize()}
        </div>
        """
    
    def select_goal(self, index: int):
        """
        Handle goal selection.
        
        Args:
            index: Index of selected goal option
        """
        if 0 <= index < len(st.session_state.goal_options):
            logger.info(f"User selected goal: {st.session_state.goal_options[index]['emotion']}")
            selected_goal = st.session_state.goal_options[index]['emotion']
            self.journey_manager.set_goal(selected_goal)
            st.session_state.goal_emotion = selected_goal
            st.session_state.show_goal_buttons = False
            
            # Add selected goal message
            emoji = st.session_state.goal_options[index]['emoji']
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"You've chosen to work towards **{selected_goal}** {emoji}. Let me help you with that.",
                "is_emotion": False
            })
    
    def format_suggestion(self, suggestion: Dict[str, Any]) -> str:
        """
        Format a suggestion with title, description, and percentage.
        
        Args:
            suggestion: Suggestion dictionary
            
        Returns:
            Formatted HTML for the suggestion
        """
        return f"""
        <div style="
            padding: 10px 15px;
            margin: 10px 0;
            background-color: #f0f0f0;
            border-radius: 10px;
            border-left: 5px solid #4CAF50;
        ">
            <h4 style="margin: 0 0 5px 0;">{suggestion['title']} ({suggestion['closer_percentage']}% closer)</h4>
            <p style="margin: 0;">{suggestion['description']}</p>
        </div>
        """
    
    def render_chat_ui(self):
        """Render the main chat UI with messages and input."""
        # Title with emoji
        st.title("🧠 EmoJourney")
        st.write("An emotional planner chat to help you reach your desired emotional state.")
        
        # Reset button
        if st.button("Reset Chat"):
            logger.info("User clicked Reset Chat button")
            self.reset_chat()
            st.rerun()
        
        # Initialize chat if empty
        if not st.session_state.messages:
            self.reset_chat()
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message.get("is_emotion", False):
                    # Render emotion badge
                    st.markdown(message["content"], unsafe_allow_html=True)
                else:
                    # Render regular message
                    st.markdown(message["content"])
        
        # Display goal buttons if needed
        if st.session_state.show_goal_buttons and st.session_state.goal_options:
            with st.chat_message("assistant"):
                st.markdown("**What emotion would you like to work towards?**")
                
                # Create buttons for each goal option
                for i, option in enumerate(st.session_state.goal_options):
                    emotion = option["emotion"]
                    emoji = option["emoji"]
                    distance = option["distance"]
                    color = option["color"]
                    
                    # Use button with custom styling
                    button_label = f"{emoji} {emotion.capitalize()} ({distance} hops)"
                    button_style = f"background-color: {color}; color: white;"
                    
                    if st.button(button_label, key=f"goal_{i}", use_container_width=True):
                        self.select_goal(i)
                        st.rerun()
        
        # Chat input
        if prompt := st.chat_input("How are you feeling?"):
            logger.info(f"User input: {prompt[:50]}...")
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message in UI
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Process the message
            self.process_user_message(prompt)
    
    def process_user_message(self, message: str):
        """
        Process a user message, updating emotions and generating responses.
        
        Args:
            message: User's message
        """
        logger.info("Processing user message")
        # Create a placeholder for streaming response
        with st.chat_message("assistant"):
            placeholder = st.empty()
            
            # Simulate typing effect
            display_text = "Analyzing your emotions..."
            placeholder.markdown(display_text)
            
            # Get emotion classification
            emotion_data = self.journey_manager.classify_user_message(message)
            emotion = emotion_data["emotion"]
            emoji = emotion_data["emoji"]
            color = emotion_data["color"]
            
            logger.info(f"Classified emotion: {emotion}")
            
            # Update session state
            st.session_state.current_emotion = emotion
            
            # Format the emotion badge
            emotion_badge = self.format_emotion(emotion, emoji, color)
            
            # Acknowledge the user's feelings with empathy
            acknowledgement = self._get_acknowledgement(emotion, message)
            
            # Add emotion message to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"{acknowledgement} {emotion_badge}",
                "is_emotion": True
            })
            
            # Display the emotion with acknowledgement
            placeholder.markdown(f"{acknowledgement} {emotion_badge}", unsafe_allow_html=True)
            
            # If no goal is set, prepare to show goal options
            if not st.session_state.goal_emotion:
                time.sleep(0.5)  # Brief pause for better UX
                
                # Get goal options
                goal_options = self.journey_manager.get_goal_options(n=2)
                st.session_state.goal_options = goal_options
                st.session_state.show_goal_buttons = True
                
                # Force rerun to show the buttons
                st.rerun()
            
            # If goal is set, show suggestions
            elif st.session_state.goal_emotion:
                time.sleep(0.7)  # Brief pause for better UX
                
                # Get progress
                progress = self.journey_manager.get_progress()
                
                # Get suggestions
                suggestions = self.journey_manager.generate_suggestions()
                st.session_state.suggestions = suggestions
                
                # Format suggestions
                suggestions_html = f"""
                <div style="margin-top: 15px;">
                    <p><strong>Working towards {st.session_state.goal_emotion} 
                    ({progress['progress']}% progress)</strong></p>
                    <p>Here are some suggestions:</p>
                """
                
                for suggestion in suggestions:
                    suggestions_html += self.format_suggestion(suggestion)
                
                suggestions_html += "</div>"
                
                # Add suggestions to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": suggestions_html,
                    "is_suggestions": True
                })
                
                # Display suggestions
                placeholder.markdown(suggestions_html, unsafe_allow_html=True)
    
    def _get_acknowledgement(self, emotion: str, message: str) -> str:
        """
        Generate an empathetic acknowledgement based on the detected emotion.
        
        Args:
            emotion: Detected emotion
            message: User's message
            
        Returns:
            Acknowledgement text
        """
        acknowledgements = {
            "joy": "I'm glad to hear you're feeling happy!",
            "sadness": "I understand that you're feeling down right now.",
            "anger": "I can see that you're feeling frustrated.",
            "fear": "It sounds like you're feeling anxious or worried.",
            "disgust": "I notice you're feeling uncomfortable with this situation.",
            "surprise": "That seems to have caught you off guard!",
            "trust": "I appreciate your openness and trust.",
            "anticipation": "I can see you're looking forward to what comes next."
        }
        
        return acknowledgements.get(emotion, f"I sense that you're feeling **{emotion}**.")
    
    def run(self):
        """Run the UI Stream application."""
        logger.info("Starting UI Stream application")
        self.render_chat_ui()


# Streamlit page configuration
def setup_page():
    """Configure Streamlit page settings."""
    logger.info("Setting up page configuration")
    st.set_page_config(
        page_title="EmoJourney - Emotional Planner Chat",
        page_icon="🧠",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Add custom CSS
    st.markdown("""
    <style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .stChatMessage {
        padding: 10px;
    }
    
    /* Style for reset button */
    .stButton button {
        background-color: #f44336;
        color: white;
        font-weight: bold;
    }
    
    /* Style for goal buttons */
    button[data-testid="baseButton-secondary"] {
        margin: 5px 0;
        border-radius: 15px;
        font-weight: bold;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True) 
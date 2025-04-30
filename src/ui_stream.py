"""
UI Stream module for EmoJourney.
Implements Streamlit UI with chat, emotion badges, and reset functionality.
"""
import time
import streamlit as st
import os
from typing import Dict, List, Any, Optional, Callable

from src.journey_manager import JourneyManager
from src.emotion_api import EmotionAPI

class UIStream:
    """Streamlit UI handler with streaming capabilities."""
    
    def __init__(self, journey_manager: Optional[JourneyManager] = None):
        """
        Initialize the UI Stream.
        
        Args:
            journey_manager: JourneyManager instance or None to create a new one
        """
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
        
        self.journey_manager = st.session_state.journey_manager
    
    def reset_chat(self):
        """Reset the chat and all state."""
        st.session_state.messages = []
        st.session_state.current_emotion = None
        st.session_state.goal_emotion = None
        st.session_state.goal_options = []
        st.session_state.suggestions = []
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
    
    def format_goal_option(self, option: Dict[str, Any]) -> str:
        """
        Format a goal option with emoji, name, and hops.
        
        Args:
            option: Goal option dictionary
            
        Returns:
            Formatted HTML for the goal option
        """
        return f"""
        <div style="
            display: inline-block;
            padding: 8px 12px;
            margin: 8px 0;
            background-color: {option['color']};
            color: white;
            border-radius: 15px;
            font-weight: bold;
            cursor: pointer;
            width: 80%;
            text-align: center;
        ">
            {option['emoji']} {option['emotion'].capitalize()} ({option['distance']} hops)
        </div>
        """
    
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
                elif message.get("is_goal_options", False):
                    # Render goal options
                    st.markdown(message["content"], unsafe_allow_html=True)
                elif message.get("is_suggestions", False):
                    # Render suggestions
                    st.markdown(message["content"], unsafe_allow_html=True)
                else:
                    # Render regular message
                    st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("How are you feeling?"):
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
            
            # Update session state
            st.session_state.current_emotion = emotion
            
            # Format the emotion badge
            emotion_badge = self.format_emotion(emotion, emoji, color)
            
            # Add emotion message to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"I sense that you're feeling **{emotion}**. {emotion_badge}",
                "is_emotion": True
            })
            
            # Display the emotion 
            placeholder.markdown(f"I sense that you're feeling **{emotion}**. {emotion_badge}", unsafe_allow_html=True)
            
            # If no goal is set, show goal options
            if not st.session_state.goal_emotion:
                time.sleep(0.5)  # Brief pause for better UX
                
                # Get goal options
                goal_options = self.journey_manager.get_goal_options(n=2)
                st.session_state.goal_options = goal_options
                
                # Format goal options
                goal_options_html = """
                <div style="margin-top: 15px;">
                    <p><strong>What emotion would you like to work towards?</strong></p>
                """
                
                for i, option in enumerate(goal_options):
                    goal_options_html += f"""
                    <div onclick="parent.postMessage({{command: 'streamlitSelectGoal', option: {i}}}, '*')" style="cursor:pointer;">
                        {self.format_goal_option(option)}
                    </div>
                    """
                
                goal_options_html += "</div>"
                
                # Add goal options to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": goal_options_html,
                    "is_goal_options": True
                })
                
                # Display goal options
                placeholder.markdown(goal_options_html, unsafe_allow_html=True)
                
                # Note: In a real implementation, we would need JavaScript to handle the goal selection
                # Since Streamlit limitations prevent direct onclick handling,
                # we would need to use two columns with buttons or other Streamlit components
            
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
    
    def run(self):
        """Run the UI Stream application."""
        self.render_chat_ui()
        
        # Note: In a real implementation, we would need to add handlers for:
        # 1. Goal selection (could use Streamlit components or alternative UI elements)
        # 2. Suggestion selection feedback
        # These are omitted here for simplicity since they require JavaScript integration


# Streamlit page configuration
def setup_page():
    """Configure Streamlit page settings."""
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
    </style>
    """, unsafe_allow_html=True) 
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

# Add a function to log state changes
def log_state(message, state_data=None):
    """Log state changes with detailed information."""
    if state_data:
        logger.info(f"{message}: {state_data}")
    else:
        logger.info(message)

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
            
        if "implemented_suggestions" not in st.session_state:
            st.session_state.implemented_suggestions = set()
        
        if "chat_disabled" not in st.session_state:
            st.session_state.chat_disabled = False
        
        self.journey_manager = st.session_state.journey_manager
    
    def reset_chat(self):
        """Reset the chat and all state."""
        log_state("Resetting chat and clearing all state")
        st.session_state.messages = []
        st.session_state.current_emotion = None
        st.session_state.goal_emotion = None
        st.session_state.goal_options = []
        st.session_state.suggestions = []
        st.session_state.show_goal_buttons = False
        st.session_state.implemented_suggestions = set()
        st.session_state.chat_disabled = False
        self.journey_manager.reset()
        
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! How are you feeling today?",
            "is_emotion": False
        })
        log_state("Added welcome message to reset chat")
    
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
            selected_goal = st.session_state.goal_options[index]['emotion']
            emoji = st.session_state.goal_options[index]['emoji']
            
            log_state(f"User selected goal", {
                "emotion": selected_goal,
                "emoji": emoji,
                "index": index
            })
            
            self.journey_manager.set_goal(selected_goal)
            st.session_state.goal_emotion = selected_goal
            st.session_state.show_goal_buttons = False
            
            # Ensure chat remains disabled during goal journey
            st.session_state.chat_disabled = True
            
            # Add selected goal message
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"You've chosen to work towards **{selected_goal}** {emoji}. I'll guide you step by step with suggestions to help you reach this emotional state.",
                "is_emotion": False
            })
            
            # Generate suggestions immediately after goal selection
            log_state("Generating suggestions after goal selection")
            time.sleep(0.7)  # Brief pause for better UX
            
            try:
                # Get progress
                progress = self.journey_manager.get_progress()
                log_state("Journey progress", progress)
                
                # Get suggestions
                suggestions = self.journey_manager.generate_suggestions()
                log_state(f"Generated {len(suggestions)} suggestions")
                st.session_state.suggestions = suggestions
                
                # Format suggestions
                suggestions_html = self._format_suggestions_html(suggestions, progress)
                
                # Add suggestions to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": suggestions_html,
                    "is_suggestions": True
                })
                
                log_state("Added suggestions to chat history")
            except Exception as e:
                logger.error(f"Error generating suggestions: {str(e)}")
                # Add fallback message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"I'm having trouble generating suggestions right now. Let's try again later.",
                    "is_emotion": False
                })
    
    def format_suggestion(self, suggestion: Dict[str, Any], index: int, progress: Dict[str, Any]) -> str:
        """
        Format a suggestion with title, description, and percentage.
        
        Args:
            suggestion: Suggestion dictionary
            index: Index of the suggestion for button identification
            progress: Progress data from journey manager
            
        Returns:
            Formatted HTML for the suggestion
        """
        # Generate a unique ID for this suggestion
        suggestion_id = f"suggestion_{index}_{hash(suggestion['title'])}"[:20]
        
        # Use suggestion specific progress percentage
        closer_percentage = suggestion['closer_percentage']
        
        # Choose different emojis based on closer_percentage
        if closer_percentage >= 70:
            progress_emoji = "🚀"  # Rocket for big jumps
        elif closer_percentage >= 50:
            progress_emoji = "✨"  # Sparkles for medium progress
        elif closer_percentage >= 30:
            progress_emoji = "🔍"  # Magnifying glass for smaller progress
        else:
            progress_emoji = "🌱"  # Seedling for minimal progress
        
        # Different color schemes based on closer_percentage
        if closer_percentage >= 70:
            color = "#2E7D32"  # Dark green for big progress
        elif closer_percentage >= 50:
            color = "#5C6BC0"  # Indigo for medium progress
        elif closer_percentage >= 30:
            color = "#FF9800"  # Orange for smaller progress
        else:
            color = "#9E9E9E"  # Grey for minimal progress
        
        # Check if this suggestion has been implemented
        is_implemented = suggestion_id in st.session_state.implemented_suggestions
        
        # Create different styling based on implementation status
        if is_implemented:
            background_color = "#f0f8ff"  # Light blue background for implemented
            border_style = "border-left: 8px solid #90caf9; opacity: 0.7;"
            implemented_badge = '<span style="background-color: #90caf9; color: #fff; padding: 3px 8px; border-radius: 10px; font-size: 0.8em; margin-left: 10px;">✓ Chosen</span>'
        else:
            background_color = "#f8f9fa"  # Default background
            border_style = f"border-left: 8px solid {color};"
            implemented_badge = ""
        
        return f"""
        <div id="{suggestion_id}_container" style="
            padding: 15px;
            margin: 15px 0;
            background-color: {background_color};
            border-radius: 12px;
            {border_style}
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            position: relative;
            transition: all 0.3s ease;
        ">
            <h4 style="margin: 0 0 8px 0; color: {color};">
                {progress_emoji} {suggestion['title']} {implemented_badge}
                <span style="
                    background-color: {color};
                    color: #ffffff;
                    padding: 3px 8px;
                    border-radius: 10px;
                    font-size: 0.9em;
                    float: right;
                    font-weight: bold;
                ">{closer_percentage}% closer</span>
            </h4>
            <p style="margin: 0; font-size: 1.05em; color: #333333;">{suggestion['description']}</p>
        </div>
        """
    
    def _format_suggestions_html(self, suggestions, progress):
        """
        Format suggestions as HTML.
        
        Args:
            suggestions: List of suggestion dictionaries
            progress: Progress data dictionary
            
        Returns:
            Formatted HTML for suggestions
        """
        # Get goal emotion data
        goal_emotion = st.session_state.goal_emotion
        goal_emoji = self.journey_manager.emotion_api.EMOTIONS.get(goal_emotion, "❓")
        goal_color = self.journey_manager.emotion_api.EMOTION_COLORS.get(goal_emotion, "#808080")
        
        suggestions_html = f"""
        <div style="
            margin: 15px 0;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 15px;
            border: 1px solid {goal_color};
        ">
            <div style="
                padding: 8px 12px;
                margin-bottom: 10px;
                background-color: {goal_color};
                color: white;
                border-radius: 8px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: space-between;
            ">
                <span>Working towards {goal_emoji} <strong>{goal_emotion.capitalize()}</strong></span>
                <span style="
                    background-color: white;
                    color: {goal_color};
                    padding: 3px 8px;
                    border-radius: 10px;
                    font-size: 0.9em;
                    font-weight: bold;
                ">{progress['progress']}% progress</span>
            </div>
        """
        
        if suggestions:
            suggestions_html += "<p>Here are some suggestions:</p>"
            for i, suggestion in enumerate(suggestions):
                suggestions_html += self.format_suggestion(suggestion, i, progress)
        else:
            # Fallback suggestions with new styling
            suggestions_html += """
            <p>I'm working on personalized suggestions for you. 
            In the meantime, try to think about what might help you move toward your goal emotion.</p>
            """
            
            # Create a fallback suggestion with the same styling as regular suggestions
            fallback_suggestion = {
                'title': 'Reflect on your goal',
                'description': 'Take a moment to think about times when you\'ve felt your goal emotion before.',
                'closer_percentage': 25
            }
            
            suggestions_html += self.format_suggestion(fallback_suggestion, 0, progress)
        
        suggestions_html += "</div>"
        return suggestions_html
    
    def handle_suggestion_choice(self, suggestion_index):
        """
        Handle when a user chooses a suggestion.
        
        Args:
            suggestion_index: Index of the suggestion chosen
        """
        if 0 <= suggestion_index < len(st.session_state.suggestions):
            suggestion = st.session_state.suggestions[suggestion_index]
            suggestion_id = f"suggestion_{suggestion_index}_{hash(suggestion['title'])}"[:20]
            
            logger.info(f"User chose suggestion: {suggestion['title']}")
            
            # Mark this suggestion as implemented
            st.session_state.implemented_suggestions.add(suggestion_id)
            
            # Update progress based on suggestion's closer_percentage
            progress_before = self.journey_manager.get_progress()
            
            # Apply the suggestion's progress boost - this is simulated since we don't have a real simulation
            # In a real emotional journey, we would update the journey manager with actual progress
            # For now, we'll check if the suggestion gets us to the goal
            closer_percentage = suggestion.get('closer_percentage', 0)
            goal_reached = closer_percentage >= 95 or progress_before['progress'] + 30 >= 100
            
            # If goal is reached, notify journey manager
            if goal_reached:
                logger.info(f"Goal reached through suggestion implementation: {st.session_state.goal_emotion}")
                
                # Set current emotion to goal emotion to trigger congratulations
                self.journey_manager.current_emotion = self.journey_manager.goal_emotion
                
                # Add a response acknowledging the achievement
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Great choice! You've successfully reached your goal of feeling {st.session_state.goal_emotion}!",
                    "is_emotion": False
                })
                
                # Re-enable chat
                st.session_state.chat_disabled = False
            else:
                # Add a response acknowledging the choice and encouraging next step
                progress_after = self.journey_manager.get_progress()
                
                # Add response message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Good choice! You're making progress toward feeling {st.session_state.goal_emotion}. Let's continue with another suggestion.",
                    "is_emotion": False
                })
                
                # Get new suggestions
                time.sleep(0.7)  # Brief pause for better UX
                
                # Get progress
                progress = self.journey_manager.get_progress()
                
                # Get suggestions
                suggestions = self.journey_manager.generate_suggestions()
                st.session_state.suggestions = suggestions
                
                # Format suggestions
                suggestions_html = self._format_suggestions_html(suggestions, progress)
                
                # Add suggestions to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": suggestions_html,
                    "is_suggestions": True
                })
    
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
                elif message.get("is_suggestions", False):
                    # Render suggestions with HTML
                    st.markdown(message["content"], unsafe_allow_html=True)
                    
                    # Add buttons for suggestions
                    if "suggestions" in st.session_state and st.session_state.suggestions:
                        # Create a container for the buttons
                        cols = st.columns(2)
                        with cols[0]:
                            if st.button("Choose 1", key="choose_suggestion_1", help="Choose the first suggestion", type="primary"):
                                self.handle_suggestion_choice(0)
                                st.rerun()
                        with cols[1]:
                            if len(st.session_state.suggestions) > 1:
                                if st.button("Choose 2", key="choose_suggestion_2", help="Choose the second suggestion", type="primary"):
                                    self.handle_suggestion_choice(1)
                                    st.rerun()
                else:
                    # Render regular message
                    st.markdown(message["content"])
        
        # Display goal buttons if needed
        if st.session_state.show_goal_buttons and st.session_state.goal_options:
            with st.chat_message("assistant"):
                st.markdown("<h4 style='margin-bottom: 15px;'>What emotion would you like to work towards?</h4>", unsafe_allow_html=True)
                
                # Create a columns layout for buttons
                cols = st.columns(2)
                
                # Create buttons for each goal option
                for i, option in enumerate(st.session_state.goal_options):
                    emotion = option["emotion"]
                    emoji = option["emoji"]
                    distance = option["distance"]
                    color = option["color"]
                    
                    # Custom button styling
                    with cols[i]:
                        # Use custom HTML for better styling
                        st.markdown(f"""
                        <div id="goal_button_{i}" style="
                            background-color: {color};
                            color: white;
                            padding: 15px;
                            border-radius: 15px;
                            margin: 5px 0;
                            text-align: center;
                            cursor: pointer;
                            font-weight: bold;
                            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                            transition: all 0.3s ease;
                        ">
                            <div style="font-size: 1.8em;">{emoji}</div>
                            <div>{emotion.capitalize()}</div>
                            <div style="
                                background-color: rgba(255,255,255,0.3);
                                padding: 3px 8px;
                                border-radius: 10px;
                                margin-top: 5px;
                                font-size: 0.8em;
                            ">{distance} steps away</div>
                        </div>
                        <script>
                            document.getElementById("goal_button_{i}").addEventListener("click", function() {{
                                this.style.transform = "scale(0.95)";
                                this.style.backgroundColor = "darken({color}, 10%)";
                            }});
                        </script>
                        """, unsafe_allow_html=True)
                        
                        # Hidden button for actual functionality
                        if st.button(f"Select {emotion}", key=f"goal_{i}", use_container_width=True):
                            self.select_goal(i)
                            st.rerun()
        
        # Display journey status message if chat is disabled
        if st.session_state.chat_disabled and st.session_state.goal_emotion:
            with st.container():
                st.info(f"Chat input is disabled while you work towards {st.session_state.goal_emotion}. Choose a suggestion to continue your emotional journey.")
        
        # Chat input - conditionally enabled
        if st.session_state.chat_disabled:
            # Display disabled chat input
            st.text_input("How are you feeling?", 
                         value="Chat disabled during emotional journey", 
                         disabled=True,
                         key="disabled_chat_input")
        else:
            # Normal chat input functionality
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
        log_state("Processing user message", {"message_preview": message[:50] + "..." if len(message) > 50 else message})
        
        # Create a placeholder for streaming response
        with st.chat_message("assistant"):
            placeholder = st.empty()
            
            # Simulate typing effect
            display_text = "Analyzing your emotions..."
            placeholder.markdown(display_text)
            
            try:
                # Get emotion classification
                emotion_data = self.journey_manager.classify_user_message(message)
                emotion = emotion_data["emotion"]
                emoji = emotion_data["emoji"]
                color = emotion_data["color"]
                goal_reached = emotion_data.get("goal_reached", False)
                
                log_state(f"Classified emotion", {
                    "emotion": emotion,
                    "emoji": emoji,
                    "confidence": emotion_data.get("confidence", "N/A"),
                    "goal_reached": goal_reached
                })
                
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
                
                # Handle goal reached case
                if goal_reached and st.session_state.goal_emotion:
                    log_state(f"Goal reached: {st.session_state.goal_emotion}")
                    time.sleep(0.7)  # Brief pause for better UX
                    
                    # Format congratulations message
                    congrats_message = self._format_goal_reached_message(emotion, emoji, color)
                    
                    # Add congratulations to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": congrats_message,
                        "is_congrats": True
                    })
                    
                    # Display congratulations
                    placeholder = st.empty()
                    placeholder.markdown(congrats_message, unsafe_allow_html=True)
                    
                    # Reset goal but keep current emotion
                    st.session_state.goal_emotion = None
                    st.session_state.show_goal_buttons = True
                    
                    # Re-enable chat since goal was reached
                    st.session_state.chat_disabled = False
                    
                    # Get new goal options for next journey
                    goal_options = self.journey_manager.get_goal_options(n=2)
                    st.session_state.goal_options = goal_options
                    
                    # Force rerun to show the new goal buttons
                    st.rerun()
                
                # If no goal is set, prepare to show goal options
                elif not st.session_state.goal_emotion:
                    log_state("No goal set, showing goal options")
                    time.sleep(0.5)  # Brief pause for better UX
                    
                    # Disable chat during goal selection
                    st.session_state.chat_disabled = True
                    
                    # Show instructions for goal selection
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "I'll help you work toward a positive emotion. Please select which emotion you'd like to reach:",
                        "is_emotion": False
                    })
                    
                    # Get goal options
                    goal_options = self.journey_manager.get_goal_options(n=2)
                    log_state(f"Retrieved {len(goal_options)} goal options", 
                             {"options": [opt["emotion"] for opt in goal_options]})
                    
                    st.session_state.goal_options = goal_options
                    st.session_state.show_goal_buttons = True
                    
                    # Force rerun to show the buttons
                    st.rerun()
                
                # If goal is set, show suggestions
                elif st.session_state.goal_emotion:
                    log_state(f"Goal already set: {st.session_state.goal_emotion}, generating suggestions")
                    time.sleep(0.7)  # Brief pause for better UX
                    
                    # Get progress
                    progress = self.journey_manager.get_progress()
                    log_state("Journey progress", progress)
                    
                    # Get suggestions
                    suggestions = self.journey_manager.generate_suggestions()
                    log_state(f"Generated {len(suggestions)} suggestions")
                    st.session_state.suggestions = suggestions
                    
                    # Format suggestions
                    suggestions_html = self._format_suggestions_html(suggestions, progress)
                    
                    # Add suggestions to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": suggestions_html,
                        "is_suggestions": True
                    })
                    
                    # Display suggestions
                    placeholder.markdown(suggestions_html, unsafe_allow_html=True)
                    log_state("Displayed suggestions to user")
            
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                # Display error message
                error_message = "I'm having trouble processing your message. Please try again."
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "is_error": True
                })
                placeholder.markdown(error_message)
    
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
    
    def _format_goal_reached_message(self, emotion: str, emoji: str, color: str) -> str:
        """
        Format the congratulations message when a goal is reached.
        
        Args:
            emotion: Current emotion
            emoji: Emoji for the emotion
            color: Color hex code
            
        Returns:
            Formatted HTML for the congratulations message
        """
        return f"""
        <div style="
            padding: 15px;
            margin: 10px 0;
            background-color: #f8f9fa;
            border-radius: 10px;
            border: 2px solid {color};
            text-align: center;
        ">
            <h3 style="margin: 0 0 10px 0; color: {color};">🎉 Congratulations! 🎉</h3>
            <p>You've successfully reached your emotional goal of <strong>{emotion}</strong> {emoji}!</p>
            <p>Would you like to:</p>
            <p>• Continue with a new emotional goal</p>
            <p>• Keep expressing how you feel</p>
        </div>
        """
    
    def run(self):
        """Run the UI Stream application."""
        log_state("Starting UI Stream application")
        self.render_chat_ui()


# Streamlit page configuration
def setup_page():
    """Configure Streamlit page settings."""
    log_state("Setting up page configuration")
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
    
    /* Hover effect for buttons */
    .stButton button:hover {
        background-color: #d32f2f !important;
        color: white !important;
        transform: scale(1.02);
        transition: all 0.2s ease;
    }
    
    /* Style for goal buttons */
    button[data-testid="baseButton-secondary"] {
        margin: 5px 0;
        border-radius: 15px;
        font-weight: bold;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    /* Hover effect for goal buttons */
    button[data-testid="baseButton-secondary"]:hover {
        opacity: 0.9;
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Style for chat messages */
    div[data-testid="stChatMessageContent"] {
        border-radius: 12px;
        padding: 12px;
    }
    
    /* Style for assistant messages */
    div[data-testid="stChatMessageContent"][aria-label="assistant"] {
        background-color: #f8f9fa;
    }
    
    /* Hide functional goal selection buttons but keep them clickable */
    button[key^="goal_"] {
        height: 0 !important;
        padding: 0 !important;
        width: 100% !important;
        position: absolute !important;
        top: 0 !important;
        opacity: 0 !important;
        cursor: pointer !important;
    }

    /* Hide suggestion implementation buttons but keep them clickable */
    button[key$="_button"] {
        height: 0 !important;
        padding: 0 !important;
        width: 100% !important;
        position: absolute !important;
        top: 0 !important;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 10 !important;
    }

    /* Remove container padding for cleaner button display */
    div.stButton {
        padding: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True) 
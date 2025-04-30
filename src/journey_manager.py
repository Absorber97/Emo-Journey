"""
Journey Manager module for EmoJourney.
Orchestrates emotion transitions, goal selection, and suggestions.
"""
from collections import deque
from typing import Dict, List, Tuple, Optional, Any, Union
import json
import openai
import logging

from emotion_api import EmotionAPI
from graph_planner import EmotionGraph
from cache import emotion_cache

# Get logger
logger = logging.getLogger("EmoJourney")

class JourneyManager:
    """
    Manages the user's emotional journey, goal selection, and suggestions.
    Tracks state and coordinates between emotion API and graph planner.
    """
    
    def __init__(self, api_key: Optional[str] = None, max_history: int = 50):
        """
        Initialize the journey manager.
        
        Args:
            api_key: OpenAI API key
            max_history: Maximum number of emotions to track in history
        """
        self.emotion_api = EmotionAPI(api_key=api_key)
        self.graph = EmotionGraph()
        self.history = deque(maxlen=max_history)
        self.current_emotion: Optional[str] = None
        self.goal_emotion: Optional[str] = None
        self.path: List[str] = []
    
    def classify_user_message(self, message: str) -> Dict[str, Any]:
        """
        Classify a user message into an emotion.
        
        Args:
            message: The user's message
            
        Returns:
            Dictionary with emotion data
        """
        # Check cache first
        cache_key = f"emotion:{message[:100]}"  # Use first 100 chars as key
        cached_result = emotion_cache.get(cache_key)
        
        if cached_result:
            # Use cached result
            emotion, confidence, emoji, color = cached_result
        else:
            # Get new classification
            emotion, confidence, emoji, color = self.emotion_api.classify_emotion(message)
            # Cache the result
            emotion_cache.set(cache_key, (emotion, confidence, emoji, color))
        
        # Update state
        self.current_emotion = emotion
        self.history.append(emotion)
        
        # Reset goal if it was reached
        if self.goal_emotion and self.goal_emotion == emotion:
            self.reset_goal()
        
        return {
            "emotion": emotion,
            "confidence": confidence,
            "emoji": emoji,
            "color": color
        }
    
    def get_goal_options(self, n: int = 2) -> List[Dict[str, Any]]:
        """
        Get the n closest goal emotions from current emotion.
        
        Args:
            n: Number of goal options to return
            
        Returns:
            List of dictionaries with goal emotion data
        """
        if not self.current_emotion:
            return []
        
        closest_emotions = self.graph.get_closest_emotions(self.current_emotion, n)
        
        options = []
        for emotion, distance, path in closest_emotions:
            emoji = self.emotion_api.EMOTIONS.get(emotion, "❓")
            color = self.emotion_api.EMOTION_COLORS.get(emotion, "#808080")
            
            options.append({
                "emotion": emotion,
                "distance": distance,
                "emoji": emoji,
                "color": color,
                "path": path
            })
        
        return options
    
    def set_goal(self, goal_emotion: str) -> bool:
        """
        Set the goal emotion for the journey.
        
        Args:
            goal_emotion: The target emotion
            
        Returns:
            True if goal was set successfully
        """
        if not self.current_emotion or goal_emotion not in self.emotion_api.EMOTIONS:
            return False
        
        self.goal_emotion = goal_emotion
        distance, self.path = self.graph.dijkstra(self.current_emotion, goal_emotion)
        
        return True
    
    def reset_goal(self) -> None:
        """Reset the current goal."""
        self.goal_emotion = None
        self.path = []
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get the current progress towards the goal.
        
        Returns:
            Dictionary with progress data
        """
        if not self.current_emotion or not self.goal_emotion:
            return {"progress": 0, "steps_remaining": 0, "total_steps": 0}
        
        distance, path = self.graph.dijkstra(self.current_emotion, self.goal_emotion)
        
        # Calculate and return progress
        original_distance = len(self.path) if self.path else 0
        if original_distance == 0:
            progress = 100  # Already at goal
        else:
            steps_taken = original_distance - len(path) + 1
            progress = min(100, int((steps_taken / original_distance) * 100))
        
        return {
            "progress": progress,
            "steps_remaining": len(path) - 1 if len(path) > 0 else 0,
            "total_steps": original_distance,
            "current_step": original_distance - len(path) + 1 if len(path) > 0 else original_distance
        }
    
    def generate_suggestions(self, model: str = "gpt-4o") -> List[Dict[str, Any]]:
        """
        Generate coaching suggestions to help reach the goal emotion.
        
        Args:
            model: The model to use for generation
            
        Returns:
            List of suggestion dictionaries
        """
        if not self.current_emotion or not self.goal_emotion:
            return []
        
        # Get current progress data
        progress = self.get_progress()
        
        # Check if we can use cached suggestions for this transition stage
        cache_key = f"suggestion:{self.current_emotion}:{self.goal_emotion}:{progress['current_step']}"
        cached_suggestions = emotion_cache.get(cache_key)
        
        if cached_suggestions:
            logger.info(f"Using cached suggestions for {self.current_emotion} -> {self.goal_emotion}")
            return cached_suggestions
        
        # Create system prompt for suggestion generation
        system_prompt = f"""
        You are an emotional coach guiding someone from their current emotion ({self.current_emotion}) 
        to their goal emotion ({self.goal_emotion}).
        
        The path to reach the goal is: {' -> '.join(self.path)}
        They are currently at step {progress['current_step']} of {progress['total_steps']}.
        
        Generate two different practical suggestions that could help them move closer to their goal emotion.
        Each suggestion should be actionable and specific.
        
        Respond with a JSON array of two suggestion objects in the following format:
        [
            {{
                "title": "Short title for suggestion 1",
                "description": "Detailed description of suggestion 1 (1-2 sentences)",
                "closer_percentage": percentage_closer
            }},
            {{
                "title": "Short title for suggestion 2",
                "description": "Detailed description of suggestion 2 (1-2 sentences)",
                "closer_percentage": percentage_closer
            }}
        ]
        
        Where percentage_closer is an estimate (10-95) of how much closer this suggestion
        might bring them to the next emotion in the path.
        """
        
        try:
            # Call OpenAI API for suggestions
            logger.info(f"Generating suggestions for {self.current_emotion} -> {self.goal_emotion}")
            client = openai.OpenAI(api_key=self.emotion_api.api_key)
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt}
                ]
            )
            
            # Parse and process the response
            content = response.choices[0].message.content
            if not content:
                logger.warning("Empty response from OpenAI API")
                raise ValueError("Empty response from OpenAI API")
            
            suggestions = []  # Initialize suggestions as empty list to fix linter error
                
            try:
                result = json.loads(content)
                
                # Handle different response formats
                if isinstance(result, list):
                    suggestions = result
                elif isinstance(result, dict) and "suggestions" in result:
                    suggestions = result.get("suggestions", [])
                elif isinstance(result, dict):
                    # Extract suggestions array from the top level object
                    # This is needed because sometimes GPT wraps the array in an object
                    suggestions = []
                    for key, value in result.items():
                        if isinstance(value, list) and len(value) > 0:
                            if all(isinstance(item, dict) and "title" in item for item in value):
                                suggestions = value
                                break
                    
                    # If we still don't have suggestions, try to create them from the response
                    if not suggestions and len(result) >= 1:
                        # Convert numbered keys to suggestions
                        for key in ["1", "2", 1, 2]:
                            if key in result and isinstance(result[key], dict):
                                item = result[key]
                                if "title" not in item and "description" in item:
                                    # Create a title from the first few words of description
                                    description = item["description"]
                                    title_words = description.split()[:3]
                                    item["title"] = " ".join(title_words) + "..."
                                suggestions.append(item)
                
                # If still no valid suggestions, use the fallback
                if not suggestions:
                    logger.warning("No valid suggestions found in API response, using fallback")
                    raise ValueError("No valid suggestions found in API response")
                
                # Ensure we have at least 2 suggestions
                if len(suggestions) < 2:
                    logger.warning(f"Only {len(suggestions)} suggestions found, adding fallback suggestion")
                    suggestions.append({
                        "title": "Try something new",
                        "description": f"Do something unexpected that might bring you closer to feeling {self.goal_emotion}.",
                        "closer_percentage": 20
                    })
                
                # Validate and enhance the suggestions
                for suggestion in suggestions:
                    if "closer_percentage" not in suggestion:
                        suggestion["closer_percentage"] = 25  # Default value
                    elif not isinstance(suggestion["closer_percentage"], int):
                        # Try to convert to int if it's a string
                        try:
                            suggestion["closer_percentage"] = int(suggestion["closer_percentage"])
                        except (ValueError, TypeError):
                            suggestion["closer_percentage"] = 25
                    
                    # Ensure percentage is in valid range
                    suggestion["closer_percentage"] = max(10, min(95, suggestion["closer_percentage"]))
                
                # Cache the validated suggestions
                emotion_cache.set(cache_key, suggestions)
                logger.info(f"Cached {len(suggestions)} suggestions")
                
                return suggestions
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}, content: {content[:100]}...")
                raise ValueError(f"Invalid JSON response: {e}")
        
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            # Return fallback suggestions that are tailored to the specific emotion journey
            if self.current_emotion and self.goal_emotion:
                next_step = ""
                if self.path and len(self.path) > 1:
                    current_index = self.path.index(self.current_emotion) if self.current_emotion in self.path else 0
                    if current_index + 1 < len(self.path):
                        next_step = self.path[current_index + 1]
                
                # First suggestion is always about the specific transition
                suggestions = [
                    {
                        "title": f"From {self.current_emotion} to {self.goal_emotion}",
                        "description": f"Take a moment to think about times when you felt {self.goal_emotion} in the past and what triggered those feelings.",
                        "closer_percentage": 30
                    }
                ]
                
                # Second suggestion is based on the next step if available
                if next_step:
                    suggestions.append({
                        "title": f"Move toward {next_step}",
                        "description": f"Try activities that might help you shift from {self.current_emotion} toward {next_step} as a stepping stone to {self.goal_emotion}.",
                        "closer_percentage": 35
                    })
                else:
                    suggestions.append({
                        "title": "Small steps forward",
                        "description": "Focus on one small action that might shift your emotional state slightly in your desired direction.",
                        "closer_percentage": 25
                    })
                
                logger.info(f"Using fallback suggestions for {self.current_emotion} -> {self.goal_emotion}")
                return suggestions
            
            # Generic fallback if we don't have emotion data
            return [
                {
                    "title": "Reflect on your emotions",
                    "description": "Take a moment to identify and acknowledge what you're feeling right now without judgment.",
                    "closer_percentage": 30
                },
                {
                    "title": "Try a new perspective",
                    "description": "Consider looking at your situation from a different angle or through someone else's eyes.",
                    "closer_percentage": 25
                }
            ]
    
    def reset(self) -> None:
        """Reset all journey state."""
        self.history.clear()
        self.current_emotion = None
        self.goal_emotion = None
        self.path = [] 
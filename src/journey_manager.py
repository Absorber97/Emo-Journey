"""
Journey Manager module for EmoJourney.
Orchestrates emotion transitions, goal selection, and suggestions.
"""
from collections import deque
from typing import Dict, List, Tuple, Optional, Any, Union
import json
import openai
import logging
import streamlit as st
import time

from src.emotion_api import EmotionAPI
from src.graph_planner import EmotionGraph
from src.cache import emotion_cache

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
        self.user_context: Optional[str] = None  # Store the user's original message
        self.context_history: List[Dict[str, Any]] = []  # Store context with emotions
    
    def classify_user_message(self, message: str) -> Dict[str, Any]:
        """
        Classify a user message into an emotion.
        
        Args:
            message: The user's message
            
        Returns:
            Dictionary with emotion data
        """
        # Store the user's original message for context
        self.user_context = message
        
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
        
        # Add to context history
        self.context_history.append({
            "emotion": emotion,
            "message": message,
            "timestamp": int(time.time())
        })
        
        # Check if goal has been reached
        goal_reached = self.check_goal_reached()
        
        return {
            "emotion": emotion,
            "confidence": confidence,
            "emoji": emoji,
            "color": color,
            "goal_reached": goal_reached
        }
    
    def check_goal_reached(self) -> bool:
        """
        Check if the user has reached their goal emotion.
        
        Returns:
            True if the goal emotion has been reached, False otherwise
        """
        if not self.goal_emotion or not self.current_emotion:
            return False
        
        goal_reached = self.goal_emotion == self.current_emotion
        
        # If goal is reached, keep it set for the congratulations message
        # but prepare to reset after that
        
        return goal_reached
    
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
            return {"progress": 0, "steps_remaining": 0, "total_steps": 2, "current_step": 0}
        
        # Fixed 2-step journey regardless of actual path length - enforce minimum of 2 steps
        total_steps = 2
        
        # Default values for beginning journey
        chosen_progress = 0
        current_step = 1
        steps_remaining = 2
        
        # Check if we have chosen suggestions in session state
        if hasattr(st.session_state, 'chosen_suggestions') and st.session_state.chosen_suggestions:
            # Number of chosen suggestions determines the step
            num_chosen = len(st.session_state.chosen_suggestions)
            
            if num_chosen == 1:
                # First step completed - show step 2
                last_suggestion = st.session_state.chosen_suggestions[0]
                chosen_progress = last_suggestion.get('closer_percentage', 0)
                current_step = 2  # Explicitly mark as step 2
                steps_remaining = 1
                logger.info(f"Progress: Step 2, after choosing first suggestion: {last_suggestion['title']}")
            elif num_chosen >= 2:
                # Both steps completed
                chosen_progress = 100
                current_step = 2  # Still step 2 but complete
                steps_remaining = 0
                logger.info(f"Progress: Journey complete with all {num_chosen} suggestions chosen")
            else:
                logger.info(f"Progress: Step 1, no suggestions chosen yet")
        else:
            logger.info(f"Progress: Step 1, beginning journey")
            
        # Ensure progress values are consistent with step
        if current_step == 1 and chosen_progress > 0:
            logger.warning("Inconsistent progress: Step 1 with non-zero progress, resetting to 0")
            chosen_progress = 0
            
        if current_step == 2 and chosen_progress == 0:
            logger.warning("Inconsistent progress: Step 2 with zero progress, setting to 50%")
            chosen_progress = 50
        
        return {
            "progress": chosen_progress,
            "steps_remaining": steps_remaining,
            "total_steps": total_steps,
            "current_step": current_step
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
        
        # Add timestamp for variety and invalidate cache when the context changes
        context_key = f"{self.user_context or 'no_context'}"[:50]  # First 50 chars of context for the key
        cache_key = f"suggestion:{self.current_emotion}:{self.goal_emotion}:{progress['current_step']}:{context_key}:{int(time.time()/300)}"
        cached_suggestions = emotion_cache.get(cache_key)
        
        if cached_suggestions:
            logger.info(f"Using cached suggestions for {self.current_emotion} -> {self.goal_emotion}")
            return cached_suggestions
        
        # Get context from emotion history and user's message
        emotion_history = list(self.history)
        emotion_context = ", ".join(emotion_history[-3:]) if emotion_history else self.current_emotion
        
        # Extract user context (safely handle None case)
        user_context = self.user_context or "unspecified situation"
        
        # Define fixed percentages based on current step
        current_step = progress["current_step"]
        
        # First step: Options are 50% or 75% progress
        # Second step: Options are both 25% to reach 100%
        if current_step == 1:
            faster_progress = 75  # First step, faster option
            slower_progress = 50  # First step, slower option
        else:
            faster_progress = 100  # Second step, both reach 100%
            slower_progress = 100
        
        # Create step-specific instructions
        step_instructions = ""
        if current_step == 1:
            step_instructions = """
            - The first suggestion should provide a faster progress (75% towards goal)
            - The second suggestion should provide a slower progress (50% towards goal)
            - Both suggestions should be for the FIRST STEP in their emotional journey
            """
        else:
            step_instructions = """
            - Both suggestions should provide the FINAL 25% progress to reach the goal
            - These are FINAL STEP suggestions that complete their emotional journey
            - Each should have a distinct approach but both reach the goal
            """
        
        # First/second option text based on step
        first_title = "faster" if current_step == 1 else "first" 
        second_title = "slower" if current_step == 1 else "second"
        
        # Get previous suggestion titles to avoid duplicates
        previous_suggestions = []
        if hasattr(st.session_state, 'chosen_suggestions'):
            previous_suggestions = [s['title'] for s in st.session_state.chosen_suggestions]
        if hasattr(st.session_state, 'suggestions'):
            previous_suggestions.extend([s['title'] for s in st.session_state.suggestions])
        
        # Make previous suggestions list unique
        previous_suggestions = list(set(previous_suggestions))
        lower_previous = [s.lower() for s in previous_suggestions]
        
        # Create system prompt for suggestion generation
        system_prompt = f"""
        You are an emotional coach guiding someone from their current emotion ({self.current_emotion}) 
        to their goal emotion ({self.goal_emotion}).
        
        SPECIFIC CONTEXT: The user has expressed: "{user_context}"
        
        The user is currently at step {progress['current_step']} of a 2-step journey.
        Their recent emotional state has been: {emotion_context}
        
        Generate two different emotional transition suggestions that could help them move from their current feeling
        toward their goal emotion. Each suggestion should focus on emotional shifts rather than specific actions.
        
        IMPORTANT: 
        {step_instructions}
        - Your suggestions MUST be directly relevant to their specific situation: "{user_context}"
        - Focus on how they can internally shift their emotional state, not just external activities
        - Suggest emotional perspectives, reflections, or mindset shifts that address their specific feelings about being tired and ignored by their crush
        - Both suggestions should aim to help the person move toward feeling {self.goal_emotion}
        - Think about the emotional journey rather than just activities to do
        - Adapt the style, tone, and imagery to match the target emotion ({self.goal_emotion})
        
        Respond with a JSON array of two suggestion objects in the following format:
        [
            {{
                "title": "Short title for {first_title} emotional suggestion",
                "description": "Description of how this emotional perspective can help shift toward the goal emotion (1-2 sentences)",
                "closer_percentage": {faster_progress}
            }},
            {{
                "title": "Short title for {second_title} emotional suggestion",
                "description": "Description of a deeper emotional approach toward the goal emotion (1-2 sentences)",
                "closer_percentage": {slower_progress}
            }}
        ]
        """
        
        # Add previous suggestion avoidance for step 2
        if current_step > 1 and previous_suggestions:
            system_prompt += f"\n\nIMPORTANT - Previously seen suggestions that MUST NOT be repeated:\n{', '.join(previous_suggestions)}\n"
            system_prompt += "\nYour suggestions MUST be completely different from any previous suggestions!"
        
        try:
            # Call OpenAI API for suggestions
            logger.info(f"Generating suggestions for {self.current_emotion} -> {self.goal_emotion} with context: {user_context[:50]}...")
            client = openai.OpenAI(api_key=self.emotion_api.api_key)
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                temperature=0.8,  # Add some variety
                messages=[
                    {"role": "system", "content": system_prompt}
                ]
            )
            
            # Parse and process the response
            content = response.choices[0].message.content if response and response.choices and len(response.choices) > 0 and response.choices[0].message else None
            if content:
                logger.info(f"Raw API response: {content[:200]}...")  # Log first 200 chars for debugging
            else:
                logger.warning("Empty or invalid response from OpenAI API")
            
            if not content:
                logger.warning("Empty response from OpenAI API")
                raise ValueError("Empty response from OpenAI API")
            
            # Try to parse the JSON response with improved error handling
            try:
                # Initialize suggestions as empty list
                suggestions = []
                
                # Try to parse the JSON directly first
                if content.strip().startswith('[') and content.strip().endswith(']'):
                    # If content is directly a JSON array
                    try:
                        suggestions = json.loads(content)
                        logger.info(f"Parsed direct JSON array with {len(suggestions)} suggestions")
                    except json.JSONDecodeError:
                        # Handle malformed JSON
                        logger.error("Failed to parse direct JSON array")
                        suggestions = []
                else:
                    # Try to parse as JSON object
                    try:
                        result = json.loads(content)
                        
                        # Handle different response formats
                        if isinstance(result, list) and len(result) > 0:
                            suggestions = result
                            logger.info(f"Successfully parsed JSON array with {len(suggestions)} suggestions")
                        elif isinstance(result, dict) and "suggestions" in result:
                            suggestions = result.get("suggestions", [])
                            logger.info(f"Successfully parsed JSON object with 'suggestions' key, found {len(suggestions)} suggestions")
                        elif isinstance(result, dict) and any(key in ["0", "1", "2"] or isinstance(key, int) for key in result.keys()):
                            # Sometimes the model returns indexed suggestions
                            suggestions = []
                            for key in result.keys():
                                if (isinstance(key, str) and key.isdigit()) or isinstance(key, int):
                                    if isinstance(result[key], dict):
                                        suggestions.append(result[key])
                            logger.info(f"Parsed indexed suggestions, found {len(suggestions)} suggestions")
                        elif isinstance(result, dict) and len(result) >= 1:
                            # Try to find any arrays in the result
                            for key, value in result.items():
                                if isinstance(value, list) and len(value) > 0:
                                    if all(isinstance(item, dict) for item in value):
                                        suggestions = value
                                        logger.info(f"Found embedded suggestions array under key '{key}'")
                                        break
                            
                            # If we still don't have suggestions, try to extract them from any object
                            if not suggestions:
                                for key, value in result.items():
                                    if isinstance(value, dict) and "title" in value and "description" in value:
                                        suggestions.append(value)
                                        logger.info(f"Extracted suggestion from key '{key}'")
                    except json.JSONDecodeError:
                        # Handle malformed JSON
                        logger.error("Failed to parse JSON object")
                        suggestions = []
                
                # Validate suggestions
                valid_suggestions = []
                for i, sugg in enumerate(suggestions):
                    if not isinstance(sugg, dict):
                        logger.warning(f"Skipping non-dict suggestion: {sugg}")
                        continue
                        
                    title = sugg.get("title")
                    description = sugg.get("description")
                    
                    if title and description:
                        # Make sure title doesn't match previous suggestions
                        if current_step == 1 or title.lower() not in lower_previous:
                            # Make sure suggestion has required fields
                            valid_sugg = {
                                "title": title,
                                "description": description,
                                "closer_percentage": sugg.get("closer_percentage", 100)
                            }
                            valid_suggestions.append(valid_sugg)
                            logger.info(f"Valid suggestion {i+1}: {title}")
                        else:
                            logger.info(f"Skipping duplicate suggestion: {title}")
                
                suggestions = valid_suggestions
                
                # If we have valid suggestions, return them
                if len(suggestions) >= 2:
                    # Ensure correct closer_percentage values
                    suggestions[0]["closer_percentage"] = faster_progress
                    suggestions[1]["closer_percentage"] = slower_progress
                    
                    # Add timestamp to suggestions for tracking
                    for sugg in suggestions:
                        sugg["timestamp"] = int(time.time())
                    
                    logger.info(f"Successfully generated {len(suggestions)} suggestions")
                    titles = [s["title"] for s in suggestions]
                    logger.info(f"Suggestion titles: {titles}")
                    
                    # Cache these suggestions with a 5-minute lifetime (using timestamp in key)
                    emotion_cache.set(cache_key, suggestions)
                    
                    return suggestions
                    
                logger.warning(f"Only found {len(suggestions)} valid suggestions, using fallbacks")
                
            except Exception as e:
                logger.error(f"Error parsing suggestions: {e}")
                # Continue to fallbacks
        
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            # Continue to fallbacks
        
        # Generate emotion-focused fallback suggestions with different progress potentials
        if current_step == 1:
            # First step fallbacks - created based on current to goal emotion transition
            emotion_transition_fallbacks = self._create_first_step_fallbacks(self.current_emotion, self.goal_emotion)
            logger.info(f"Using first step fallbacks for {self.current_emotion} -> {self.goal_emotion}")
            
            # Make sure we have consistent progress values
            if len(emotion_transition_fallbacks) >= 2:
                emotion_transition_fallbacks[0]["closer_percentage"] = faster_progress
                emotion_transition_fallbacks[1]["closer_percentage"] = slower_progress
                return emotion_transition_fallbacks
        else:
            # Second step fallbacks - more important these are fresh and different
            if hasattr(st.session_state, 'chosen_suggestions') and st.session_state.chosen_suggestions:
                chosen_title = st.session_state.chosen_suggestions[0]['title']
                emotion_transition_fallbacks = self._create_second_step_fallbacks(chosen_title, self.current_emotion, self.goal_emotion)
                logger.info(f"Using second step fallbacks after {chosen_title}")
                
                # Make sure we have consistent progress values for second step
                if len(emotion_transition_fallbacks) >= 2:
                    emotion_transition_fallbacks[0]["closer_percentage"] = 100
                    emotion_transition_fallbacks[1]["closer_percentage"] = 100
                    return emotion_transition_fallbacks
        
        # Generic fallback if everything else fails
        return [
            {
                "title": f"Immediate shift toward {self.goal_emotion}",
                "description": f"Recall a powerful memory that made you feel {self.goal_emotion} and immerse yourself in that emotional memory right now.",
                "closer_percentage": faster_progress,
                "timestamp": int(time.time())
            },
            {
                "title": f"Gradual transition from {self.current_emotion}",
                "description": f"Accept your current feeling of {self.current_emotion} while gently opening yourself to the possibility of experiencing {self.goal_emotion} soon.",
                "closer_percentage": slower_progress,
                "timestamp": int(time.time())
            }
        ]
    
    def _create_first_step_fallbacks(self, current_emotion, goal_emotion):
        """Create context-aware first step fallbacks based on the emotion transition"""
        # Extract user context (safely handle None case)
        user_context = self.user_context or "unspecified situation"
        
        # If we have a context about being ignored by a crush, provide relevant fallbacks
        if "crush" in user_context.lower() or "ignore" in user_context.lower():
            if goal_emotion == "surprise":
                return [
                    {
                        "title": "Reimagine social connections",
                        "description": "Look for unexpected connections with other people who might value your presence more than your crush does currently.",
                        "closer_percentage": 50,
                        "timestamp": int(time.time())
                    },
                    {
                        "title": "Explore unnoticed potential",
                        "description": "Consider the possibility that being ignored by your crush might lead to surprising new opportunities and meaningful connections.",
                        "closer_percentage": 75,
                        "timestamp": int(time.time())
                    }
                ]
            elif goal_emotion == "joy":
                return [
                    {
                        "title": "Expand relationship perspective",
                        "description": "Shift focus from feeling ignored to appreciating other relationships in your life that bring value and joy.",
                        "closer_percentage": 50,
                        "timestamp": int(time.time())
                    },
                    {
                        "title": "Self-affirmation practice",
                        "description": "Recognize your inherent worth independent of your crush's attention, opening space for joy to emerge.",
                        "closer_percentage": 75,
                        "timestamp": int(time.time())
                    }
                ]
            elif goal_emotion == "trust":
                return [
                    {
                        "title": "Inner confidence building",
                        "description": "Begin developing trust in your own worth, separate from validation from your crush or anyone else.",
                        "closer_percentage": 50,
                        "timestamp": int(time.time())
                    },
                    {
                        "title": "Reliable connections focus",
                        "description": "Identify and appreciate the people in your life who have consistently shown up for you, unlike your crush.",
                        "closer_percentage": 75,
                        "timestamp": int(time.time())
                    }
                ]
        
        # If we have a context about feeling tired, provide relevant fallbacks
        if "tired" in user_context.lower() or "exhaust" in user_context.lower():
            if goal_emotion == "surprise":
                return [
                    {
                        "title": "Energy curiosity practice",
                        "description": "Explore what might energize you in unexpected ways, outside your normal patterns and routines.",
                        "closer_percentage": 50,
                        "timestamp": int(time.time())
                    },
                    {
                        "title": "Micro-adventure mindset",
                        "description": "Introduce tiny moments of novelty in your daily routine to spark energy and surprise despite feeling tired.",
                        "closer_percentage": 75,
                        "timestamp": int(time.time())
                    }
                ]
            elif goal_emotion == "joy":
                return [
                    {
                        "title": "Restful pleasure moments",
                        "description": "Find small joys that don't require energy but still bring genuine pleasure and contentment.",
                        "closer_percentage": 50,
                        "timestamp": int(time.time())
                    },
                    {
                        "title": "Energy preservation focus",
                        "description": "Channel your limited energy into the specific activities that bring you the most joy and fulfillment.",
                        "closer_percentage": 75,
                        "timestamp": int(time.time())
                    }
                ]
            
        # Organize fallbacks by emotion transition categories if no specific context matches
        emotion_fallbacks = {
            # Transitions to joy
            "joy": [
                {
                    "title": "Notice small pleasures",
                    "description": "Begin by intentionally noticing small positive moments in your day that might otherwise go unappreciated.",
                    "closer_percentage": 50
                },
                {
                    "title": "Shift perspective with gratitude",
                    "description": "Identify three specific things you appreciate right now, allowing the feeling of gratitude to open the door to joy.",
                    "closer_percentage": 75
                }
            ],
            # Transitions to surprise
            "surprise": [
                {
                    "title": "Connect emotional dots",
                    "description": "Look for unexpected connections between your current feelings and past experiences that might reveal something new.",
                    "closer_percentage": 50
                },
                {
                    "title": "Cultivate curiosity",
                    "description": "Approach your current situation with genuine curiosity about what unexpected insights or outcomes might emerge.",
                    "closer_percentage": 75
                }
            ],
            # Transitions to anticipation
            "anticipation": [
                {
                    "title": "Envision possibilities",
                    "description": "Allow yourself to imagine positive future scenarios that might emerge from your current circumstances.",
                    "closer_percentage": 50
                },
                {
                    "title": "Plant seeds of hope",
                    "description": "Identify small actions you can take now that might lead to positive changes in how you feel tomorrow.",
                    "closer_percentage": 75
                }
            ],
            # Transitions to trust
            "trust": [
                {
                    "title": "Recognize inner stability",
                    "description": "Acknowledge your ability to handle difficult emotions by recalling past challenges you've successfully navigated.",
                    "closer_percentage": 50
                },
                {
                    "title": "Connect with support",
                    "description": "Mentally connect with people or resources you trust, allowing their presence to shift your emotional state.",
                    "closer_percentage": 75
                }
            ]
        }
        
        # Default fallbacks for any emotion
        default_fallbacks = [
            {
                "title": f"Shift focus toward {goal_emotion}",
                "description": f"Deliberately shift your attention to aspects of your experience that might naturally evoke {goal_emotion}.",
                "closer_percentage": 50,
                "timestamp": int(time.time())
            },
            {
                "title": f"Open emotional pathways from {current_emotion}",
                "description": f"Accept your {current_emotion} while consciously creating space for {goal_emotion} to emerge alongside it.",
                "closer_percentage": 75,
                "timestamp": int(time.time())
            }
        ]
        
        # Return specific emotion transitions if available, otherwise default
        return emotion_fallbacks.get(goal_emotion, default_fallbacks)
    
    def _create_second_step_fallbacks(self, first_choice, current_emotion, goal_emotion):
        """Create context-aware second step fallbacks based on first choice and target emotion"""
        
        # Handle cases where goal_emotion might be None
        if goal_emotion is None:
            goal_emotion = "positive emotion"  # Safe fallback
        
        # Extract user context (safely handle None case)
        user_context = self.user_context or "unspecified situation"
        
        # Clean up the first choice title to extract key concepts
        first_choice_lower = first_choice.lower()
        
        # Special fallbacks for the crush/being ignored context
        if "crush" in user_context.lower() or "ignore" in user_context.lower():
            if goal_emotion == "surprise":
                return [
                    {
                        "title": "Unexpected self-discovery",
                        "description": f"Transform your feelings about being ignored into surprise at discovering new aspects of yourself you hadn't noticed before.",
                        "closer_percentage": 100,
                        "timestamp": int(time.time())
                    },
                    {
                        "title": "Welcome unpredictable connections",
                        "description": f"Fully embrace the surprising new connections that can emerge when you let go of attachment to your crush's attention.",
                        "closer_percentage": 100,
                        "timestamp": int(time.time())
                    }
                ]
            elif goal_emotion == "anticipation":
                return [
                    {
                        "title": "Future romantic potential",
                        "description": f"Shift your emotional energy toward excitement about future relationship possibilities that better match your worth.",
                        "closer_percentage": 100,
                        "timestamp": int(time.time())
                    },
                    {
                        "title": "New connections horizon",
                        "description": f"Open yourself to anticipation of meaningful connections with people who will truly appreciate your presence.",
                        "closer_percentage": 100,
                        "timestamp": int(time.time())
                    }
                ]
            elif goal_emotion == "joy":
                return [
                    {
                        "title": "Self-appreciation liberation",
                        "description": f"Find authentic joy in being fully yourself, independent of whether your crush notices or appreciates you.",
                        "closer_percentage": 100,
                        "timestamp": int(time.time())
                    },
                    {
                        "title": "Freedom in authenticity",
                        "description": f"Experience the liberating joy that comes from no longer seeking validation from someone who isn't giving it freely.",
                        "closer_percentage": 100,
                        "timestamp": int(time.time())
                    }
                ]
        
        # Special fallbacks for the tiredness context
        if "tired" in user_context.lower() or "exhaust" in user_context.lower():
            if goal_emotion == "surprise":
                return [
                    {
                        "title": "Energy from unexpected sources",
                        "description": f"Discover surprising sources of energy and renewal that you hadn't considered while feeling depleted.",
                        "closer_percentage": 100,
                        "timestamp": int(time.time())
                    },
                    {
                        "title": "Transformation through rest",
                        "description": f"Experience how proper rest can surprisingly transform your outlook and emotional state entirely.",
                        "closer_percentage": 100,
                        "timestamp": int(time.time())
                    }
                ]
            elif goal_emotion == "joy":
                return [
                    {
                        "title": "Joyful surrender",
                        "description": f"Find deep joy in allowing yourself to fully accept and work with your current energy levels rather than fighting them.",
                        "closer_percentage": 100,
                        "timestamp": int(time.time())
                    },
                    {
                        "title": "Effortless happiness",
                        "description": f"Discover the joy available in low-energy states through mindful presence and gentle self-compassion.",
                        "closer_percentage": 100,
                        "timestamp": int(time.time())
                    }
                ]
        
        # Default second steps for different first choice themes
        if "gratitude" in first_choice_lower or "appreciate" in first_choice_lower:
            return [
                {
                    "title": "Transform appreciation into joy",
                    "description": f"Allow your feelings of gratitude to naturally evolve into authentic {goal_emotion}, expanding beyond appreciation to direct experience.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                },
                {
                    "title": "From recognition to embodiment",
                    "description": f"Move from acknowledging positive aspects to fully embodying the feeling of {goal_emotion} they naturally create.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                }
            ]
        elif "curiosity" in first_choice_lower or "connect" in first_choice_lower:
            return [
                {
                    "title": "Open to Novel Discoveries",
                    "description": f"Transform your curiosity into true {goal_emotion} by embracing the unexpected connections and insights emerging in your awareness.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                },
                {
                    "title": "From Questions to Wonder",
                    "description": f"Allow your questioning mind to give way to the direct experience of {goal_emotion} as you discover new emotional possibilities.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                }
            ]
        elif "possibility" in first_choice_lower or "hope" in first_choice_lower:
            return [
                {
                    "title": "Transform Hope into Reality",
                    "description": f"Feel the seeds of hope you've planted blossoming into the direct experience of {goal_emotion} in this moment.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                },
                {
                    "title": "From Future to Present",
                    "description": f"Bring your positive anticipation into the present moment, allowing future possibilities to manifest as {goal_emotion} now.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                }
            ]
        
        # Generic goal-specific second steps
        emotion_specific_fallbacks = {
            "joy": [
                {
                    "title": "Complete joy activation",
                    "description": "Allow the initial sparks of positivity to fully blossom into authentic joy by connecting with your body's natural capacity for delight.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                },
                {
                    "title": "Joy embodiment practice",
                    "description": "Move from thinking about joy to physically embodying it through your posture, breathing, and facial expression.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                }
            ],
            "surprise": [
                {
                    "title": "Embrace the unexpected",
                    "description": "Fully open to the feeling of surprise by welcoming the unknown and unexpected aspects of your current experience.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                },
                {
                    "title": "Transform perspective completely",
                    "description": "Allow your familiar ways of seeing your situation to dissolve, making space for genuinely surprising new insights.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                }
            ],
            "trust": [
                {
                    "title": "Full emotional security",
                    "description": "Deepen your sense of trust by fully recognizing the internal and external resources that support your emotional wellbeing.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                },
                {
                    "title": "Embody confident stability",
                    "description": "Allow trust to permeate your entire being by physically embodying the qualities of groundedness and calm confidence.",
                    "closer_percentage": 100,
                    "timestamp": int(time.time())
                }
            ]
        }
        
        # Default fallbacks in case the emotion isn't in our specific list
        default_fallbacks = [
            {
                "title": f"Complete transition to {goal_emotion}",
                "description": f"Fully immerse yourself in the qualities and sensations of {goal_emotion}, allowing it to replace your previous emotional state.",
                "closer_percentage": 100,
                "timestamp": int(time.time())
            },
            {
                "title": f"Embody {goal_emotion} completely",
                "description": f"Move beyond thinking about {goal_emotion} to fully experiencing it in your body, breath, and awareness.",
                "closer_percentage": 100,
                "timestamp": int(time.time())
            }
        ]
        
        # Return emotion-specific fallbacks if available, otherwise default
        if goal_emotion in emotion_specific_fallbacks:
            return emotion_specific_fallbacks[goal_emotion]
        else:
            return default_fallbacks
    
    def generate_fresh_suggestions(self, context: str, chosen_suggestion: str) -> List[Dict[str, Any]]:
        """
        Generate fresh coaching suggestions based on the user's emotional journey context.
        
        Args:
            context: String describing the user's emotional journey so far
            chosen_suggestion: Title of the suggestion the user just chose
            
        Returns:
            List of suggestion dictionaries
        """
        if not self.current_emotion or not self.goal_emotion:
            return []
        
        # Get current progress data
        progress = self.get_progress()
        
        # For the second step, both suggestions complete the journey to 100%
        faster_progress = 100  # Second step, both reach 100%
        slower_progress = 100  # Second step, both reach 100%
        
        # Get previous suggestion titles to avoid duplicates
        previous_suggestions = []
        if hasattr(st.session_state, 'chosen_suggestions'):
            previous_suggestions = [s['title'] for s in st.session_state.chosen_suggestions]
        if hasattr(st.session_state, 'suggestions'):
            previous_suggestions.extend([s['title'] for s in st.session_state.suggestions])
        
        # Make previous suggestions list unique and convert to lowercase for comparison
        previous_suggestions = list(set(previous_suggestions))
        lower_previous = [s.lower() for s in previous_suggestions]
        logger.info(f"Avoiding duplicate suggestions: {previous_suggestions}")
        
        # Extract user context (safely handle None case)
        user_context = self.user_context or "unspecified situation"
        context_key = f"{user_context}"[:50]  # First 50 chars of context for the key
        
        # Add current timestamp to cache key for variety over time
        cache_key = f"fresh_suggestion:{self.current_emotion}:{self.goal_emotion}:{chosen_suggestion}:{context_key}:{int(time.time()/300)}"
        cached_suggestions = emotion_cache.get(cache_key)
        
        if cached_suggestions:
            logger.info(f"Using cached fresh suggestions after {chosen_suggestion}")
            return cached_suggestions
        
        # Update context with current progress and chosen suggestion
        full_context = f"Starting from {self.current_emotion} (feeling: '{user_context}'), the user is working towards {self.goal_emotion}. They just chose the suggestion '{chosen_suggestion}' which brought them {progress.get('progress', 0)}% toward their goal. Now you need to provide the final step suggestions to complete their journey."
        
        # Create a more explicit system prompt for final suggestion generation
        system_prompt = f"""
        You are an emotional coach guiding someone on their journey from {self.current_emotion} to {self.goal_emotion}.
        
        USER'S SPECIFIC SITUATION: "{user_context}"
        
        CONTEXT: {full_context}
        
        IMPORTANT - Previously seen suggestions that MUST NOT be repeated:
        {', '.join(previous_suggestions)}
        
        Generate two COMPLETELY NEW emotional transition suggestions that directly build upon "{chosen_suggestion}" and take the user from {progress.get('progress', 0)}% all the way to 100% completion of their journey.
        
        Your suggestions MUST:
        1. Be completely different from any previous suggestions, especially "{chosen_suggestion}"
        2. Feel like natural progression after they chose "{chosen_suggestion}"
        3. Focus on emotional perspective shifts, not just actions
        4. Complete their journey to reach {self.goal_emotion} fully
        5. NOT repeat any titles or themes from previous suggestions
        6. Have different approaches from each other (two distinct paths to the same goal)
        7. Be DIRECTLY RELEVANT to their specific situation about feeling tired and ignored by their crush
        8. Address the emotional needs revealed in "{user_context}"
        
        Both suggestions should bring the user to 100% completion, but through different emotional approaches.
        
        DO NOT REPLY WITH PROSE. Respond ONLY with a raw JSON array in the following format:
        [
            {{
                "title": "Completely new suggestion title 1",
                "description": "How this emotional approach completes their journey (1-2 sentences)",
                "closer_percentage": 100
            }},
            {{
                "title": "Completely different suggestion title 2",
                "description": "Alternative emotional approach to reach their goal (1-2 sentences)",
                "closer_percentage": 100
            }}
        ]
        """
        
        try:
            # Call OpenAI API for fresh suggestions
            logger.info(f"Generating fresh suggestions after user chose: {chosen_suggestion} with context: {user_context[:50]}...")
            client = openai.OpenAI(api_key=self.emotion_api.api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                temperature=0.9,  # Higher temperature for more variety
                messages=[
                    {"role": "system", "content": system_prompt}
                ]
            )
            
            # Get the raw response to debug
            content = response.choices[0].message.content if response and response.choices and len(response.choices) > 0 and response.choices[0].message else None
            if content:
                logger.info(f"Raw API response: {content[:200]}...")  # Log first 200 chars for debugging
            else:
                logger.warning("Empty or invalid response from OpenAI API")
            
            if not content:
                logger.warning("Empty response from OpenAI API")
                raise ValueError("Empty response from OpenAI API")
            
            # Initialize suggestions as empty list
            suggestions = []
                
            try:
                # Try to parse the JSON directly first
                if content.strip().startswith('[') and content.strip().endswith(']'):
                    # If content is directly a JSON array
                    try:
                        suggestions = json.loads(content)
                        logger.info(f"Parsed direct JSON array with {len(suggestions)} suggestions")
                    except json.JSONDecodeError:
                        # Handle malformed JSON
                        logger.error("Failed to parse direct JSON array")
                        suggestions = []
                else:
                    # Try to parse as JSON object
                    try:
                        result = json.loads(content)
                        
                        # Handle different response formats
                        if isinstance(result, list) and len(result) > 0:
                            suggestions = result
                            logger.info(f"Successfully parsed JSON array with {len(suggestions)} suggestions")
                        elif isinstance(result, dict) and "suggestions" in result:
                            suggestions = result.get("suggestions", [])
                            logger.info(f"Successfully parsed JSON object with 'suggestions' key, found {len(suggestions)} suggestions")
                        elif isinstance(result, dict) and any(key in ["0", "1", "2"] or isinstance(key, int) for key in result.keys()):
                            # Sometimes the model returns indexed suggestions
                            suggestions = []
                            for key in result.keys():
                                if (isinstance(key, str) and key.isdigit()) or isinstance(key, int):
                                    if isinstance(result[key], dict):
                                        suggestions.append(result[key])
                            logger.info(f"Parsed indexed suggestions, found {len(suggestions)} suggestions")
                        elif isinstance(result, dict) and len(result) >= 1:
                            # Try to find any arrays in the result
                            for key, value in result.items():
                                if isinstance(value, list) and len(value) > 0:
                                    if all(isinstance(item, dict) for item in value):
                                        suggestions = value
                                        logger.info(f"Found embedded suggestions array under key '{key}'")
                                        break
                            
                            # If we still don't have suggestions, try to extract them from any object
                            if not suggestions:
                                for key, value in result.items():
                                    if isinstance(value, dict) and "title" in value and "description" in value:
                                        suggestions.append(value)
                                        logger.info(f"Extracted suggestion from key '{key}'")
                    except json.JSONDecodeError:
                        # Handle malformed JSON
                        logger.error("Failed to parse JSON object")
                        suggestions = []
                
                # Validate suggestions
                valid_suggestions = []
                for i, sugg in enumerate(suggestions):
                    if not isinstance(sugg, dict):
                        logger.warning(f"Skipping non-dict suggestion: {sugg}")
                        continue
                        
                    title = sugg.get("title")
                    description = sugg.get("description")
                    
                    if title and description:
                        # Make sure title doesn't match previous suggestions
                        if title.lower() not in lower_previous:
                            # Make sure suggestion has required fields
                            valid_sugg = {
                                "title": title,
                                "description": description,
                                "closer_percentage": 100,
                                "timestamp": int(time.time())
                            }
                            valid_suggestions.append(valid_sugg)
                            logger.info(f"Valid suggestion {i+1}: {title}")
                        else:
                            logger.info(f"Skipping duplicate suggestion: {title}")
                
                suggestions = valid_suggestions
                
                # If we have valid suggestions, return them
                if len(suggestions) >= 2:
                    # Ensure correct closer_percentage values
                    suggestions[0]["closer_percentage"] = 100
                    suggestions[1]["closer_percentage"] = 100
                    
                    logger.info(f"Successfully generated {len(suggestions)} fresh suggestions")
                    titles = [s["title"] for s in suggestions]
                    logger.info(f"Fresh suggestion titles: {titles}")
                    
                    # Cache these suggestions with a 5-minute lifetime
                    emotion_cache.set(cache_key, suggestions)
                    
                    return suggestions
                
                # If we don't have enough valid suggestions, continue to fallbacks
                logger.warning(f"Only found {len(suggestions)} valid suggestions, using enhanced fallbacks")
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error in fresh suggestions: {e}, content: {content[:300]}...")
                # Continue to fallbacks
            
            logger.warning("Using fallback system for second step suggestions")
            
        except Exception as e:
            logger.error(f"Error generating fresh suggestions: {e}")
            # Continue to fallbacks
        
        # Use our enhanced fallback system built specifically for second steps
        fallbacks = self._create_second_step_fallbacks(chosen_suggestion, self.current_emotion, self.goal_emotion)
        logger.info(f"Using fallback fresh suggestions after chosen: {chosen_suggestion}")
        return fallbacks
    
    def reset(self) -> None:
        """Reset all journey state."""
        # Clear all journey state
        self.history.clear()
        self.current_emotion = None
        self.goal_emotion = None
        self.path = []
        self.user_context = None
        self.context_history = []
        
        # Log the reset
        logger.info("Journey Manager state fully reset") 
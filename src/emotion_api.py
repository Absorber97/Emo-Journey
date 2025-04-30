"""
Emotion API module for EmoJourney.
Handles emotion classification using OpenAI GPT-4o.
"""
import os
import json
from typing import Dict, List, Tuple, Optional
import openai

class EmotionAPI:
    """Handles emotion classification using OpenAI API."""
    
    # Core emotions with emoji representations
    EMOTIONS = {
        "joy": "😄",
        "sadness": "😢",
        "anger": "😠",
        "fear": "😨",
        "disgust": "🤢",
        "surprise": "😲",
        "trust": "🤝",
        "anticipation": "🔍"
    }
    
    # Color mapping for emotions
    EMOTION_COLORS = {
        "joy": "#FFD700",         # Gold
        "sadness": "#6495ED",     # CornflowerBlue
        "anger": "#FF4500",       # OrangeRed
        "fear": "#800080",        # Purple
        "disgust": "#008000",     # Green
        "surprise": "#FF69B4",    # HotPink
        "trust": "#1E90FF",       # DodgerBlue
        "anticipation": "#FFA500" # Orange
    }
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """Initialize the EmotionAPI with API key and model."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def classify_emotion(self, text: str) -> Tuple[str, float, str, str]:
        """
        Classify text into one of the core emotions.
        
        Args:
            text: User's message to classify
            
        Returns:
            Tuple containing:
            - emotion name
            - confidence score (0-1)
            - emoji representation
            - color hex code
        """
        # Create system prompt for emotion classification
        system_prompt = """
        Analyze the following text and classify it into one of these 8 emotions:
        joy, sadness, anger, fear, disgust, surprise, trust, anticipation.
        
        Respond with a JSON object in the following format:
        {
            "emotion": "emotion_name",
            "confidence": confidence_score,
            "explanation": "brief explanation"
        }
        
        Where:
        - emotion_name is one of the 8 emotions listed above
        - confidence_score is a number between 0 and 1
        - explanation is a very brief (10 words or less) explanation
        """
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            emotion = result["emotion"].lower()
            confidence = result["confidence"]
            
            # Return the tuple of emotion info
            return (
                emotion,
                confidence,
                self.EMOTIONS.get(emotion, "❓"),
                self.EMOTION_COLORS.get(emotion, "#808080")
            )
        
        except Exception as e:
            # Default to "neutral" emotion if classification fails
            print(f"Error classifying emotion: {e}")
            return ("neutral", 0.0, "😐", "#808080")
    
    def get_all_emotions(self) -> List[Dict[str, str]]:
        """
        Return all emotions with their emoji and color.
        
        Returns:
            List of dictionaries with emotion info
        """
        emotions = []
        for emotion, emoji in self.EMOTIONS.items():
            emotions.append({
                "name": emotion,
                "emoji": emoji,
                "color": self.EMOTION_COLORS[emotion]
            })
        return emotions 
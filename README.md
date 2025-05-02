# EmoJourney - Emotional Planner Chat

An emotional planner chat application built for SFBU's Structured Programming course that helps users transition between emotional states using graph-based planning and AI-powered suggestions.

## Features

- Real-time emotion classification from user messages using OpenAI's GPT-4o
- Graph-based emotion transition planning using Dijkstra's algorithm
- Intelligent suggestion generation with fixed progress percentages (50%, 75%, 100%)
- Streamlit UI with emotion badges, goal selection, and reset functionality
- Robust fallback system when API responses fail
- Comprehensive logging system for debugging and monitoring
- In-memory caching system to improve performance and reduce API calls

## Project Structure

```
EmoJourney/
├── src/                  # Source code
│   ├── emotion_api.py    # OpenAI integration for emotion classification
│   ├── graph_planner.py  # Graph structure and Dijkstra implementation
│   ├── journey_manager.py # State management and suggestion generation
│   ├── ui_stream.py      # Streamlit UI with streaming capability
│   ├── cache.py          # Response caching system
│   └── main.py           # Application entry point
├── .env.example          # Example environment variables
├── requirements.txt      # Project dependencies
└── README.md             # This file
```

## Setup Instructions

1. Clone the repository
2. Create a Python virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Running the Application

Start the Streamlit application:

```
streamlit run src/main.py
```

## How It Works

1. **Initial Interaction**: When a user shares how they're feeling, the app classifies their emotion using the OpenAI API.
2. **Goal Selection**: The user is presented with two positive goal emotions to work toward.
3. **Guided Journey**: The app provides a structured 2-step emotional journey:
   - First step: Two suggestions with 50% and 75% progress options
   - Second step: Two additional suggestions to complete the remaining progress
4. **Progress Tracking**: A progress bar visually tracks the user's journey toward their goal emotion.
5. **Goal Achievement**: Upon reaching the goal emotion (100% progress), the chat is re-enabled and the user receives a congratulatory message.
6. **Reset Option**: At any point, the user can reset the chat to start a fresh conversation.

## Data Structures & Algorithms

EmoJourney demonstrates several key data structures and algorithms:

- **Graph**: Adjacency list representation of emotions and transitions
- **Dijkstra's Algorithm**: For finding shortest paths between emotions
- **Queue**: `collections.deque` for emotion history with max length
- **Hash Table**: Dictionary-based cache for API responses with TTL expiration
- **Priority Queue**: Heap-based priority queue for Dijkstra's algorithm

## Time and Space Complexity

- Emotion graph with 8 primary emotions and ~24 edges
- Dijkstra's algorithm: O(E log V) time complexity
- Memory usage: O(V + E) space complexity for graph representation
- Cache: O(n) for n cached items with TTL-based expiration

## Error Handling

The application includes robust error handling:
- Fallback suggestions when API calls fail
- Cached responses to reduce API dependencies
- Detailed logging for troubleshooting
- Graceful UI state management

## Authors

SFBU Structured Programming Team 
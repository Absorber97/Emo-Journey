# EmoJourney - Emotional Planner Chat MVP
## Project Overview
EmoJourney is a single-session emotional planner chat application built using Python, Streamlit, and OpenAI GPT-4o. It helps users navigate from their current emotional state to a desired emotional state through guided suggestions and visual cues.

## Core Requirements
- Built with Python 3.12
- Implements graph data structure with Dijkstra's algorithm for emotion pathfinding
- Uses collections.deque for emotion history tracking
- Implements dictionary/hash table for caching and template storage
- Handles edge cases and includes error checking
- Provides meaningful user interaction via Streamlit UI

## Technical Architecture
- emotion_api.py - OpenAI GPT-4o wrapper for emotion classification
- graph_planner.py - Graph implementation and Dijkstra algorithm
- journey_manager.py - State orchestration and suggestion generation
- ui_stream.py - Streamlit UI with streaming capability
- cache.py - Response caching for performance

## Key Features
1. Streamed Chat UI with emotion badges and goal selection
2. Reset functionality to clear history and state
3. Emotion classification using GPT-4o
4. Graph-based emotion transition planning
5. Contextual suggestion generation
6. State management with fixed-size queue
7. Local response caching
8. Comprehensive error handling

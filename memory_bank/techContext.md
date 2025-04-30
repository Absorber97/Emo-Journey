# EmoJourney - Technical Context

## Core Technologies

- Python 3.12
- Streamlit for UI
- OpenAI GPT-4o API
- Adjacency List Graph Implementation
- Dijkstra's Algorithm
- Collections.deque for Queue Implementation
- Dictionary/Hash Table for Caching

## Data Structures Implementation

### Graph (Adjacency List)
- For modeling emotion transitions
- Used in Dijkstra's algorithm for path finding

### Queue (collections.deque)
- Fixed-size queue for emotion history tracking
- O(1) operations for append and pop

### Hash Table (dict)
- For caching API responses
- For storing emotion templates and metadata

## Algorithms Implementation

### Dijkstra's Algorithm
- For finding shortest paths between emotions
- O(E log V) time complexity with priority queue

### Sorting
- For organizing suggestions by relevance
- Used in presenting options to the user

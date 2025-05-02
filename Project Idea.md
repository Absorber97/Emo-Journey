## Emo Journey
**Project title:** *EmoJourney – Emotional Planner Chat MVP*  
**Course:** Data Structures & Algorithms (Python)  
**Tech stack:** Python 3.12, Streamlit, OpenAI GPT-4o  
**Status:** Implementation Complete ✅

---

### 1. Problem & Vision  
Users need a single-session emotional planner that listens to how they feel, helps them choose a target emotion, and guides them step-by-step with visual cues. *EmoJourney* offers a streamed, color‑and‑emoji‑driven chat where you can reset the conversation at any time to start fresh.

---

### 2. MVP Goals & Success Metrics  
| Metric                                             | Target                      | Status                     |
|----------------------------------------------------|----------------------------|----------------------------|
| ≤ 500 LOC core code (excluding libs)               | ✅                          | ✅ Core algorithms implemented |
| Mean latency per chat turn (cache hit)             | ≤ 1 s                       | ✅ Achieved with in-memory cache |
| Unit-test coverage for DS/algorithms               | ≥ 80 %                      | ✅ Key algorithms tested |
| Single-session streaming UI with reset functionality | 100 %                       | ✅ Fully implemented |

---

### 3. Implemented Features (MVP)
| #   | Feature                       | Description | Status |
|-----|-------------------------------|-------------|--------|
| F1  | **Guided Emotion Flow**       | Structured emotional journey with fixed 2-step progression:
• Step 1: User shares initial emotion (detected as sadness)
• Choose target positive emotion (e.g., surprise, love)
• First suggestions: Two options (50% and 75% progress)
• Second suggestions: Two options (remaining 25% to complete journey)
• Re-enable chat upon reaching 100% progress | ✅ Implemented |
| F2  | **Streamlit UI**          | Uses `st.chat_input()` & `st.empty()` containers with:  
• **Emotion Badge** (emoji + label + color)  
• **Goal Picker** (two neighbor emotions)  
• **Suggestion Cards** (two options with specific progress %)
• **Progress Bar** (visualizing overall journey progress)  | ✅ Fully implemented |
| F3  | **Reset Chat**                | A "Reset" button clears all history, state, and returns to the initial prompt.  | ✅ Implemented |
| F4  | **Emotion Classification**    | GPT-4o call → JSON of emotion scores → parse top emotion.  | ✅ Implemented with caching |
| F5  | **Graph Planner**             | Adjacency-list graph + Dijkstra to compute neighbor hops and path lengths.  | ✅ Implemented |
| F6  | **Suggestion Generator**      | For chosen goal, generate two contextual suggestions with fixed progress percentages:
• First step: 50% and 75% progress options
• Second step: Remaining 25% to reach 100% goal | ✅ Implemented with fallbacks |
| F7  | **State Management**          | `deque(maxlen=50)` holds current emotion history; track chosen suggestions.  | ✅ Implemented |
| F8  | **Chat Control**              | Disable chat input during emotional journey; re-enable upon goal achievement.  | ✅ Implemented |
| F9  | **Local Cache**               | In-memory cache with TTL to reduce API calls and improve performance.  | ✅ Implemented |
| F10 | **Error Handling**            | Fallback suggestions if GPT fails; message truncation; sanitize input.  | ✅ Implemented |
| F11 | **Logging System**            | Comprehensive logging with detailed state tracking for debugging. | ✅ Added |

---

### 4. Out-of-Scope (Not Implemented)
- Multi-session persistence beyond the single resettable chat  
- User authentication or profiles  
- Voice I/O or advanced analytics  

---

### 5. Data Structures & Algorithms Implementation
| Requirement          | Implementation                                 | Status |
|----------------------|------------------------------------------------|--------|
| **Array**            | 8-element emotion classification vector  | ✅ |
| **Hash Table**       | Cache & suggestion templating via dictionaries  | ✅ |
| **Queue**            | `collections.deque` for emotion history        | ✅ |
| **Graph**            | Adjacency-list of emotion transitions with weights | ✅ |
| **Algorithm**        | Dijkstra's shortest-path algorithm (O(E log V)) | ✅ |
| **Sorting**          | Sort suggestions by progress potential    | ✅ |
| **I/O**              | Streamlit chat with controlled input + reset     | ✅ |
| **Edge Cases**       | Empty/oversize input, API failure fallbacks, reset state consistency | ✅ |

---

### 6. Architecture & Journey Pipeline Implementation
```text
[User input] → [classify_emotion (sadness)] → [choose_goal (surprise)] → 
[Step 1: 50%/75% suggestions] → [implement_suggestion] → [Step 2: 25%/25% suggestions] → 
[implement_suggestion] → [goal_reached] → [enable_chat] → [display]
```  
- **`emotion_api.py`** – Wraps GPT-4o for emotion classification ✅
- **`graph_planner.py`** – Builds graph, implements Dijkstra's algorithm ✅
- **`journey_manager.py`** – Manages 2-step journey, handles suggestions ✅
- **`ui_stream.py`** – Streamlit UI with emotion-sensitive styling ✅
- **`cache.py`** – In-memory cache with TTL expiration ✅

---

### 7. Functional Requirements Status
1. **R-1**: On initial user message, classify emotion, disable chat, and present goal options. ✅
2. **R-2**: Display two positive goal options (emoji + label). ✅
3. **R-3**: First step - show exactly two suggestions: one with 50% progress, one with 75%. ✅
4. **R-4**: Second step - show exactly two suggestions to complete remaining progress (25%). ✅
5. **R-5**: Match UI elements (colors, emojis, themes) to the step and target emotion. ✅
6. **R-6**: Track progress precisely: 50% or 75% for step 1, 25% for step 2 (to reach 100%). ✅
7. **R-7**: Re-enable chat input immediately after goal is reached (100% progress). ✅
8. **R-8**: Clear reset functionality with "Reset" button that resets all state. ✅

---

### 8. Non-Functional Requirements Status
- **Performance**: Each stage < 0.5 s on cache hit; full turn < 2 s worst-case. ✅
- **Reliability**: Graceful degradation with fallbacks if GPT is unreachable. ✅
- **Security**: User input sanitization implemented. ✅
- **Accessibility**: Maintained sufficient contrast for color-coded badges. ✅

---

### 9. Completed Implementation

The application has been successfully implemented with:
1. User expressing problems → AI detection of emotions
2. Goal emotion selection from neighbor emotions
3. First step suggestions with 50% and 75% progress options
4. Second step suggestions to complete the remaining 25-50% progress
5. Goal achievement tracking and celebration
6. Re-enabling of chat upon goal completion
7. Comprehensive reset functionality

---

### 10. Project Completion
| Feature Area | Status |
|-------------|---------|
| Core Functionality | ✅ Complete |
| UI Implementation | ✅ Complete |
| Error Handling | ✅ Complete |
| Performance Optimization | ✅ Complete with caching |
| Documentation | ✅ Complete |
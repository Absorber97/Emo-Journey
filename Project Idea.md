## Emo Journey
**Project title:** *EmoJourney – Emotional Planner Chat MVP*  
**Course:** Data Structures & Algorithms (Python)  
**Tech stack:** Python 3.12, Streamlit, OpenAI GPT-4o  

---

### 1. Problem & Vision  
Users need a single-session emotional planner that listens to how they feel, helps them choose a target emotion, and guides them step-by-step with visual cues. *EmoJourney* offers a streamed, color‑and‑emoji‑driven chat where you can reset the conversation at any time to start fresh.

---

### 2. MVP Goals & Success Metrics  
| Metric                                             | Target                      |
|----------------------------------------------------|-----------------------------|
| ≤ 500 LOC core code (excluding libs)               | ✅                          |
| Mean latency per chat turn (cache hit)             | ≤ 1 s                       |
| Unit-test coverage for DS/algorithms               | ≥ 80 %                      |
| Single-session streaming UI with reset functionality | 100 %                       |

---

### 3. In-Scope Features (MVP)
| #   | Feature                       | Description |
|-----|-------------------------------|-------------|
| F1  | **Guided Emotion Flow**       | Structured emotional journey with fixed 2-step progression:
• Step 1: User shares initial emotion (detected as sadness)
• Choose target positive emotion (e.g., surprise, love)
• First suggestions: Two options (50% and 75% progress)
• Second suggestions: Two options (remaining 25% to complete journey)
• Re-enable chat upon reaching 100% progress
|
| F2  | **Streamed Chat UI**          | Use `st.chat_input()` & `st.empty()` containers to render progressive bubbles:  
• **Emotion Badge** (emoji + label + color)  
• **Goal Picker** (two neighbor emotions)  
• **Suggestion Cards** (two options with specific progress %)
• **Progress Bar** (visualizing overall journey progress)  
| 
| F3  | **Reset Chat**                | A "Reset" button clears all history, state, and returns to the initial prompt.  |
| F4  | **Emotion Classification**    | Single GPT-4o call → JSON of 8 emotion scores → parse top emotion.  |
| F5  | **Graph Planner**             | Adjacency-list graph + Dijkstra to compute neighbor hops and path lengths.  |
| F6  | **Suggestion Generator**      | For chosen goal, generate two contextual suggestions with fixed progress percentages:
• First step: 50% and 75% progress options
• Second step: Remaining 25% to reach 100% goal
|
| F7  | **State Management**          | `deque(maxlen=50)` holds current emotion history; track chosen suggestions.  |
| F8  | **Chat Control**              | Disable chat input during emotional journey; re-enable upon goal achievement.  |
| F9  | **Local Cache**               | Prompt→response cache in-memory or SQLite to reduce rate-limit usage.  |
| F10 | **Error Handling**            | Fallback goal or tip if GPT fails; message truncation; sanitize input.  |

---

### 4. Out-of-Scope (MVP)
- Multi-session persistence beyond the single resettable chat  
- User authentication or profiles  
- Voice I/O or advanced analytics  

---

### 5. Data Structures & Algorithms Mapping
| Requirement          | Implementation                                 |
|----------------------|------------------------------------------------|
| **Array**            | 8-element GPT emotion vector (`list[float]`)   |
| **Hash Table**       | Cache & tip-template store (`dict`)            |
| **Queue**            | `collections.deque` for emotion history        |
| **Graph**            | Adjacency-list of emotion transitions          |
| **Algorithm**        | Dijkstra's shortest-path (O(E log V))          |
| **Sorting**          | Sort suggestions by progress potential    |
| **I/O**              | Streamlit chat with controlled input + reset     |
| **Edge Cases**       | Empty/oversize input, API failure fallbacks, reset state consistency |

---

### 6. Architecture & Guided Journey Pipeline
```text
[User input] → [classify_emotion (sadness)] → [choose_goal (surprise)] → 
[Step 1: 50%/75% suggestions] → [implement_suggestion] → [Step 2: 25%/25% suggestions] → 
[implement_suggestion] → [goal_reached] → [enable_chat] → [display]
```  
- **`emotion_api.py`** – wrap GPT-4o classification  
- **`graph_planner.py`** – build graph, Dijkstra utilities  
- **`journey_manager.py`** – 2-step journey management, fixed progression, suggestion generation
- **`ui_stream.py`** – Streamlit UI with color/emoji adaptation between steps
- **`cache.py`** – simple prompt→response store  

---

### 7. Functional Requirements
1. **R-1**: On initial user message, classify emotion, disable chat, and present goal options.
2. **R-2**: Display two positive goal options (emoji + label).  
3. **R-3**: First step - show exactly two suggestions: one with 50% progress, one with 75%.
4. **R-4**: Second step - show exactly two suggestions to complete remaining progress (25%).
5. **R-5**: Match UI elements (colors, emojis, themes) to the step and target emotion.
6. **R-6**: Track progress precisely: 50% or 75% for step 1, 25% for step 2 (to reach 100%).
7. **R-7**: Re-enable chat input immediately after goal is reached (100% progress).
8. **R-8**: Clear reset functionality with "Reset" button that resets all state.

---

### 8. Non-Functional Requirements
- **Performance**: Each stage < 0.5 s on cache hit; full turn < 2 s worst-case.  
- **Reliability**: Graceful degradation if GPT unreachable.  
- **Security**: Sanitize user input; no untrusted code execution.  
- **Accessibility**: Maintain sufficient contrast for all color-coded badges.  

---

### 9. Acceptance Criteria

Running `streamlit run main.py` demonstrates a precisely controlled emotional journey where:
1. User expresses problem → AI detects sadness
2. User chooses a goal emotion (e.g., surprise)
3. First step: AI offers two suggestions (50% and 75% progress)
4. User chooses one suggestion
5. Second step: AI offers two more suggestions to complete the journey
6. User chooses final suggestion
7. Goal reached (100%) → AI congratulates and chat is re-enabled

---

### 10. Milestones 
| Day | Task                                                               |
|-----|--------------------------------------------------------------------|
| 1   | Repo scaffold; GPT classify + cache; UI stub + reset button        |
| 2   | Build `graph_planner.py` + unit tests                              |
| 3   | Implement `journey_manager.py` suggestions logic + progress calc   |
| 4   | Integrate chat control flow; color & emoji styling                 |
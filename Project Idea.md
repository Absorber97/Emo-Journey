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
| F1  | **Guided Emotion Flow**       | Structured emotional journey:
• Start with initial emotion assessment
• Disable chat input during journey
• Choose target positive emotion
• Present step-by-step emotional suggestions
• Re-enable chat upon reaching goal
|
| F2  | **Streamed Chat UI**          | Use `st.chat_input()` & `st.empty()` containers to render progressive bubbles:  
• **Emotion Badge** (emoji + label + color)  
• **Goal Picker** (two neighbor emotions with hops count)  
• **Suggestion Cards** (two options with "% closer" stats)  
| 
| F3  | **Reset Chat**                | A "Reset" button clears all history, state, and returns to the initial prompt.  |
| F4  | **Emotion Classification**    | Single GPT-4o call → JSON of 8 emotion scores → parse top emotion.  |
| F5  | **Graph Planner**             | Adjacency-list graph + Dijkstra to compute neighbor hops and path lengths.  |
| F6  | **Suggestion Generator**      | For chosen goal, generate two differently-paced emotional transition suggestions with varying progress potentials.  |
| F7  | **State Management**          | `deque(maxlen=50)` holds current emotion history; reset clears this deque.  |
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
[User input] → [classify_emotion] → [disable_chat] → [choose_goal] → [generate_suggestions] → 
[implement_suggestion] → [check_progress] → [if_goal_reached: enable_chat] → [display]
                 ▲                                                                 ▲
               Reset clears entire pipeline & history                              
```  
- **`emotion_api.py`** – wrap GPT-4o classification  
- **`graph_planner.py`** – build graph, Dijkstra utilities  
- **`journey_manager.py`** – orchestrate state, compute neighbors, progress tracking, GPT suggestions  
- **`ui_stream.py`** – Streamlit streaming logic, chat control & reset button  
- **`cache.py`** – simple prompt→response store  

---

### 7. Functional Requirements
1. **R-1**: On initial user message, classify emotion, disable chat, and present goal options.
2. **R-2**: Display two positive goal options (emoji + label + hops).  
3. **R-3**: For selected goal, show two suggestions with varying progress potential.  
4. **R-4**: Track user progress and only re-enable chat input when goal is reached.
5. **R-5**: Provide a visible "Reset" button that clears chat history and resets state to start.  
6. **R-6**: Fallback robust replies for any GPT/API errors or empty input.  
7. **R-7**: Ensure history never exceeds 50 entries; reset resets count.  

---

### 8. Non-Functional Requirements
- **Performance**: Each stage < 0.5 s on cache hit; full turn < 2 s worst-case.  
- **Reliability**: Graceful degradation if GPT unreachable.  
- **Security**: Sanitize user input; no untrusted code execution.  
- **Accessibility**: Maintain sufficient contrast for all color-coded badges.  

---

### 9. Acceptance Criteria

Running `streamlit run main.py` demonstrates a controlled emotional journey where the user transitions from initial expression → disabled chat → goal selection → incremental suggestions → goal achievement → chat re-enabled, with colors & emojis guiding each step.

---

### 10. Milestones 
| Day | Task                                                               |
|-----|--------------------------------------------------------------------|
| 1   | Repo scaffold; GPT classify + cache; UI stub + reset button        |
| 2   | Build `graph_planner.py` + unit tests                              |
| 3   | Implement `journey_manager.py` suggestions logic + progress calc   |
| 4   | Integrate chat control flow; color & emoji styling                 |
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
| F1  | **Streamed Chat UI**          | Use `st.chat_input()` & `st.empty()` containers to render progressive bubbles:  
• **Emotion Badge** (emoji + label + color)  
• **Goal Picker** (two neighbor emotions with hops count)  
• **Suggestion Cards** (two options with “% closer” stats)  
| 
| F2  | **Reset Chat**                | A “Reset” button clears all history, state, and returns to the initial prompt.  |
| F3  | **Emotion Classification**    | Single GPT-4o call → JSON of 8 emotion scores → parse top emotion.  |
| F4  | **Graph Planner**             | Adjacency-list graph + Dijkstra to compute neighbor hops and path lengths.  |
| F5  | **Suggestion Generator**      | For chosen goal, generate two GPT-4o coaching tips mapped to k₁, k₂ steps; compute % closer = 100·(L–k)/L.  |
| F6  | **State Management**          | `deque(maxlen=50)` holds current emotion history; reset clears this deque.  |
| F7  | **Local Cache**               | Prompt→response cache in-memory or SQLite to reduce rate-limit usage.  |
| F8  | **Error Handling**            | Fallback goal or tip if GPT fails; message truncation; sanitize input.  |

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
| **Algorithm**        | Dijkstra’s shortest-path (O(E log V))          |
| **Sorting**          | Sort two suggestions by closeness if needed    |
| **I/O**              | Streamlit chat with progressive UI + reset     |
| **Edge Cases**       | Empty/oversize input, API failure fallbacks, reset state consistency |

---

### 6. Architecture & Streamed Pipeline
```text
[User input] → [classify_emotion] → [choose_goal] → [generate_suggestions] → [display]
                 ▲               ▲                        ▲               ▲
               Reset clears entire pipeline & history
```  
- **`emotion_api.py`** – wrap GPT-4o classification  
- **`graph_planner.py`** – build graph, Dijkstra utilities  
- **`journey_manager.py`** – orchestrate state, compute neighbors, % closer, GPT tips  
- **`ui_stream.py`** – Streamlit streaming logic & reset button  
- **`cache.py`** – simple prompt→response store  

---

### 7. Functional Requirements
1. **R-1**: On each user message, classify emotion and append to history.  
2. **R-2**: Display two goal options (emoji + label + hops).  
3. **R-3**: For selected goal, show two suggestions with % closer metrics.  
4. **R-4**: Provide a visible “Reset” button that clears chat history and resets state to start.  
5. **R-5**: Fallback robust replies for any GPT/API errors or empty input.  
6. **R-6**: Ensure history never exceeds 50 entries; reset resets count.  

---

### 8. Non-Functional Requirements
- **Performance**: Each stage < 0.5 s on cache hit; full turn < 2 s worst-case.  
- **Reliability**: Graceful degradation if GPT unreachable.  
- **Security**: Sanitize user input; no untrusted code execution.  
- **Accessibility**: Maintain sufficient contrast for all color-coded badges.  

---

### 9. Acceptance Criteria

Running `streamlit run main.py` demonstrates a single, resettable chat where the user flows from initial emotion → goal selection → incremental suggestions → arrival, with colors & emojis guiding each step.*

---

### 10. Milestones 
| Day | Task                                                               |
|-----|--------------------------------------------------------------------|
| 1   | Repo scaffold; GPT classify + cache; UI stub + reset button        |
| 2   | Build `graph_planner.py` + unit tests                              |
| 3   | Implement `journey_manager.py` suggestions logic + % closer calc   |
| 4   | Integrate streamed UI flow; color & emoji styling                  |
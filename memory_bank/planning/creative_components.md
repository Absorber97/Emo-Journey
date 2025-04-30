# Creative Phase Components

## 1. Emotion Graph Design

### Design Considerations
- Core emotion set (joy, sadness, anger, fear, surprise, disgust, trust, anticipation)
- Transition edges with meaningful weights
- Balance between accuracy and complexity
- Psychological validity of emotion transitions

### Key Decisions Needed
- How to represent emotion intensity
- Whether to allow direct transitions between all emotions
- How to determine edge weights based on psychological research
- Whether to include compound emotions

### Success Criteria
- Graph should allow meaningful pathfinding
- Transitions should feel natural to users
- Structure should support percentage completion calculations
- Design should be extensible for future enhancements

## 2. Suggestion Generation Algorithm

### Design Considerations
- Context-awareness based on current and target emotions
- Progression metrics that feel meaningful to users
- Balance between generic and specific suggestions
- Integration with GPT-4o capabilities

### Key Decisions Needed
- How to template suggestions for different emotion transitions
- Whether to use predefined templates or dynamic generation
- How to calculate percentage closer metrics
- How to present multiple suggestion options effectively

### Success Criteria
- Suggestions should feel personalized and helpful
- Progress metrics should accurately reflect path progress
- Multiple suggestion options should provide meaningful choice
- Algorithm should be efficient and minimize API calls

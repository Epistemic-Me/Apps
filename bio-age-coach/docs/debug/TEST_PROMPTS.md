# Test Prompts for Semantic Router

Use these prompts to test the semantic router's ability to route queries to the appropriate agents based on context.

## Sleep Context

- "How did I sleep last night?"
- "What's my average sleep duration?"
- "How can I improve my sleep quality?"
- "Is 7 hours of sleep enough?"
- "What's the relationship between sleep and biological age?"

## Exercise Context

- "How many calories did I burn during my workout?"
- "What's my average step count?"
- "How can I improve my exercise routine?"
- "Is 30 minutes of exercise per day enough?"
- "What's the relationship between exercise and biological age?"

## Nutrition Context

- "What should I eat to reduce my biological age?"
- "How does my diet affect my health?"
- "What are the best foods for longevity?"
- "Should I try intermittent fasting?"
- "How many calories should I consume per day?"

## Biometric Context

- "What's my current weight?"
- "How has my blood pressure changed over time?"
- "Is my heart rate normal?"
- "What's a healthy body fat percentage?"
- "How do my biomarkers compare to others my age?"

## Bio Age Score Context

- "What's my biological age?"
- "How can I reduce my biological age?"
- "What factors affect my biological age the most?"
- "How has my biological age changed over time?"
- "What's the difference between biological age and chronological age?"

## Research Context

- "What does the latest research say about aging?"
- "Are there any new studies on longevity?"
- "What are the most promising anti-aging interventions?"
- "How does telomere length relate to aging?"
- "What is the science behind epigenetic clocks?"

## General Context

- "What is this app for?"
- "How do I use this app?"
- "Can you help me understand my health data?"
- "What features does this app have?"
- "Who created this app?"

## Multi-Context Interactions

- "How does my sleep affect my biological age?"
- "What exercise is best for improving my biomarkers?"
- "Can you analyze my health data and give me recommendations?"
- "How do my diet and exercise habits compare to best practices?"
- "What lifestyle changes would have the biggest impact on my health?"

## Visualization Testing

- "Show me a graph of my sleep over time"
- "Can you visualize my exercise data?"
- "I'd like to see a chart of my biological age trends"
- "Create a visualization of my health metrics"
- "Compare my biomarkers in a visual format"

## Notes

When testing, pay attention to the "Current Context" section in the sidebar. This will show which contexts are active and their relevancy scores. The semantic router should route queries to the agent with the highest relevancy score above the threshold (default 0.5). 
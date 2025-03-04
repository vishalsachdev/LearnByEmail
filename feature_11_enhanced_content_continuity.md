# Enhanced Content Continuity

## Overview
Improve educational value by using the full history of previously sent emails as context when generating new content for a subscription. This ensures that new lessons build upon previous knowledge and creates a more cohesive learning journey.

## Current Limitations
- Currently, only the last 3 emails are used as context (limited in `content_generator.py`)
- No compression or summarization of context, leading to potential token limitations
- No visualization for users to understand progression of learning
- No way for users to see how current content relates to previous lessons

## Implementation Details

### 1. Email History Context Expansion
- Modify `app/services/content_generator.py` to retrieve and use all previous emails for a topic
- Update database queries in `app/services/email_sender.py` to fetch full history
- Add token usage monitoring to track potential API limits
- Implement fallback to limited context if token limits are reached

### 2. Context Compression (Optional Enhancement)
- Create a new function to generate compressed context summaries
- Store both full content and compressed summary in EmailHistory table
- Use compressed summaries when full context would exceed token limits
- Implement periodic background task to generate summaries for existing history

### 3. Learning Journey Visualization
- Add a new API endpoint to view content progression for a subscription
- Create a visual timeline UI component showing lesson progression
- Highlight connections between related concepts across emails
- Allow users to navigate through previous lessons

### 4. Content References
- Enhance email template to include "Previously Covered" section
- Add links to concepts explained in earlier lessons
- Include progress indicators (e.g., "Lesson 5 of your Python journey")

## Database Changes
- Add `summary` column to EmailHistory table (nullable text field)
- Add `sequence_number` column to track lesson order
- Add `builds_on` column to store IDs of related previous emails

## API Endpoints
- `GET /api/subscriptions/{id}/learning-journey` - View progression of content
- `GET /api/subscriptions/{id}/previous-lessons` - Access past lesson content

## UI Changes
- Add Learning Journey tab to subscription details page
- Include content continuity visualization
- Show connections between lessons

## Testing Strategy
- Unit tests for context retrieval and summarization
- Integration tests for content generation with full history
- UI tests for learning journey visualization
- Performance testing with large email histories

## Future Enhancements
- AI-generated learning paths based on topic relationships
- Personalized learning recommendations
- Interactive review quizzes that build on previous content
- Content branching based on user interests within topics
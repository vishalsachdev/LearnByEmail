"""
Mock content generation service implementation.
This service is used as a fallback when no content generation API is available.
"""

from typing import Dict, Any, Optional, List

from app.core.interfaces.service_interfaces import ContentGenerationInterface
from app.core.error_handler import ServiceErrorHandler


class MockContentService(ContentGenerationInterface):
    """
    Mock implementation of the content generation interface.
    
    This service is used as a fallback when no content generation API is available.
    It returns hardcoded content samples for testing purposes.
    """
    
    def __init__(self, error_handler: ServiceErrorHandler):
        """
        Initialize the mock content generation service.
        
        Args:
            error_handler: Error handler for service errors
        """
        self.error_handler = error_handler
        
        # Sample content for different topics and difficulty levels
        self.sample_content = {
            "python:beginner": """
# Introduction to Python

Python is one of the most popular programming languages in the world. It's known for its simplicity and readability, making it an excellent choice for beginners.

## Getting Started

To start using Python, you need to:

1. Install Python from python.org
2. Set up a code editor (like VS Code, PyCharm, or even a simple text editor)
3. Write your first program!

## Your First Program

Here's a simple "Hello, World!" program in Python:

```python
print("Hello, World!")
```

When you run this program, it will display the text "Hello, World!" on your screen.

## What's Next?

In the next lesson, we'll learn about variables and data types in Python.
            """,
            
            "python:intermediate": """
# Python Decorators

Decorators are a powerful feature in Python that allow you to modify the behavior of functions or classes. They are a form of metaprogramming where you can wrap a function to extend its functionality.

## Basic Decorator Structure

```python
def my_decorator(func):
    def wrapper():
        print("Something is happening before the function is called.")
        func()
        print("Something is happening after the function is called.")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

say_hello()
```

This will output:
```
Something is happening before the function is called.
Hello!
Something is happening after the function is called.
```

## Decorators with Arguments

You can also create decorators that accept arguments:

```python
def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def say_hello(name):
    print(f"Hello, {name}!")

say_hello("World")
```

This will print "Hello, World!" three times.

In the next lesson, we'll explore more advanced decorator patterns and use cases.
            """,
            
            "history:beginner": """
# Introduction to World History

History is the study of past events, particularly human affairs. Understanding history helps us make sense of the present and prepare for the future.

## Why Study History?

1. **Learn from the past**: History shows us what strategies worked and what mistakes to avoid.
2. **Understand the present**: Many current conflicts and traditions have roots in historical events.
3. **Appreciate cultural diversity**: History reveals how different societies developed unique ways of life.

## Early Human Civilizations

The first complex human civilizations emerged around 3500-3000 BCE in:

- Mesopotamia (modern Iraq)
- Egypt (along the Nile River)
- Indus Valley (modern Pakistan/India)
- China (along the Yellow River)

These early civilizations developed writing systems, organized governments, and complex religious beliefs.

In our next lesson, we'll explore the ancient Mesopotamian civilization in more detail.
            """
        }
    
    def generate_content(self, 
                        topic: str, 
                        difficulty: str,
                        previous_content: Optional[List[Dict[str, Any]]] = None,
                        lesson_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate mock educational content for a topic.
        
        Args:
            topic: The topic to generate content about
            difficulty: The difficulty level (beginner, intermediate, advanced)
            previous_content: Optional history of previous lessons
            lesson_number: Optional sequential lesson number
            
        Returns:
            Dict containing the generated content and status information
        """
        # Log the request
        self.error_handler.logger.info(
            f"MockContentService: Generating content for {topic} ({difficulty})"
        )
        
        # Normalize topic and difficulty for lookup
        normalized_topic = topic.lower().split()[0]  # Take just the first word
        normalized_difficulty = difficulty.lower()
        
        # Try to find matching content
        key = f"{normalized_topic}:{normalized_difficulty}"
        content = self.sample_content.get(key)
        
        # If no exact match, try with just difficulty
        if not content:
            # Find any topic with the same difficulty
            for sample_key in self.sample_content:
                if sample_key.endswith(f":{normalized_difficulty}"):
                    content = self.sample_content[sample_key]
                    break
        
        # If still no match, use the first available sample
        if not content:
            content = next(iter(self.sample_content.values()))
        
        # Add lesson number if provided
        if lesson_number:
            content = f"# Lesson {lesson_number}\n\n{content}"
        
        return {
            "success": True,
            "content": content,
            "source": "mock"
        }
    
    def generate_preview(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate a mock preview for a topic.
        
        Args:
            topic: The topic to preview
            difficulty: The difficulty level (beginner, intermediate, advanced)
            
        Returns:
            Dict containing the preview content and status information
        """
        # Log the request
        self.error_handler.logger.info(
            f"MockContentService: Generating preview for {topic} ({difficulty})"
        )
        
        # Get full content
        result = self.generate_content(topic, difficulty)
        
        if result["success"]:
            # Extract the first 200 characters as a preview
            full_content = result["content"]
            preview = full_content[:200] + "..." if len(full_content) > 200 else full_content
            
            return {
                "success": True,
                "preview": preview,
                "source": "mock"
            }
        
        return result
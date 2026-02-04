# AI Chatbot Integration Reference

## Table of Contents
- [OpenAI Integration](#openai-integration)
- [Agents SDK](#agents-sdk)
- [RAG Implementation](#rag-implementation)
- [Conversation Management](#conversation-management)
- [API Endpoints](#api-endpoints)

## OpenAI Integration

### Basic Setup
```python
# chatbot/client.py
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat_completion(
    messages: list[dict],
    system_prompt: str | None = None,
    model: str = "gpt-4",
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> str:
    """Generate chat completion response."""
    msgs = []

    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})

    msgs.extend(messages)

    response = client.chat.completions.create(
        model=model,
        messages=msgs,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content
```

### Streaming Response
```python
def stream_chat_completion(
    messages: list[dict],
    system_prompt: str | None = None,
    model: str = "gpt-4"
):
    """Stream chat completion for real-time responses."""
    msgs = []

    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.extend(messages)

    stream = client.chat.completions.create(
        model=model,
        messages=msgs,
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

## Agents SDK

### Agent Definition
```python
# chatbot/agent.py
from openai import OpenAI
from typing import Callable

class TaskAgent:
    """Agent for task management with tool calling."""

    def __init__(self):
        self.client = OpenAI()
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Create a new task for the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Task title"},
                            "description": {"type": "string", "description": "Task description"},
                            "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tasks",
                    "description": "List user's tasks with optional filter",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["pending", "completed", "all"]}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_task",
                    "description": "Mark a task as completed",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string", "description": "Task ID to complete"}
                        },
                        "required": ["task_id"]
                    }
                }
            }
        ]

    def process(self, messages: list[dict], tool_handlers: dict[str, Callable]) -> str:
        """Process messages and handle tool calls."""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        # Handle tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                if function_name in tool_handlers:
                    result = tool_handlers[function_name](**arguments)

                    # Add tool result to conversation
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })

            # Get final response after tool execution
            final_response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            return final_response.choices[0].message.content

        return message.content
```

## RAG Implementation

### Document Embedding
```python
# chatbot/rag.py
from openai import OpenAI
import numpy as np
from typing import List

client = OpenAI()

def create_embedding(text: str) -> List[float]:
    """Create embedding for text using OpenAI."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

### Vector Store (Simple In-Memory)
```python
class SimpleVectorStore:
    """Simple in-memory vector store for RAG."""

    def __init__(self):
        self.documents = []
        self.embeddings = []

    def add_document(self, content: str, metadata: dict = None):
        """Add document with its embedding."""
        embedding = create_embedding(content)
        self.documents.append({
            "content": content,
            "metadata": metadata or {}
        })
        self.embeddings.append(embedding)

    def search(self, query: str, top_k: int = 3) -> List[dict]:
        """Search for most relevant documents."""
        query_embedding = create_embedding(query)

        similarities = [
            cosine_similarity(query_embedding, emb)
            for emb in self.embeddings
        ]

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [
            {**self.documents[i], "score": similarities[i]}
            for i in top_indices
        ]
```

### RAG Chat
```python
def rag_chat(query: str, vector_store: SimpleVectorStore) -> str:
    """RAG-enhanced chat response."""
    # Retrieve relevant documents
    relevant_docs = vector_store.search(query, top_k=3)

    # Build context from documents
    context = "\n\n".join([
        f"Document {i+1}: {doc['content']}"
        for i, doc in enumerate(relevant_docs)
    ])

    system_prompt = f"""You are a helpful assistant. Use the following context to answer questions.

Context:
{context}

If the context doesn't contain relevant information, say so and provide a general response."""

    response = chat_completion(
        messages=[{"role": "user", "content": query}],
        system_prompt=system_prompt
    )

    return response
```

## Conversation Management

### Conversation Store
```python
# chatbot/conversation.py
from sqlmodel import Field, SQLModel, Session
from uuid import UUID, uuid4
from datetime import datetime
from typing import List
import json

class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    title: str = "New Conversation"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversation.id", index=True)
    role: str  # "user", "assistant", "system"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ConversationManager:
    """Manage chat conversations and message history."""

    def __init__(self, session: Session):
        self.session = session

    def create_conversation(self, user_id: UUID) -> Conversation:
        """Create new conversation for user."""
        conversation = Conversation(user_id=user_id)
        self.session.add(conversation)
        self.session.commit()
        self.session.refresh(conversation)
        return conversation

    def add_message(self, conversation_id: UUID, role: str, content: str) -> Message:
        """Add message to conversation."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.session.add(message)
        self.session.commit()
        return message

    def get_history(self, conversation_id: UUID, limit: int = 20) -> List[dict]:
        """Get conversation history as OpenAI message format."""
        messages = self.session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit).all()

        return [
            {"role": m.role, "content": m.content}
            for m in reversed(messages)
        ]
```

## API Endpoints

### Chat Endpoint
```python
# api/chat.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from sqlmodel import Session
from ..database import get_session
from ..middleware.auth import get_current_user
from ..chatbot.client import chat_completion
from ..chatbot.conversation import ConversationManager

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_id: UUID | None = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: UUID

SYSTEM_PROMPT = """You are a helpful task management assistant.
Help users organize their tasks, set priorities, and stay productive.
Be concise and actionable in your responses."""

@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    manager = ConversationManager(session)

    # Get or create conversation
    if request.conversation_id:
        conversation_id = request.conversation_id
    else:
        conversation = manager.create_conversation(current_user.id)
        conversation_id = conversation.id

    # Get conversation history
    history = manager.get_history(conversation_id)

    # Add user message
    history.append({"role": "user", "content": request.message})
    manager.add_message(conversation_id, "user", request.message)

    # Generate response
    response = chat_completion(
        messages=history,
        system_prompt=SYSTEM_PROMPT
    )

    # Save assistant response
    manager.add_message(conversation_id, "assistant", response)

    return ChatResponse(
        response=response,
        conversation_id=conversation_id
    )
```

### Streaming Endpoint
```python
from fastapi.responses import StreamingResponse

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    manager = ConversationManager(session)

    if request.conversation_id:
        conversation_id = request.conversation_id
    else:
        conversation = manager.create_conversation(current_user.id)
        conversation_id = conversation.id

    history = manager.get_history(conversation_id)
    history.append({"role": "user", "content": request.message})
    manager.add_message(conversation_id, "user", request.message)

    def generate():
        full_response = ""
        for chunk in stream_chat_completion(history, SYSTEM_PROMPT):
            full_response += chunk
            yield chunk

        # Save complete response after streaming
        manager.add_message(conversation_id, "assistant", full_response)

    return StreamingResponse(generate(), media_type="text/plain")
```

## Environment Variables

```bash
# Required for chatbot
OPENAI_API_KEY=sk-...

# Optional model configuration
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000
```

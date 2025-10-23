# backend/app/api/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from app.services.mistral_service import get_mistral_service
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

class Course(BaseModel):
    name: str
    code: str
    orgUnitId: Optional[str] = None
    homepage: Optional[str] = None
    gradesUrl: Optional[str] = None
    finalGradeUrl: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    isActive: Optional[bool] = True
    enrollmentUrl: Optional[str] = None
    organizationUrl: Optional[str] = None
    description: Optional[str] = ""
    semester: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    query: str
    context: Dict[str, Any]
    sessionId: str
    conversationHistory: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str
    suggestedActions: Optional[List[Dict[str, str]]] = None
    sessionId: str
    timestamp: str

@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """
    Handle chat queries from the Chrome extension using Mistral AI with conversation history
    """
    try:
        # Extract context
        courses = request.context.get('courses', [])
        current_page = request.context.get('currentPage', {})
        grades = request.context.get('grades', [])
        assignments = request.context.get('assignments', [])
        announcements = request.context.get('announcements', [])
        conversation_history = request.conversationHistory or []
        current_term_only = request.context.get('currentTermOnly', True)
        
        logger.info(f"📥 Received query: {request.query}")
        logger.info(f"📚 Context: {len(courses)} courses, {len(grades)} grade sets, {len(assignments)} assignment sets, {len(announcements)} announcement sets")
        logger.info(f"💬 Conversation history: {len(conversation_history)} messages")
        logger.info(f"🎓 Current term only: {current_term_only}")
        
        # Check if we have any data
        has_data = len(courses) > 0 or len(grades) > 0 or len(assignments) > 0 or len(announcements) > 0
        
        if not has_data and len(conversation_history) == 0:
            # First message and no data - provide helpful onboarding
            response_text = (
                "I don't have any data loaded yet. To get started:\n\n"
                "1. Click ⚙️ (Settings) in the top right\n"
                "2. Click 'Sync All My Courses' to load your course list\n"
                "3. Click 'Fetch All Grades' to get your grades\n"
                "4. Click 'Fetch All Assignments' for upcoming work\n"
                "5. Click 'Fetch All Announcements' for news\n\n"
                "Once loaded, you can ask me questions like:\n"
                "• 'What courses do I have?'\n"
                "• 'What's my CSI2532 grade?'\n"
                "• 'What assignments are due this week?'\n"
                "• 'Any new announcements?'"
            )
            
            return ChatResponse(
                response=response_text,
                suggestedActions=[
                    {
                        "label": "Open Settings",
                        "type": "action",
                        "query": "open_settings"
                    }
                ],
                sessionId=request.sessionId,
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Get Mistral service
        mistral_service = get_mistral_service()
        
        # Build context for Mistral
        context_data = {
            'courses': courses,
            'grades': grades,
            'assignments': assignments,
            'announcements': announcements,
            'currentPage': current_page
        }
        
        # Format conversation history for Mistral
        formatted_history = []
        if conversation_history:
            # Take last 10 messages to avoid token limit
            recent_history = conversation_history[-10:]
            for msg in recent_history:
                formatted_history.append({
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', '')
                })
        
        # Generate AI response using Mistral with conversation history
        logger.info(f"🤖 Calling Mistral AI with {len(formatted_history)} history messages...")
        ai_response = await mistral_service.generate_response(
            query=request.query,
            context=context_data,
            conversation_history=formatted_history
        )
        
        logger.info(f"✅ Generated response ({len(ai_response)} chars)")
        
        # Generate suggested actions based on query and conversation
        suggested_actions = generate_suggested_actions(
            request.query, 
            context_data, 
            conversation_history
        )
        
        return ChatResponse(
            response=ai_response,
            suggestedActions=suggested_actions,
            sessionId=request.sessionId,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

def generate_suggested_actions(
    query: str, 
    context: Dict[str, Any],
    conversation_history: List[Dict[str, str]] = None
) -> List[Dict[str, str]]:
    """
    Generate contextual suggested actions based on the query, context, and conversation flow.
    """
    query_lower = query.lower()
    suggestions = []
    
    # Check conversation context for follow-up suggestions
    has_mentioned_course = False
    mentioned_courses = set()
    
    if conversation_history:
        # Look for course mentions in recent conversation
        recent_messages = conversation_history[-5:]
        for msg in recent_messages:
            content = msg.get('content', '').lower()
            # Simple course code detection (e.g., CSI2532)
            import re
            course_codes = re.findall(r'\b[A-Z]{3,4}\d{4}\b', msg.get('content', ''))
            if course_codes:
                has_mentioned_course = True
                mentioned_courses.update(course_codes)
    
    # Smart follow-up suggestions based on conversation
    if has_mentioned_course and mentioned_courses:
        course = list(mentioned_courses)[0]
        suggestions.append({
            "label": f"What's due in {course}?",
            "type": "query",
            "query": f"What assignments are due soon in {course}?"
        })
        suggestions.append({
            "label": f"Any {course} announcements?",
            "type": "query",
            "query": f"Are there any recent announcements in {course}?"
        })
    
    # Course-related suggestions
    elif 'course' in query_lower:
        if context.get('courses'):
            suggestions.append({
                "label": "Compare Grades",
                "type": "query",
                "query": "Compare my grades across all courses"
            })
            suggestions.append({
                "label": "Upcoming Deadlines",
                "type": "query",
                "query": "What's due in the next 7 days?"
            })
    
    # Grade-related suggestions
    elif 'grade' in query_lower or 'mark' in query_lower:
        suggestions.append({
            "label": "Course Average",
            "type": "query",
            "query": "What's my current average across all courses?"
        })
        suggestions.append({
            "label": "Lowest Grade",
            "type": "query",
            "query": "Which course do I need to focus on?"
        })
    
    # Assignment-related suggestions
    elif 'assignment' in query_lower or 'due' in query_lower:
        suggestions.append({
            "label": "This Week",
            "type": "query",
            "query": "What's due this week?"
        })
        suggestions.append({
            "label": "Next Week",
            "type": "query",
            "query": "What's due next week?"
        })
        suggestions.append({
            "label": "Overdue",
            "type": "query",
            "query": "Do I have any overdue assignments?"
        })
    
    # Announcement-related suggestions
    elif 'announcement' in query_lower or 'news' in query_lower:
        suggestions.append({
            "label": "Latest Updates",
            "type": "query",
            "query": "Show me the 5 most recent announcements"
        })
        suggestions.append({
            "label": "Important News",
            "type": "query",
            "query": "Any important announcements I should know about?"
        })
    
    # Default suggestions if none match
    if not suggestions:
        suggestions = [
            {
                "label": "Check Grades",
                "type": "query",
                "query": "What are my grades?"
            },
            {
                "label": "Upcoming Work",
                "type": "query",
                "query": "What assignments are due soon?"
            },
            {
                "label": "Recent News",
                "type": "query",
                "query": "Any new announcements?"
            }
        ]
    
    return suggestions[:3]  # Limit to 3 suggestions

@router.post("/courses/sync")
async def sync_courses(data: Dict[str, Any]):
    """
    Receive synced courses from the extension
    """
    try:
        courses = data.get('courses', [])
        user_id = data.get('userId', 'unknown')
        session = data.get('session', {})
        
        logger.info(f"📚 Syncing {len(courses)} courses for user {user_id}")
        if session:
            logger.info(f"🔐 Session info received: {session.get('userId')}")
        
        # TODO: Store courses and session in database
        # For now, just acknowledge receipt
        # In production, use PostgreSQL or Redis
        
        return {
            "status": "success",
            "message": f"Successfully synced {len(courses)} courses",
            "courseCount": len(courses),
            "sessionCaptured": bool(session)
        }
        
    except Exception as e:
        logger.error(f"❌ Error syncing courses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-mistral")
async def test_mistral_connection():
    """
    Test endpoint to verify Mistral API is working.
    Visit: http://localhost:8001/api/chat/test-mistral
    """
    import os
    from mistralai import Mistral
    
    result = {
        "checks": [],
        "success": True,
        "errors": []
    }
    
    # Check 1: API Key
    api_key = os.getenv('MISTRAL_API_KEY')
    if api_key:
        result["checks"].append({
            "name": "API Key",
            "status": "✅ Found",
            "details": f"{api_key[:10]}...{api_key[-4:]}"
        })
    else:
        result["checks"].append({
            "name": "API Key",
            "status": "❌ Not Found",
            "details": "MISTRAL_API_KEY not in environment"
        })
        result["success"] = False
        result["errors"].append("API key not found in environment variables")
        return result
    
    # Check 2: Mistral package
    try:
        from mistralai import Mistral
        result["checks"].append({
            "name": "Mistral Package",
            "status": "✅ Installed",
            "details": "mistralai package imported successfully"
        })
    except ImportError as e:
        result["checks"].append({
            "name": "Mistral Package",
            "status": "❌ Not Found",
            "details": str(e)
        })
        result["success"] = False
        result["errors"].append(f"Mistral package not installed: {e}")
        return result
    
    # Check 3: Client initialization
    try:
        client = Mistral(api_key=api_key)
        result["checks"].append({
            "name": "Client Init",
            "status": "✅ Success",
            "details": "Client initialized"
        })
    except Exception as e:
        result["checks"].append({
            "name": "Client Init",
            "status": "❌ Failed",
            "details": str(e)
        })
        result["success"] = False
        result["errors"].append(f"Failed to initialize client: {e}")
        return result
    
    # Check 4: API Call
    try:
        logger.info("🧪 Testing Mistral API call...")
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "user", "content": "Respond with only the word 'SUCCESS'"}
            ],
            max_tokens=10
        )
        
        message = response.choices[0].message.content
        
        result["checks"].append({
            "name": "API Call",
            "status": "✅ Success",
            "details": f"Response: {message}"
        })
        
        result["test_response"] = message
        
    except Exception as e:
        result["checks"].append({
            "name": "API Call",
            "status": "❌ Failed",
            "details": f"{type(e).__name__}: {str(e)}"
        })
        result["success"] = False
        result["errors"].append(f"API call failed: {type(e).__name__}: {str(e)}")
        
        # Add specific guidance based on error
        error_msg = str(e).lower()
        if 'unauthorized' in error_msg or '401' in error_msg:
            result["solution"] = "Your API key is invalid. Get a new one from console.mistral.ai"
        elif 'rate limit' in error_msg or '429' in error_msg:
            result["solution"] = "Rate limit exceeded. Wait a few minutes or upgrade your plan"
        elif 'connection' in error_msg or 'network' in error_msg:
            result["solution"] = "Network error. Check your internet connection and firewall"
        else:
            result["solution"] = "Check the error details above and verify your API key"
    
    return result

@router.get("/ping")
async def ping():
    """Test if the API is responding"""
    return {
        "status": "ok",
        "message": "Backend is running",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the extension to test connectivity
    """
    return {
        "status": "healthy",
        "service": "Brightspace GPT API",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
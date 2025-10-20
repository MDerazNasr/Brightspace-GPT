# backend/app/api/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

router = APIRouter()

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

class ChatRequest(BaseModel):
    query: str
    context: Dict[str, Any]
    sessionId: str

class ChatResponse(BaseModel):
    response: str
    suggestedActions: Optional[List[Dict[str, str]]] = None

@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """
    Handle chat queries from the Chrome extension
    """
    try:
        # Extract context
        courses = request.context.get('courses', [])
        current_page = request.context.get('currentPage', {})
        
        print(f"📥 Received query: {request.query}")
        print(f"📚 Context: {len(courses)} courses")
        
        # Build simple response based on query
        query_lower = request.query.lower()
        
        # Handle different types of queries
        if 'course' in query_lower or 'class' in query_lower or 'what do i have' in query_lower:
            if len(courses) == 0:
                response_text = "I don't see any courses loaded yet. Please click 'Sync All My Courses' to load your course data."
            else:
                response_text = f"You have {len(courses)} courses:\n\n"
                for i, course in enumerate(courses, 1):
                    response_text += f"{i}. {course['name']}\n"
                    response_text += f"   Code: {course['code']}\n"
                    if course.get('semester'):
                        response_text += f"   Semester: {course['semester']}\n"
                    if course.get('homepage'):
                        response_text += f"   Link: {course['homepage']}\n"
                    response_text += "\n"
        
        elif 'grade' in query_lower:
            # Check if we have grades URLs from synced courses
            grades_info = []
            for course in courses:
                if course.get('gradesUrl'):
                    grades_info.append({
                        'course': course['name'],
                        'gradesUrl': course['gradesUrl']
                    })
            
            if grades_info:
                response_text = f"I found grade information for {len(grades_info)} courses:\n\n"
                for info in grades_info:
                    response_text += f"• {info['course']}\n"
                response_text += "\n📊 To see actual grade values, navigate to a course's grades page and I can extract the visible grades.\n\n"
                response_text += "In the future, I'll be able to fetch grades directly using the Brightspace API!"
            else:
                response_text = "I don't have grades data yet. Please sync your courses first, then navigate to a course's grades page so I can extract the information."
        
        elif 'assignment' in query_lower or 'due' in query_lower:
            response_text = "To see your assignments and due dates, please navigate to a course's assignments or dropbox page, and I can extract them for you.\n\n"
            response_text += "In the future, I'll be able to fetch all assignments across all your courses automatically!"
        
        elif 'announcement' in query_lower or 'news' in query_lower:
            response_text = "To see announcements, please navigate to a course's news/announcements page and I can show you the latest updates.\n\n"
            response_text += "I'm working on being able to fetch all announcements automatically!"
        
        elif 'help' in query_lower or 'what can you do' in query_lower:
            response_text = "I'm your Brightspace assistant! Here's what I can help with:\n\n"
            response_text += "📚 **Courses**: Ask 'What courses do I have?' (works now!)\n"
            response_text += "📊 **Grades**: Navigate to grades page, then ask about them\n"
            response_text += "📝 **Assignments**: Navigate to assignments page, then ask about due dates\n"
            response_text += "📢 **Announcements**: Navigate to news page, then ask about updates\n\n"
            response_text += "💡 Tip: Make sure to 'Sync All My Courses' first!"
        
        else:
            response_text = f"I received your question: '{request.query}'\n\n"
            if len(courses) > 0:
                response_text += f"I have data for {len(courses)} courses:\n"
                for course in courses[:3]:
                    response_text += f"• {course['name']}\n"
                if len(courses) > 3:
                    response_text += f"• ... and {len(courses) - 3} more\n"
                response_text += "\n"
            response_text += "You can ask me about:\n"
            response_text += "• Your courses and their details\n"
            response_text += "• Grades (when on a grades page)\n"
            response_text += "• Assignments and due dates (when on assignments page)\n"
            response_text += "• Announcements (when on news page)\n"
        
        return ChatResponse(
            response=response_text,
            suggestedActions=[
                {
                    "label": "View All Courses",
                    "type": "query",
                    "query": "Show me all my courses"
                },
                {
                    "label": "Check Grades",
                    "type": "query",
                    "query": "What are my grades?"
                },
                {
                    "label": "Get Help",
                    "type": "query",
                    "query": "What can you do?"
                }
            ]
        )
        
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses/sync")
async def sync_courses(data: Dict[str, Any]):
    """
    Receive synced courses from the extension
    """
    try:
        courses = data.get('courses', [])
        user_id = data.get('userId', 'unknown')
        session = data.get('session', {})
        
        print(f"📚 Syncing {len(courses)} courses for user {user_id}")
        if session:
            print(f"🔐 Session info received: {session.get('userId')}")
        
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
        print(f"❌ Error syncing courses: {e}")
        raise HTTPException(status_code=500, detail=str(e))
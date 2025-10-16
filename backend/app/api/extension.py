# backend/app/api/extension.py
"""
API endpoints for Chrome extension communication - Phase 1
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Temporary in-memory storage for Phase 1 (use Redis in production)
extension_data_store = {}

@router.post("/process-brightspace-data")
async def process_brightspace_data(data: Dict[str, Any]):
    """
    Process raw Brightspace data from extension - Phase 1 version.
    """
    try:
        logger.info("Received data from extension")
        
        # Basic validation
        if not data:
            raise HTTPException(status_code=400, detail="No data provided")
        
        # Extract basic info
        page_type = data.get('pageType', 'unknown')
        course_id = data.get('courseId')
        items = data.get('items', [])
        data_types = data.get('dataTypes', [])
        
        # Store data temporarily (replace with proper database later)
        storage_key = f"data_{datetime.now().timestamp()}"
        extension_data_store[storage_key] = {
            'raw_data': data,
            'processed_at': datetime.now().isoformat(),
            'page_type': page_type,
            'course_id': course_id,
            'item_count': len(items),
            'data_types': data_types
        }
        
        # Basic processing
        processed_summary = {
            'page_type': page_type,
            'course_id': course_id,
            'data_types_found': data_types,
            'items_extracted': len(items),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add some basic insights
        insights = []
        if 'grades' in data_types:
            grade_items = [item for item in items if item.get('type') == 'grade']
            insights.append(f"Found {len(grade_items)} grade entries")
            
        if 'announcements' in data_types:
            announcement_items = [item for item in items if item.get('type') == 'announcement']
            insights.append(f"Found {len(announcement_items)} announcements")
            
        if 'assignments' in data_types:
            assignment_items = [item for item in items if item.get('type') == 'assignment']
            insights.append(f"Found {len(assignment_items)} assignments")
        
        return {
            "success": True,
            "message": "Data processed successfully",
            "summary": processed_summary,
            "insights": insights,
            "storage_key": storage_key
        }
        
    except Exception as e:
        logger.error(f"Error processing extension data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_extension_data(request: Dict[str, Any]):
    """
    Handle chat queries from extension with Brightspace context - Phase 1.
    """
    try:
        query = request.get('query', '')
        brightspace_data = request.get('brightspace_data')
        user_id = request.get('user_id', 'anonymous')
        
        if not query:
            raise HTTPException(status_code=400, detail="No query provided")
        
        logger.info(f"Chat query from extension: {query}")
        
        # Basic response generation (replace with LLM later)
        response = generate_basic_response(query, brightspace_data)
        
        return {
            "response": response,
            "query": query,
            "context_used": get_context_types(brightspace_data) if brightspace_data else [],
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Error in extension chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-connection")
async def test_extension_connection():
    """
    Simple endpoint to test extension connectivity.
    """
    return {
        "status": "connected",
        "message": "Extension backend connection successful",
        "timestamp": datetime.now().isoformat(),
        "version": "Phase 1 - Development"
    }

@router.get("/stored-data/{storage_key}")
async def get_stored_data(storage_key: str):
    """
    Retrieve stored data by key - for debugging.
    """
    if storage_key in extension_data_store:
        return {
            "success": True,
            "data": extension_data_store[storage_key]
        }
    else:
        raise HTTPException(status_code=404, detail="Data not found")

@router.get("/recent-data")
async def get_recent_data(limit: int = 5):
    """
    Get recent stored data entries - for debugging.
    """
    recent_keys = list(extension_data_store.keys())[-limit:]
    recent_data = []
    
    for key in recent_keys:
        entry = extension_data_store[key]
        recent_data.append({
            "key": key,
            "summary": {
                "page_type": entry.get('page_type'),
                "course_id": entry.get('course_id'),
                "item_count": entry.get('item_count'),
                "processed_at": entry.get('processed_at')
            }
        })
    
    return {
        "success": True,
        "count": len(recent_data),
        "data": recent_data
    }

# Helper functions

def generate_basic_response(query: str, brightspace_data: Optional[Dict[str, Any]]) -> str:
    """
    Generate basic response for Phase 1 - replace with LLM later.
    """
    query_lower = query.lower()
    
    # Check if we have relevant data
    if not brightspace_data or not brightspace_data.get('success'):
        return generate_no_data_response(query_lower)
    
    items = brightspace_data.get('items', [])
    data_types = brightspace_data.get('dataTypes', [])
    page_type = brightspace_data.get('pageType', 'unknown')
    
    # Generate responses based on query type and available data
    if any(word in query_lower for word in ['grade', 'mark', 'score']):
        return generate_grade_response(query_lower, items, data_types)
    
    elif any(word in query_lower for word in ['announcement', 'news', 'update']):
        return generate_announcement_response(query_lower, items, data_types)
    
    elif any(word in query_lower for word in ['assignment', 'due', 'deadline']):
        return generate_assignment_response(query_lower, items, data_types)
    
    elif any(word in query_lower for word in ['tutorial', 'class', 'cancelled']):
        return generate_schedule_response(query_lower, items, data_types)
    
    else:
        return generate_general_response(query_lower, items, data_types, page_type)

def generate_no_data_response(query: str) -> str:
    """Generate response when no Brightspace data is available."""
    return (
        "I don't have access to your current Brightspace data. "
        "Please navigate to the relevant Brightspace page (like grades, announcements, or assignments) "
        "and try your question again. I can help you find information from the page you're currently viewing!"
    )

def generate_grade_response(query: str, items: List[Dict], data_types: List[str]) -> str:
    """Generate response for grade-related queries."""
    if 'grades' not in data_types:
        return (
            "I don't see any grade information on the current page. "
            "Try navigating to your Grades page in Brightspace and ask again!"
        )
    
    grade_items = [item for item in items if item.get('type') == 'grade']
    
    if not grade_items:
        return "I can see this is a grades page, but I couldn't extract specific grade information. The page might still be loading or use a format I don't recognize yet."
    
    response = f"I found {len(grade_items)} grade entries on this page:\n\n"
    
    for i, grade in enumerate(grade_items[:3], 1):  # Show first 3
        assignment = grade.get('assignment', f'Assignment {i}')
        grade_value = grade.get('grade', 'Not graded')
        response += f"• {assignment}: {grade_value}\n"
    
    if len(grade_items) > 3:
        response += f"\n...and {len(grade_items) - 3} more entries."
    
    if 'midterm' in query or 'mid-term' in query:
        midterm_grades = [g for g in grade_items if 'midterm' in g.get('assignment', '').lower()]
        if midterm_grades:
            response += f"\n\n📊 I found {len(midterm_grades)} midterm grade(s)!"
        else:
            response += "\n\n❓ I don't see any midterm grades posted yet."
    
    return response

def generate_announcement_response(query: str, items: List[Dict], data_types: List[str]) -> str:
    """Generate response for announcement-related queries."""
    if 'announcements' not in data_types:
        return (
            "I don't see any announcements on the current page. "
            "Try navigating to the News/Announcements section in your course and ask again!"
        )
    
    announcement_items = [item for item in items if item.get('type') == 'announcement']
    
    if not announcement_items:
        return "I can see this is an announcements page, but couldn't extract specific announcements."
    
    response = f"I found {len(announcement_items)} announcement(s):\n\n"
    
    for i, announcement in enumerate(announcement_items[:2], 1):  # Show first 2
        title = announcement.get('title', f'Announcement {i}')
        content = announcement.get('content', '')[:100]
        response += f"• {title}\n"
        if content:
            response += f"  {content}...\n"
    
    if 'new' in query or 'recent' in query:
        response += "\n💡 These are the most recent announcements I can see on this page."
    
    return response

def generate_assignment_response(query: str, items: List[Dict], data_types: List[str]) -> str:
    """Generate response for assignment-related queries."""
    if 'assignments' not in data_types:
        return (
            "I don't see any assignment information on the current page. "
            "Try navigating to the Assignments or Dropbox section and ask again!"
        )
    
    assignment_items = [item for item in items if item.get('type') == 'assignment']
    
    if not assignment_items:
        return "I can see this is an assignments page, but couldn't extract specific assignment details."
    
    response = f"I found {len(assignment_items)} assignment(s):\n\n"
    
    for i, assignment in enumerate(assignment_items[:3], 1):
        name = assignment.get('name', f'Assignment {i}')
        due_date = assignment.get('dueDate', 'No due date shown')
        status = assignment.get('status', 'Unknown status')
        
        response += f"• {name}\n"
        response += f"  Due: {due_date}\n"
        response += f"  Status: {status}\n\n"
    
    return response

def generate_schedule_response(query: str, items: List[Dict], data_types: List[str]) -> str:
    """Generate response for schedule-related queries."""
    return (
        "I can help with schedule information, but I'll need you to be on a calendar or schedule page in Brightspace. "
        "Try checking the Calendar section or course overview for tutorial and class schedules!"
    )

def generate_general_response(query: str, items: List[Dict], data_types: List[str], page_type: str) -> str:
    """Generate general response based on available data."""
    if not items:
        return (
            f"I can see you're on a {page_type} page in Brightspace, but I couldn't extract specific information. "
            "Try asking about grades, announcements, or assignments, and make sure you're on the relevant page!"
        )
    
    response = f"I can see you're on a {page_type} page with {len(items)} items. "
    
    if data_types:
        response += f"I found: {', '.join(data_types)}. "
    
    response += (
        "Try asking me specific questions like:\n"
        "• 'Are my midterm grades posted?'\n"
        "• 'Any new announcements?'\n"
        "• 'What assignments are due this week?'"
    )
    
    return response

def get_context_types(brightspace_data: Optional[Dict[str, Any]]) -> List[str]:
    """Extract context types from brightspace data."""
    if not brightspace_data:
        return []
    
    return brightspace_data.get('dataTypes', [])
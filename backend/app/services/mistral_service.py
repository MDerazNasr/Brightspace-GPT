# backend/app/services/mistral_service.py

from mistralai import Mistral
from typing import Dict, List, Any
import os

class MistralService:
    """
    Service for interacting with Mistral AI LLM
    """
    
    def __init__(self):
        api_key = os.getenv('MISTRAL_API_KEY')
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable not set")
        
        self.client = Mistral(api_key=api_key)
        self.model = "mistral-small-latest"  # Fast and cost-effective
        # Alternative: "mistral-medium-latest" for better quality
        # Alternative: "mistral-large-latest" for best quality
    
    def build_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build a comprehensive system prompt with all user context
        """
        courses = context.get('courses', [])
        grades = context.get('grades', [])
        assignments = context.get('assignments', [])
        announcements = context.get('announcements', [])
        
        # Build a mapping of orgUnitId to course info for easy lookup
        course_map = {}
        for course in courses:
            org_id = course.get('orgUnitId')
            if org_id:
                # Extract friendly course code from name (e.g., "CSI2532" from "CSI2532[A] Bases de données...")
                name = course.get('name', '')
                friendly_code = name.split('[')[0].strip() if '[' in name else course.get('code', '')
                course_map[org_id] = {
                    'code': friendly_code,
                    'name': name,
                    'fullCode': course.get('code', '')
                }
        
        prompt = """You are an AI assistant for University of Ottawa students using Brightspace. 
You help students with their courses, grades, assignments, and announcements.

CRITICAL FILTERING RULES:
- When user asks about a SPECIFIC course (e.g., "CSI2532", "MAT2777"), show ONLY that course's data
- When user asks for "latest" or "recent", show ONLY the most recent 1-3 items
- When user asks "what's due", show ONLY upcoming items sorted by date
- NEVER dump all data unless explicitly asked for "all" or "everything"
- Use the friendly course codes (CSI2532, MAT2777) not the internal codes

"""
        
        # Add courses info with both codes
        if courses:
            prompt += f"\n## Student's Courses ({len(courses)} total):\n"
            active_courses = [c for c in courses if c.get('isActive')]
            course_list = []
            for course in active_courses[:15]:
                name = course.get('name', 'Unknown')
                friendly_code = name.split('[')[0].strip() if '[' in name else course.get('code', 'N/A')
                internal_code = course.get('code', 'N/A')
                org_id = course.get('orgUnitId', '')
                course_list.append(f"- {friendly_code} (Internal: {internal_code}, OrgID: {org_id}): {name}")
            prompt += "\n".join(course_list)
        
        # Add grades info with friendly course codes
        if grades:
            prompt += f"\n\n## Grades Data:\n"
            for course_grade in grades[:20]:
                if course_grade.get('grades') and len(course_grade['grades']) > 0:
                    org_id = course_grade.get('orgUnitId', '')
                    internal_code = course_grade.get('courseCode', 'N/A')
                    
                    # Get friendly code from course map
                    friendly_code = internal_code
                    course_name = course_grade.get('courseName', 'Unknown')
                    if org_id in course_map:
                        friendly_code = course_map[org_id]['code']
                        course_name = course_map[org_id]['name']
                    
                    prompt += f"\n**{friendly_code}** (Internal: {internal_code}):\n"
                    for grade in course_grade['grades']:
                        grade_info = f"  - {grade['name']}: {grade.get('displayedGrade', 'N/A')}"
                        if grade.get('pointsNumerator') is not None and grade.get('pointsDenominator') is not None:
                            grade_info += f" ({grade['pointsNumerator']}/{grade['pointsDenominator']})"
                        prompt += grade_info + "\n"
        
        # Add assignments with friendly codes
        if assignments:
            prompt += f"\n## Assignments & Due Dates:\n"
            for course_assignments in assignments[:15]:
                org_id = course_assignments.get('orgUnitId', '')
                internal_code = course_assignments.get('courseCode', 'N/A')
                
                # Get friendly code
                friendly_code = internal_code
                if org_id in course_map:
                    friendly_code = course_map[org_id]['code']
                
                if course_assignments.get('assignments') and len(course_assignments['assignments']) > 0:
                    prompt += f"\n**{friendly_code}**:\n"
                    for assignment in course_assignments['assignments'][:5]:
                        assignment_info = f"  - {assignment['name']}"
                        if assignment.get('dueDate'):
                            assignment_info += f" | Due: {assignment['dueDate'][:10]}"
                        prompt += assignment_info + "\n"
        
        # Add announcements with friendly codes
        if announcements:
            prompt += f"\n## Recent Announcements:\n"
            all_announcements = []
            for course_announcements in announcements:
                org_id = course_announcements.get('orgUnitId', '')
                internal_code = course_announcements.get('courseCode', 'N/A')
                
                # Get friendly code
                friendly_code = internal_code
                if org_id in course_map:
                    friendly_code = course_map[org_id]['code']
                
                if course_announcements.get('announcements'):
                    for announcement in course_announcements['announcements']:
                        all_announcements.append({
                            'course': friendly_code,
                            'title': announcement['title'],
                            'date': announcement.get('publishDate', ''),
                            'body': announcement.get('body', '')[:200]
                        })
            
            # Sort by date (most recent first)
            all_announcements.sort(key=lambda x: x['date'], reverse=True)
            
            # Show most recent 10
            for announcement in all_announcements[:10]:
                prompt += f"\n{announcement['course']} | {announcement['date'][:10] if announcement['date'] else 'No date'}:\n"
                prompt += f"  Title: {announcement['title']}\n"
        
        prompt += """

RESPONSE EXAMPLES:
User: "Show me only CSI2532 grades"
You: "Here are your CSI2532 grades:
• Devoir 1: A+
• Mi-Session: A
• Examen Final: D+"

User: "What's the latest announcement?"
You: "The latest announcement is from MAT2777 on 2024-10-15: 'Midterm Results Posted'"

User: "When is MAT2777 homework due?"
You: "MAT2777 assignments:
• Devoir 3: Due October 25, 2024
• Devoir 4: Due November 8, 2024"

REMEMBER: Filter data precisely based on what the user asks!
"""
        
        return prompt
    
    async def generate_response(
        self, 
        query: str, 
        context: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate a response using Mistral AI
        
        Args:
            query: The user's question
            context: Dictionary containing courses, grades, assignments, announcements
            conversation_history: Optional list of previous messages
            
        Returns:
            AI-generated response string
        """
        try:
            # Build system prompt with context
            system_prompt = self.build_system_prompt(context)
            
            # Build message list
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            # Determine temperature based on query type
            query_lower = query.lower()
            
            # Factual queries need low temperature (more precise)
            if any(word in query_lower for word in ['when', 'what', 'which', 'latest', 'recent', 'due', 'grade', 'announcement']):
                temperature = 0.3  # Very precise for factual queries
            # Advisory queries can be more creative
            elif any(word in query_lower for word in ['should', 'recommend', 'suggest', 'advice', 'help', 'how']):
                temperature = 0.7  # More creative for advice
            else:
                temperature = 0.5  # Balanced
            
            # Call Mistral API
            print(f"🤖 Calling Mistral API with query: {query} (temp: {temperature})")
            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            print(f"✅ Mistral response generated ({len(ai_response)} chars)")
            
            return ai_response
            
        except Exception as e:
            print(f"❌ Error calling Mistral API: {e}")
            return f"I apologize, but I encountered an error processing your question: {str(e)}"
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimation of tokens (for monitoring costs)
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4

# Global instance
mistral_service = None

def get_mistral_service() -> MistralService:
    """
    Get or create Mistral service instance
    """
    global mistral_service
    if mistral_service is None:
        mistral_service = MistralService()
    return mistral_service
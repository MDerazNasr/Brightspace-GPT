# backend/app/services/mistral_service.py

from mistralai import Mistral
from typing import Dict, List, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

class MistralService:
    """
    Service for interacting with Mistral AI LLM with conversation history and smart filtering
    """
    
    def __init__(self):
        api_key = os.getenv('MISTRAL_API_KEY')
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable not set")
        
        self.client = Mistral(api_key=api_key)
        # Use mistral-small for cost-effectiveness, or switch to mistral-large for better quality
        self.model = os.getenv('MISTRAL_MODEL', "mistral-small-latest")
        logger.info(f"🤖 Initialized Mistral service with model: {self.model}")
    
    def filter_relevant_data(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-filter context to only include data relevant to the query.
        This reduces token usage and improves response quality.
        """
        query_lower = query.lower()
        filtered_context = {}
        
        # Extract course-specific queries (e.g., "CSI2532", "MAT2777")
        mentioned_courses = self._extract_course_codes(query_lower, context.get('courses', []))
        
        # Filter courses
        courses = context.get('courses', [])
        if mentioned_courses:
            # Only include mentioned courses
            filtered_context['courses'] = [
                c for c in courses 
                if any(code.lower() in c.get('code', '').lower() or 
                       code.lower() in c.get('name', '').lower() 
                       for code in mentioned_courses)
            ]
            logger.info(f"📊 Filtered to {len(filtered_context['courses'])} relevant courses")
        elif 'course' in query_lower or 'class' in query_lower:
            # Show all courses if asking generally
            filtered_context['courses'] = courses[:20]  # Limit to 20 most recent
        else:
            # Include minimal course info for context
            filtered_context['courses'] = courses[:5]
        
        # Filter grades
        grades = context.get('grades', [])
        if 'grade' in query_lower or 'mark' in query_lower or 'score' in query_lower:
            if mentioned_courses:
                filtered_context['grades'] = [
                    g for g in grades 
                    if any(code.lower() in g.get('courseCode', '').lower() 
                           for code in mentioned_courses)
                ]
            else:
                filtered_context['grades'] = grades[:10]  # Limit to 10 courses
        elif mentioned_courses:
            # Include grades for mentioned courses even if not explicitly asked
            filtered_context['grades'] = [
                g for g in grades 
                if any(code.lower() in g.get('courseCode', '').lower() 
                       for code in mentioned_courses)
            ]
        
        # Filter assignments
        assignments = context.get('assignments', [])
        if 'assignment' in query_lower or 'due' in query_lower or 'deadline' in query_lower:
            if mentioned_courses:
                filtered_context['assignments'] = [
                    a for a in assignments 
                    if any(code.lower() in a.get('courseCode', '').lower() 
                           for code in mentioned_courses)
                ]
            elif 'upcoming' in query_lower or 'soon' in query_lower or 'week' in query_lower:
                # Filter to upcoming assignments only
                filtered_context['assignments'] = self._filter_upcoming_assignments(assignments)
            else:
                filtered_context['assignments'] = assignments[:10]
        
        # Filter announcements
        announcements = context.get('announcements', [])
        if 'announcement' in query_lower or 'news' in query_lower or 'latest' in query_lower:
            if mentioned_courses:
                filtered_context['announcements'] = [
                    a for a in announcements 
                    if any(code.lower() in a.get('courseCode', '').lower() 
                           for code in mentioned_courses)
                ]
            elif 'latest' in query_lower or 'recent' in query_lower:
                # Only show most recent 5 announcements
                all_announcements = []
                for course_ann in announcements:
                    if course_ann.get('announcements'):
                        all_announcements.extend([
                            {**ann, 'courseCode': course_ann.get('courseCode')}
                            for ann in course_ann['announcements']
                        ])
                # Sort by date and take top 5
                all_announcements.sort(key=lambda x: x.get('publishDate', ''), reverse=True)
                filtered_context['announcements'] = all_announcements[:5]
            else:
                filtered_context['announcements'] = announcements[:5]
        
        # Log filtering results
        total_items = sum(len(v) if isinstance(v, list) else 1 for v in filtered_context.values())
        logger.info(f"📉 Filtered context: {total_items} items from {len(courses) + len(grades) + len(assignments) + len(announcements)} total")
        
        return filtered_context
    
    def _extract_course_codes(self, query: str, courses: List[Dict]) -> List[str]:
        """
        Extract course codes mentioned in the query.
        Examples: CSI2532, MAT2777, ITI1121
        """
        import re
        
        # Pattern for course codes (3-4 letters followed by 4 digits)
        pattern = r'\b[A-Z]{3,4}\d{4}\b'
        matches = re.findall(pattern, query.upper())
        
        # Also check for partial matches in course names
        query_words = query.split()
        for word in query_words:
            word_upper = word.upper()
            for course in courses:
                course_name = course.get('name', '')
                course_code = course.get('code', '')
                # Extract friendly code (e.g., "CSI2532" from "CSI2532[A] Bases de données...")
                friendly_code = course_name.split('[')[0].strip()
                
                if word_upper in course_code.upper() or word_upper in friendly_code.upper():
                    matches.append(friendly_code)
        
        return list(set(matches))  # Remove duplicates
    
    def _filter_upcoming_assignments(self, assignments: List[Dict], days: int = 14) -> List[Dict]:
        """
        Filter assignments to only upcoming ones in the next N days.
        """
        from datetime import datetime, timedelta
        
        upcoming = []
        cutoff_date = datetime.now() + timedelta(days=days)
        
        for course_assignments in assignments:
            if not course_assignments.get('assignments'):
                continue
                
            filtered_assignments = []
            for assignment in course_assignments['assignments']:
                due_date_str = assignment.get('dueDate')
                if due_date_str:
                    try:
                        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                        if datetime.now() <= due_date <= cutoff_date:
                            filtered_assignments.append(assignment)
                    except:
                        pass  # Skip if date parsing fails
            
            if filtered_assignments:
                upcoming.append({
                    **course_assignments,
                    'assignments': filtered_assignments
                })
        
        return upcoming
    
    def build_system_prompt(self, context: Dict[str, Any], has_history: bool = False) -> str:
        """
        Build a comprehensive system prompt with filtered context.
        """
        courses = context.get('courses', [])
        grades = context.get('grades', [])
        assignments = context.get('assignments', [])
        announcements = context.get('announcements', [])
        current_term_only = context.get('currentTermOnly', True)
        
        # Build a mapping of orgUnitId to course info
        course_map = {}
        for course in courses:
            org_id = course.get('orgUnitId')
            if org_id:
                name = course.get('name', '')
                friendly_code = name.split('[')[0].strip() if '[' in name else course.get('code', '')
                course_map[org_id] = {
                    'code': friendly_code,
                    'name': name,
                    'fullCode': course.get('code', '')
                }
        
        prompt = f"""You are a helpful AI assistant for University of Ottawa students using Brightspace.
You help students understand their courses, grades, assignments, and announcements.

{"🎓 IMPORTANT: Only showing CURRENT TERM courses (last 4 months). Past courses are filtered out unless specifically requested." if current_term_only else ""}

🎯 CRITICAL RESPONSE RULES:
1. BE CONVERSATIONAL: You're having a natural conversation with the student
2. BE SPECIFIC: When user asks about a specific course, show ONLY that course's data
3. BE CONCISE: Give focused answers unless asked for comprehensive details
4. BE CONTEXTUAL: Remember what was discussed earlier in the conversation
5. BE HELPFUL: If data is missing, tell them how to get it
6. BE ACCURATE: Only state facts from the provided data
7. USE FRIENDLY CODES: Always use course codes like "CSI2532" not internal IDs
8. ACKNOWLEDGE CONTEXT: Reference previous questions naturally when relevant

"""
        
        # Add conversation context note if we have history
        if has_history:
            prompt += """
💬 CONVERSATION CONTEXT:
- This is an ongoing conversation - reference previous messages when relevant
- Use phrases like "As I mentioned..." or "Building on that..." to maintain flow
- If the user asks a follow-up question, understand it in context of what was discussed
- Be natural and conversational, not robotic

"""
        
        prompt += """
❌ NEVER:
- Dump all data unless explicitly asked for "all" or "everything"
- Make up information not in the provided data
- Use technical IDs or internal codes in responses
- Give overly long responses for simple questions
- Ignore the conversation context

"""
        
        # Add courses info
        if courses:
            prompt += f"\n## Student's Enrolled Courses ({len(courses)} total):\n"
            for course in courses:
                name = course.get('name', 'Unknown')
                friendly_code = name.split('[')[0].strip() if '[' in name else course.get('code', 'N/A')
                org_id = course.get('orgUnitId', '')
                prompt += f"- {friendly_code} (OrgID: {org_id}): {name}\n"
        
        # Add grades info
        if grades:
            prompt += f"\n## Grades Data ({len(grades)} courses):\n"
            for course_grade in grades:
                if course_grade.get('grades') and len(course_grade['grades']) > 0:
                    org_id = course_grade.get('orgUnitId', '')
                    internal_code = course_grade.get('courseCode', 'N/A')
                    
                    # Get friendly code
                    friendly_code = internal_code
                    if org_id in course_map:
                        friendly_code = course_map[org_id]['code']
                    
                    prompt += f"\n**{friendly_code}**:\n"
                    for grade in course_grade['grades'][:10]:  # Limit to 10 per course
                        grade_info = f"  - {grade['name']}: {grade.get('displayedGrade', 'N/A')}"
                        if grade.get('pointsNumerator') is not None and grade.get('pointsDenominator') is not None:
                            grade_info += f" ({grade['pointsNumerator']}/{grade['pointsDenominator']})"
                        prompt += grade_info + "\n"
        
        # Add assignments
        if assignments:
            prompt += f"\n## Assignments & Due Dates ({len(assignments)} courses):\n"
            for course_assignments in assignments:
                org_id = course_assignments.get('orgUnitId', '')
                internal_code = course_assignments.get('courseCode', 'N/A')
                
                friendly_code = internal_code
                if org_id in course_map:
                    friendly_code = course_map[org_id]['code']
                
                if course_assignments.get('assignments'):
                    prompt += f"\n**{friendly_code}**:\n"
                    for assignment in course_assignments['assignments'][:5]:
                        assignment_info = f"  - {assignment['name']}"
                        if assignment.get('dueDate'):
                            due_date = assignment['dueDate'][:10]  # Just the date
                            assignment_info += f" | Due: {due_date}"
                        prompt += assignment_info + "\n"
        
        # Add announcements
        if announcements:
            # Handle both formats: list of announcements or list of course-announcements
            if isinstance(announcements, list) and announcements:
                if isinstance(announcements[0], dict) and 'courseCode' in announcements[0]:
                    # Already flattened
                    prompt += f"\n## Recent Announcements ({len(announcements)} total):\n"
                    for ann in announcements[:10]:
                        prompt += f"\n{ann.get('courseCode', 'Unknown')} | {ann.get('publishDate', '')[:10]}:\n"
                        prompt += f"  {ann.get('title', 'No title')}\n"
                else:
                    # Grouped by course
                    prompt += f"\n## Recent Announcements ({len(announcements)} courses):\n"
                    for course_ann in announcements:
                        if course_ann.get('announcements'):
                            friendly_code = course_ann.get('courseCode', 'Unknown')
                            for ann in course_ann['announcements'][:3]:
                                prompt += f"\n{friendly_code} | {ann.get('publishDate', '')[:10]}:\n"
                                prompt += f"  {ann.get('title', 'No title')}\n"
        
        prompt += """

📝 CONVERSATION STYLE:

Be natural and conversational. Examples:

User: "What's my grade in CSI2532?"
You: "Here are your CSI2532 grades:
• Devoir 1: A+ (9.5/10)
• Mi-Session: A (85/100)
• Examen Final: D+ (55/100)"

User: "How about the other assignments?"
You: "Looking at your other CSI2532 assignments:
• Devoir 2: B+ (8/10)
• Devoir 3: A (9/10)
You're doing well overall!"

User: "What's due this week?"
You: "You have 2 assignments due this week:

**CSI2532**:
• Devoir 3 - Due: Oct 25, 2024

**MAT2777**:
• Problem Set 5 - Due: Oct 27, 2024"

User: "When's the CSI2532 one due exactly?"
You: "Your CSI2532 Devoir 3 is due on October 25, 2024."

Remember: Be helpful, conversational, and context-aware!
"""
        
        return prompt
    
    async def generate_response(
        self, 
        query: str, 
        context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a response using Mistral AI with conversation history.
        """
        try:
            # Pre-filter context to reduce tokens and improve responses
            filtered_context = self.filter_relevant_data(query, context)
            
            # Add the currentTermOnly flag to filtered context
            if 'currentTermOnly' in context:
                filtered_context['currentTermOnly'] = context['currentTermOnly']
            
            # Build system prompt with filtered context
            has_history = conversation_history and len(conversation_history) > 0
            system_prompt = self.build_system_prompt(filtered_context, has_history)
            
            # Build message list
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            # Determine temperature based on query type
            temperature = self._determine_temperature(query)
            
            # Log request details
            total_tokens = self.estimate_tokens(system_prompt + query + 
                                               str(conversation_history) if conversation_history else '')
            logger.info(f"🤖 Calling Mistral API (model: {self.model}, temp: {temperature}, est. tokens: {total_tokens})")
            
            # Call Mistral API
            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            logger.info(f"✅ Mistral response generated ({len(ai_response)} chars)")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ Error calling Mistral API: {e}", exc_info=True)
            # Return a helpful error message
            return (
                "I apologize, but I encountered an error processing your question. "
                "This could be due to:\n"
                "• API connectivity issues\n"
                "• Rate limiting\n"
                "• Invalid API key\n\n"
                "Please try again in a moment, or contact support if the issue persists."
            )
    
    def _determine_temperature(self, query: str) -> float:
        """
        Determine optimal temperature based on query type.
        Lower = more precise, Higher = more creative
        """
        query_lower = query.lower()
        
        # Factual queries need low temperature (more precise)
        factual_keywords = ['when', 'what', 'which', 'latest', 'recent', 'due', 
                           'grade', 'announcement', 'how many', 'list', 'show']
        if any(word in query_lower for word in factual_keywords):
            return 0.2  # Very precise
        
        # Advisory queries can be more creative
        advisory_keywords = ['should', 'recommend', 'suggest', 'advice', 
                            'help', 'how to', 'what if', 'strategy']
        if any(word in query_lower for word in advisory_keywords):
            return 0.7  # More creative
        
        # Default balanced temperature
        return 0.4
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimation of tokens (for monitoring costs).
        1 token ≈ 4 characters for English text
        """
        return len(text) // 4

# Global instance
_mistral_service = None

def get_mistral_service() -> MistralService:
    """
    Get or create Mistral service instance (singleton pattern).
    """
    global _mistral_service
    if _mistral_service is None:
        _mistral_service = MistralService()
    return _mistral_service
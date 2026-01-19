from typing import Dict, Optional, List
from dataclasses import dataclass, field
import uuid
from datetime import datetime

@dataclass
class ResumeState:
    """State for resume building workflow"""
    session_id: str = ""
    messages: List = field(default_factory=list)
    name: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    summary: Optional[str] = None
    education: Optional[List[Dict]] = None
    skills: Optional[Dict] = None
    experience: Optional[List[Dict]] = None
    projects: Optional[List[Dict]] = None
    achievements: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    current_field: Optional[str] = None
    intent: Optional[str] = None
    resume_complete: bool = False

# Session storage (in production, use database)
sessions: Dict[str, ResumeState] = {}

class ResumeWorkflow:
    """Resume building workflow using state machine pattern"""
    
    def __init__(self):
        pass
    
    def _detect_intent(self, message: str) -> str:
        """Detect if user wants resume help or career guidance"""
        message_lower = message.lower()
        if any(word in message_lower for word in ["career", "path", "guidance", "advice", "what should"]):
            return "career_guidance"
        return "resume"
    
    def _get_next_field(self, state: ResumeState) -> Optional[str]:
        """Determine next field to collect"""
        if not state.name:
            return "name"
        if not state.email:
            return "email"
        if not state.linkedin and not state.portfolio:
            return "linkedin"
        if not state.summary:
            return "summary"
        if not state.education:
            return "education"
        if not state.skills:
            return "skills"
        if not state.experience:
            return "experience"
        if not state.projects:
            return "projects"
        if not state.achievements and not state.certifications:
            return "achievements"
        return None
    
    def _get_prompt_for_field(self, field: str) -> str:
        """Get prompt message for a field"""
        prompts = {
            "name": "Hello! I'm here to help you create a professional resume. Let's start with the basics.\n\n**What is your full name?**",
            "email": "Great! Now, let's add your contact information.\n\n**What is your email address?**",
            "linkedin": "Good! Do you have a LinkedIn profile or portfolio website? Please share the link (or type 'skip' if you don't have one).",
            "summary": "Perfect! Now, let's create a compelling career summary.\n\n**Please provide a 2-3 line career summary or objective.**\nThis should highlight your career goals and key strengths.",
            "education": "Excellent! Let's add your educational background.\n\n**Please provide your education details:**\n- Degree (e.g., B.Tech Computer Science)\n- College/University name\n- Graduation year (or expected)\n- Grade/CGPA (if applicable)\n\nYou can provide this in any format, and I'll structure it properly.",
            "skills": "Great! Now let's list your skills.\n\n**Please provide your skills separated by commas.**\nInclude both technical skills (programming languages, tools, technologies) and soft skills (communication, teamwork, etc.)\n\nExample: Python, JavaScript, React, Communication, Problem Solving",
            "experience": "Let's add your work experience or internships.\n\n**Please provide your experience details:**\n- Job/Internship title\n- Company name\n- Duration (e.g., June 2023 - August 2023)\n- Key achievements or responsibilities (bullet points)\n\nIf you have multiple experiences, list them all. Type 'none' if you don't have any experience yet.",
            "projects": "Now let's add your projects.\n\n**Please provide your project details:**\n- Project name\n- Technologies/tools used\n- Brief description (1-2 lines)\n\nList all relevant projects. Type 'none' if you don't have any projects to mention.",
            "achievements": "Finally, let's add your achievements and certifications.\n\n**Please provide:**\n- Any notable achievements, awards, or honors\n- Certifications (with issuing organization if applicable)\n\nList them separated by commas or new lines. Type 'none' if you don't have any."
        }
        return prompts.get(field, "Please provide the required information.")
    
    def _extract_field_value(self, message: str, field: str) -> Optional[str]:
        """Extract field value from user message"""
        message_clean = message.strip()
        message_lower = message_clean.lower()
        
        if message_lower == "skip" or message_lower == "none":
            return None
        
        # For email validation
        if field == "email" and "@" in message_clean:
            return message_clean.lower()
        
        # For URLs (LinkedIn/Portfolio)
        if field == "linkedin":
            if "http" in message_lower or "linkedin.com" in message_lower or "github.com" in message_lower or "portfolio" in message_lower:
                if not message_clean.startswith("http"):
                    return f"https://{message_clean}"
                return message_clean
            if message_lower == "skip":
                return None
        
        # For other fields, return as-is (but not if empty)
        return message_clean if message_clean and message_lower != "none" else None
    
    async def process_message(self, message: str, session_id: str, intent: Optional[str] = None) -> Dict:
        """Process incoming chat message"""
        # Get or create session
        if session_id not in sessions:
            sessions[session_id] = ResumeState(
                session_id=session_id,
                messages=[],
                intent=intent or self._detect_intent(message)
            )
        
        state = sessions[session_id]
        
        # Store user message
        state.messages.append({"role": "user", "content": message})
        
        # If intent is career guidance, return early
        if state.intent == "career_guidance":
            response_msg = "I see you're looking for career guidance. Please use the career guidance feature for personalized career suggestions based on your skills and interests."
            state.messages.append({"role": "assistant", "content": response_msg})
            return {
                "message": response_msg,
                "intent": state.intent,
                "resume_complete": False,
                "missing_fields": [],
                "state": None
            }
        
        # Extract information from current message based on current field
        if state.current_field:
            value = self._extract_field_value(message, state.current_field)
            
            if state.current_field == "name":
                state.name = value if value else None
                state.current_field = None
            elif state.current_field == "email":
                state.email = value if value else None
                state.current_field = None
            elif state.current_field == "linkedin":
                if value:
                    if "linkedin" in message.lower():
                        state.linkedin = value
                    elif "github" in message.lower() or "portfolio" in message.lower() or "http" in message.lower():
                        state.portfolio = value
                state.current_field = None
            elif state.current_field == "summary":
                state.summary = value if value else None
                state.current_field = None
            elif state.current_field == "education":
                if value:
                    state.education = [{"details": message}] if not state.education else state.education + [{"details": message}]
                state.current_field = None
            elif state.current_field == "skills":
                if value:
                    skills_list = [s.strip() for s in message.split(",")]
                    technical = []
                    soft = []
                    soft_keywords = ["communication", "teamwork", "leadership", "problem solving", "time management", "adaptability", "collaboration"]
                    for skill in skills_list:
                        skill_lower = skill.lower()
                        if any(keyword in skill_lower for keyword in soft_keywords):
                            soft.append(skill.strip())
                        else:
                            technical.append(skill.strip())
                    state.skills = {"technical": technical if technical else [], "soft": soft if soft else []}
                state.current_field = None
            elif state.current_field == "experience":
                if value:
                    state.experience = [{"details": message}] if not state.experience else state.experience + [{"details": message}]
                state.current_field = None
            elif state.current_field == "projects":
                if value:
                    state.projects = [{"details": message}] if not state.projects else state.projects + [{"details": message}]
                state.current_field = None
            elif state.current_field == "achievements":
                if value:
                    items = [item.strip() for item in message.split(",") if item.strip()]
                    achievements = []
                    certifications = []
                    cert_keywords = ["certificate", "certification", "certified", "course"]
                    for item in items:
                        if any(keyword in item.lower() for keyword in cert_keywords):
                            certifications.append(item)
                        else:
                            achievements.append(item)
                    state.achievements = achievements if achievements else []
                    state.certifications = certifications if certifications else []
                state.current_field = None
        
        # Get next field to collect
        next_field = self._get_next_field(state)
        
        # Check if resume is complete
        if next_field is None:
            state.resume_complete = True
            response_msg = "Perfect! I have all the information I need. Your resume is ready! 🎉\n\nYou can now view and export your resume as PDF."
        else:
            state.current_field = next_field
            response_msg = self._get_prompt_for_field(next_field)
        
        state.messages.append({"role": "assistant", "content": response_msg})
        
        # Determine missing fields
        missing_fields = []
        if not state.name:
            missing_fields.append("name")
        if not state.email:
            missing_fields.append("email")
        if not state.summary:
            missing_fields.append("summary")
        if not state.education:
            missing_fields.append("education")
        if not state.skills:
            missing_fields.append("skills")
        if not state.experience:
            missing_fields.append("experience")
        if not state.projects:
            missing_fields.append("projects")
        if not state.achievements and not state.certifications:
            missing_fields.append("achievements")
        
        return {
            "message": response_msg,
            "intent": state.intent,
            "resume_complete": state.resume_complete,
            "missing_fields": missing_fields,
            "state": state.current_field
        }
    
    async def get_resume(self, session_id: str) -> Optional[Dict]:
        """Get resume data for a session"""
        if session_id not in sessions:
            return None
        
        state = sessions[session_id]
        return {
            "name": state.name,
            "email": state.email,
            "linkedin": state.linkedin,
            "portfolio": state.portfolio,
            "summary": state.summary,
            "education": state.education,
            "skills": state.skills,
            "experience": state.experience,
            "projects": state.projects,
            "achievements": state.achievements,
            "certifications": state.certifications,
            "resume_complete": state.resume_complete
        }
    
    async def generate_polished_resume(self, resume_data: Dict, session_id: str) -> str:
        """Generate polished HTML resume"""
        from resume_generator import ResumeGenerator
        generator = ResumeGenerator()
        return generator.generate_html(resume_data)
    
    async def clear_session(self, session_id: str):
        """Clear session data"""
        if session_id in sessions:
            del sessions[session_id]

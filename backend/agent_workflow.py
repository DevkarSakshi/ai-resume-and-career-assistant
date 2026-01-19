"""
AI Agent Workflow - LangGraph-inspired State Machine
Implements agentic behavior for Resume & Career Assistant
"""
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import os
import uuid
from datetime import datetime
from typing import Any

# ==================== ENUMS ====================
class AgentState(Enum):
    """Agent workflow states"""
    START = "start"
    INTENT = "intent"
    RESUME_COLLECTION = "resume_collection"
    CAREER_COLLECTION = "career_collection"
    RESUME_OUTPUT = "resume_output"
    CAREER_OUTPUT = "career_output"
    COMPLETE = "complete"

class Intent(Enum):
    """User intent types"""
    RESUME = "resume"
    CAREER = "career"
    UNKNOWN = "unknown"

# ==================== DATA CLASS ====================
@dataclass
class AgentStateData:
    """State data for agent workflow"""
    session_id: str = ""
    current_state: AgentState = AgentState.START
    intent: Optional[Intent] = None

    # Resume collection fields
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

    # Career guidance fields
    career_skills: Optional[List[str]] = None
    career_interests: Optional[List[str]] = None
    career_education: Optional[str] = None

    # Conversation tracking
    messages: List[Dict] = field(default_factory=list)
    current_field: Optional[str] = None
    resume_complete: bool = False
    career_complete: bool = False

# Session storage (in production, use database)
sessions: Dict[str, AgentStateData] = {}

# ==================== AGENT WORKFLOW ====================
class AgentWorkflow:
    """
    LangGraph-inspired agent workflow
    Implements: start_node → intent_node → resume_node/career_node → output_node
    """

    RESUME_FIELDS = [
        "name", "email", "linkedin", "summary", "education",
        "skills", "experience", "projects", "achievements"
    ]

    CAREER_FIELDS = [
        "skills", "interests", "education"
    ]

    def __init__(self):
        pass

    def _get_session(self, session_id: str) -> AgentStateData:
        if session_id not in sessions:
            sessions[session_id] = AgentStateData(session_id=session_id)
        return sessions[session_id]

    # ==================== NODE: START ====================
    async def start_node(self, session_id: str, message: str) -> Dict:
        state = self._get_session(session_id)
        if state.current_state == AgentState.START:
            greeting = (
                "Hello! 👋 I'm your AI Resume & Career Assistant, aligned with SDG 8 "
                "(Decent Work & Economic Growth).\n\n"
                "I can help you with:\n"
                "• **Resume Building**: Create a professional resume step-by-step\n"
                "• **Career Guidance**: Get personalized career path recommendations\n\n"
                "What would you like help with today? Please say 'Resume' or 'Career Guidance'."
            )
            state.messages.append({"role": "user", "content": message})
            state.messages.append({"role": "assistant", "content": greeting})
            state.current_state = AgentState.INTENT
            return {"message": greeting, "state": "intent", "intent": None,
                    "resume_complete": False, "career_complete": False}
        return await self.intent_node(session_id, message)

    # ==================== NODE: INTENT ====================
    async def intent_node(self, session_id: str, message: str) -> Dict:
        state = self._get_session(session_id)
        message_lower = message.lower().strip()

        if any(k in message_lower for k in ["resume", "cv", "create resume", "build resume", "make resume"]):
            intent = Intent.RESUME
            next_state = AgentState.RESUME_COLLECTION
        elif any(k in message_lower for k in ["career", "guidance", "advice", "path", "what should", "recommendation"]):
            intent = Intent.CAREER
            next_state = AgentState.CAREER_COLLECTION
        else:
            response = (
                "I'd like to help you! Could you please clarify:\n"
                "• Type **'Resume'** if you want to build a resume\n"
                "• Type **'Career'** if you want career guidance\n\n"
                "What would you like to do?"
            )
            state.messages.append({"role": "user", "content": message})
            state.messages.append({"role": "assistant", "content": response})
            return {"message": response, "state": "intent", "intent": None,
                    "resume_complete": False, "career_complete": False}

        state.intent = intent
        state.current_state = next_state
        state.messages.append({"role": "user", "content": message})

        if intent == Intent.RESUME:
            return await self.resume_node(session_id, message)
        else:
            return await self.career_node(session_id, message)

    # ==================== NODE: RESUME COLLECTION ====================
    async def resume_node(self, session_id: str, message: str) -> Dict:
        state = self._get_session(session_id)
        if state.current_field:
            self._store_resume_field(state, state.current_field, message)
            state.current_field = None

        next_field = self._get_next_resume_field(state)
        if next_field is None:
            state.current_state = AgentState.RESUME_OUTPUT
            return await self.output_node(session_id, "")

        state.current_field = next_field
        prompt = self._get_resume_prompt(next_field)
        state.messages.append({"role": "assistant", "content": prompt})
        return {"message": prompt, "state": "resume_collection", "intent": "resume",
                "resume_complete": False, "career_complete": False, "current_field": next_field}

    # ==================== NODE: CAREER COLLECTION ====================
    async def career_node(self, session_id: str, message: str) -> Dict:
        state = self._get_session(session_id)
        if state.current_field:
            self._store_career_field(state, state.current_field, message)
            state.current_field = None

        next_field = self._get_next_career_field(state)
        if next_field is None:
            state.current_state = AgentState.CAREER_OUTPUT
            return await self.output_node(session_id, "")

        state.current_field = next_field
        prompt = self._get_career_prompt(next_field)
        state.messages.append({"role": "assistant", "content": prompt})
        return {"message": prompt, "state": "career_collection", "intent": "career",
                "resume_complete": False, "career_complete": False, "current_field": next_field}

    # ==================== NODE: OUTPUT ====================
    async def output_node(self, session_id: str, message: str) -> Dict:
        state = self._get_session(session_id)

        # ---------- RESUME PDF GENERATION ----------
        if state.current_state == AgentState.RESUME_OUTPUT:
            from resume_generator import ResumeGenerator
            resume_gen = ResumeGenerator()

            resume_data = {
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
            }

            pdf_file = f"generated_resumes/{state.session_id}_resume.pdf"
            resume_gen.generate_pdf(resume_data, output_file=pdf_file)

            state.resume_complete = True
            state.current_state = AgentState.COMPLETE

            response_msg = f"🎉 **Perfect! I have all the information I need.**\n\nYour professional resume has been generated: `{pdf_file}`"
            state.messages.append({"role": "assistant", "content": response_msg})

            return {
                "message": response_msg,
                "state": "complete",
                "intent": "resume",
                "resume_complete": True,
                "career_complete": False,
                "pdf_file": pdf_file
            }

        # ---------- CAREER GUIDANCE ----------
        elif state.current_state == AgentState.CAREER_OUTPUT:
            from career_guidance import CareerGuidanceService
            career_service = CareerGuidanceService()

            skills = state.career_skills or []
            interests = state.career_interests or []
            education = state.career_education or ""

            suggestions_data = await career_service.get_career_suggestions(
                skills, interests, education, state.session_id
            )

            state.career_complete = True
            state.current_state = AgentState.COMPLETE

            # Format guidance response
            response_msg = "📊 **Personalized Career Guidance**\n\n"
            recommendations = suggestions_data.get("recommendations", [])
            for i, rec in enumerate(recommendations[:3], 1):
                response_msg += f"**{i}. {rec['title']}**\n{rec['description']}\n"
                if rec.get("entry_level_roles"):
                    response_msg += f"🎯 **Entry-Level Roles**: {', '.join(rec['entry_level_roles'][:2])}\n"
                if rec.get("growth_path"):
                    response_msg += f"📈 **Career Path**: {rec['growth_path']}\n"
                if rec.get("matched_skills"):
                    response_msg += f"✅ **Your Matching Skills**: {', '.join(rec['matched_skills'][:3])}\n"
                response_msg += "\n"

            actionable = suggestions_data.get("actionable_advice", [])
            if actionable:
                response_msg += "**💡 Actionable Next Steps:**\n\n"
                for advice in actionable[:5]:
                    response_msg += f"{advice}\n\n"

            response_msg += "---\n🌍 *Aligned with SDG 8: Decent Work & Economic Growth*"
            state.messages.append({"role": "assistant", "content": response_msg})

            return {
                "message": response_msg,
                "state": "complete",
                "intent": "career",
                "resume_complete": False,
                "career_complete": True
            }

        return {"message": "Processing...", "state": "processing", "intent": None,
                "resume_complete": False, "career_complete": False}

    # ==================== HELPER FUNCTIONS ====================
    def _get_next_resume_field(self, state: AgentStateData) -> Optional[str]:
        if not state.name: return "name"
        if not state.email: return "email"
        if not state.linkedin and not state.portfolio: return "linkedin"
        if not state.summary: return "summary"
        if not state.education: return "education"
        if not state.skills: return "skills"
        if not state.experience: return "experience"
        if not state.projects: return "projects"
        if not state.achievements and not state.certifications: return "achievements"
        return None

    def _get_next_career_field(self, state: AgentStateData) -> Optional[str]:
        if not state.career_skills: return "skills"
        if not state.career_interests: return "interests"
        if not state.career_education: return "education"
        return None

    def _get_resume_prompt(self, field: str) -> str:
        prompts = {
            "name": "Hello! I'm here to help you create a professional resume. Let's start with the basics.\n\n**What is your full name?",
            "email": "Great! Now, let's add your contact information.\n\n**What is your email address?",
            "linkedin": "Good! Do you have a LinkedIn profile or portfolio website? Please share the link ",
            "summary": "Perfect! Now, let's create a compelling career summary.\n\n**Please provide a 2-3 line career summary or objective.**\nThis should highlight your career goals and key strengths.",
            "education": "Excellent! Let's add your educational background.\n\n**Please provide your education details:**\n- Degree (e.g., B.Tech Computer Science)\n- College/University name\n- Graduation year (or expected)\n- Grade/CGPA (if applicable)\n\nYou can provide this in any format, and I'll structure it properly.",
            "skills": "Great! Now let's list your skills.\n\n**Please provide your skills separated by commas.**\nInclude both technical skills (programming languages, tools, technologies) and soft skills (communication, teamwork, etc.)\n\nExample: Python, JavaScript, React, Communication, Problem Solving",
            "experience": "Let's add your work experience or internships.\n\n**Please provide your experience details:**\n- Job/Internship title\n- Company name\n- Duration (e.g., June 2023 - August 2023)\n- Key achievements or responsibilities (bullet points)\n\nIf you have multiple experiences, list them all. Type 'none' if you don't have any experience yet.",
            "projects": "Now let's add your projects.\n\n**Please provide your project details:**\n- Project name\n- Technologies/tools used\n- Brief description (1-2 lines)\n\nList all relevant projects. Type 'none' if you don't have any projects to mention.",
            "achievements": "Finally, let's add your achievements and certifications.\n\n**Please provide:**\n- Any notable achievements, awards, or honors\n- Certifications (with issuing organization if applicable)\n\nList them separated by commas or new lines. Type 'none' if you don't have any."
        }
        return prompts.get(field, "Please provide the required info.")

    def _get_career_prompt(self, field: str) -> str:
        prompts = {
            "skills": "What are your key skills?",
            "interests": "What are your interests?",
            "education": "Your educational background?"
        }
        return prompts.get(field, "Please provide the required info.")

    def _store_resume_field(self, state: AgentStateData, field: str, value: str):
        val = value.strip()
        if field == "name": state.name = val
        elif field == "email": state.email = val
        elif field == "linkedin": state.linkedin = val
        elif field == "summary": state.summary = val
        elif field == "education": state.education = [{"details": val}]
        elif field == "skills": state.skills = {"technical": val.split(","), "soft": []}
        elif field == "experience": state.experience = [{"details": val}]
        elif field == "projects": state.projects = [{"details": val}]
        elif field == "achievements": state.achievements = [val]

    def _store_career_field(self, state: AgentStateData, field: str, value: str):
        val = value.strip()
        if field == "skills": state.career_skills = [s.strip() for s in val.split(",")]
        elif field == "interests": state.career_interests = [s.strip() for s in val.split(",")]
        elif field == "education": state.career_education = val

    # ==================== MAIN PROCESS ====================
    async def process_message(self, message: str, session_id: str, intent: Optional[str] = None) -> Dict:
        state = self._get_session(session_id)
        if state.current_state == AgentState.START:
            return await self.start_node(session_id, message)
        elif state.current_state == AgentState.INTENT:
            return await self.intent_node(session_id, message)
        elif state.current_state == AgentState.RESUME_COLLECTION:
            return await self.resume_node(session_id, message)
        elif state.current_state == AgentState.CAREER_COLLECTION:
            return await self.career_node(session_id, message)
        elif state.current_state in [AgentState.RESUME_OUTPUT, AgentState.CAREER_OUTPUT]:
            return await self.output_node(session_id, message)
        else:
            state.current_state = AgentState.START
            return await self.start_node(session_id, message)

    async def get_resume(self, session_id: str) -> Optional[Dict]:
        if session_id not in sessions: return None
        state = sessions[session_id]
        return {
            "name": state.name, "email": state.email, "linkedin": state.linkedin,
            "portfolio": state.portfolio, "summary": state.summary, "education": state.education,
            "skills": state.skills, "experience": state.experience, "projects": state.projects,
            "achievements": state.achievements, "certifications": state.certifications,
            "resume_complete": state.resume_complete
        }

    async def generate_polished_resume(self, resume_data: Dict, session_id: str) -> str:
        """
        Compatibility helper used by `/api/resume/generate`.

        The frontend expects HTML for preview; we keep this minimal and reuse the
        existing `ResumeGenerator` HTML template.
        """
        from resume_generator import ResumeGenerator
        generator = ResumeGenerator()
        return generator.generate_html(resume_data)

    async def get_career_data(self, session_id: str) -> Optional[Dict]:
        """
        Minimal placeholder for `/api/career/guidance` integration.
        Returns None when no career session exists.
        """
        if session_id not in sessions:
            return None
        state = sessions[session_id]
        return {
            "career_complete": state.career_complete,
            "skills": state.career_skills,
            "interests": state.career_interests,
            "education": state.career_education,
        }

    async def clear_session(self, session_id: str):
        if session_id in sessions: del sessions[session_id]


# ==================== AI AGENT WORKFLOW PIPELINE (Relay-facing) ====================
#
# This section implements a clear, linear AI workflow used by the webhook/Relay
# integration. It is intentionally simple and separate from the conversational
# state machine above.
#
# User Data
# → ResumeBuilderAgent
# → ResumeAnalyzerAgent (score 0–100)
# → SkillGapAgent
# → CareerAdvisorAgent
# → Save results in Supabase


class ResumeBuilderAgent:
    """Converts raw chatbot/Relay payload into a normalized resume JSON."""

    def run(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        # For this MVP, we assume Relay already sends a mostly structured payload
        # and we only normalize keys / provide sensible defaults.
        return {
            "name": raw_data.get("name"),
            "email": raw_data.get("email"),
            "linkedin": raw_data.get("linkedin"),
            "portfolio": raw_data.get("portfolio"),
            "summary": raw_data.get("summary"),
            "education": raw_data.get("education") or [],
            "skills": raw_data.get("skills") or {},
            "experience": raw_data.get("experience") or [],
            "projects": raw_data.get("projects") or [],
            "achievements": raw_data.get("achievements") or [],
            "certifications": raw_data.get("certifications") or [],
        }


class ResumeAnalyzerAgent:
    """Very lightweight scoring model for the resume (0–100)."""

    def run(self, resume_json: Dict[str, Any]) -> Dict[str, Any]:
        score = 40  # base
        # Add points for each important section that is present
        if resume_json.get("summary"):
            score += 10
        if resume_json.get("education"):
            score += 10
        if resume_json.get("skills"):
            score += 15
        if resume_json.get("experience"):
            score += 15
        if resume_json.get("projects"):
            score += 10

        return {"score": max(0, min(100, score))}


class SkillGapAgent:
    """Detects simple skill gaps based on a few common expectations."""

    ESSENTIAL_CLUSTERS = {
        "version_control": ["git", "github"],
        "web_basics": ["html", "css", "javascript"],
        "problem_solving": ["data structures", "algorithms"],
    }

    def run(self, resume_json: Dict[str, Any]) -> list[str]:
        skills = resume_json.get("skills") or {}
        technical = [s.lower() for s in skills.get("technical", [])]
        soft = [s.lower() for s in skills.get("soft", [])]

        gaps: list[str] = []

        # Simple heuristic: look for missing members of essential clusters
        for cluster_name, cluster_skills in self.ESSENTIAL_CLUSTERS.items():
            has_any = any(s in technical for s in cluster_skills)
            if not has_any:
                gaps.append(cluster_name)

        # Encourage common soft skills
        soft_expectations = ["communication", "teamwork", "problem solving"]
        for soft_skill in soft_expectations:
            if soft_skill not in soft:
                gaps.append(soft_skill)

        # Deduplicate
        return sorted(list(set(gaps)))


class CareerAdvisorAgent:
    """Produces a very small, readable career roadmap based on gaps + score."""

    def run(
        self,
        resume_json: Dict[str, Any],
        score: int,
        skill_gaps: list[str],
    ) -> Dict[str, Any]:
        roadmap: Dict[str, Any] = {
            "score_band": "beginner" if score < 60 else "intermediate" if score < 80 else "strong",
            "next_steps": [],
        }

        if "version_control" in skill_gaps:
            roadmap["next_steps"].append(
                "Complete a short Git/GitHub course and add at least one project showcasing commits."
            )
        if "web_basics" in skill_gaps:
            roadmap["next_steps"].append(
                "Build a small HTML/CSS/JavaScript project (e.g., portfolio site) and list it under Projects."
            )
        if "problem_solving" in skill_gaps:
            roadmap["next_steps"].append(
                "Practice data structures & algorithms on a coding platform and mention this under Skills."
            )

        if "communication" in skill_gaps:
            roadmap["next_steps"].append(
                "Join a speaking or presentation club and add it as an achievement once completed."
            )

        if not roadmap["next_steps"]:
            roadmap["next_steps"].append(
                "Refine your existing projects, quantify impact, and tailor your resume to specific roles."
            )

        return roadmap


def run_ai_resume_workflow(
    session_id: str,
    raw_user_data: Dict[str, Any],
    supabase_service: Any | None = None,
    user_id: Optional[str] = None,
) -> None:
    """
    Orchestrate the non-chat AI resume workflow in a single, clear pipeline.

    This function is designed to be executed in a FastAPI BackgroundTask.

    User Data
    → ResumeBuilderAgent
    → ResumeAnalyzerAgent (score 0–100)
    → SkillGapAgent
    → CareerAdvisorAgent
    → Save results in Supabase + generate files
    """
    # 1) Build structured resume JSON
    builder = ResumeBuilderAgent()
    resume_json = builder.run(raw_user_data)

    # 2) Analyze resume to produce a simple score
    analyzer = ResumeAnalyzerAgent()
    analysis = analyzer.run(resume_json)
    score = analysis.get("score", 0)

    # 3) Detect skill gaps
    gap_agent = SkillGapAgent()
    skill_gaps = gap_agent.run(resume_json)

    # 4) Generate a career roadmap
    advisor = CareerAdvisorAgent()
    career_roadmap = advisor.run(resume_json, score, skill_gaps)

    # 5) Generate resume files (PDF + DOCX)
    from resume_generator import ResumeGenerator

    os.makedirs("generated_resumes", exist_ok=True)
    pdf_path = f"generated_resumes/{session_id}_resume.pdf"
    docx_path = f"generated_resumes/{session_id}_resume.docx"

    generator = ResumeGenerator()
    try:
        generator.generate_pdf(resume_json, output_file=pdf_path)
    except Exception:
        # If PDF generation fails, continue with the rest of the workflow
        pdf_path = ""

    try:
        generator.generate_docx(resume_json, output_file=docx_path)
    except Exception:
        docx_path = ""

    # 6) Persist results in Supabase (if configured)
    if supabase_service is not None:
        try:
            supabase_service.save_resume_results(
                session_id=session_id,
                resume_json=resume_json,
                score=score,
                skill_gaps=skill_gaps,
                career_roadmap=career_roadmap,
                user_id=user_id,
            )

            # Upload files if generated successfully
            if pdf_path:
                supabase_service.save_resume_file(
                    session_id=session_id,
                    file_path=pdf_path,
                    content_type="application/pdf",
                )
            if docx_path:
                supabase_service.save_resume_file(
                    session_id=session_id,
                    file_path=docx_path,
                    content_type=(
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    ),
                )
        except Exception:
            # Supabase failures should not break the background workflow
            pass


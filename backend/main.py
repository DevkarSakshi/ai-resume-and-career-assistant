from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import traceback
from fastapi.responses import FileResponse
import json
import os

from agent_workflow import AgentWorkflow, run_ai_resume_workflow
from career_guidance import CareerGuidanceService
from supabase_service import SupabaseService

app = FastAPI(title="AI Resume & Career Assistant API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://ai-resume-and-career-assistant.onrender.com", "https://*.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
agent_workflow = AgentWorkflow()
career_service = CareerGuidanceService()
supabase_service = SupabaseService()

# Metrics tracking
metrics = {
    "resumes_generated": 0,
    "career_suggestions": 0,
    "users_engaged": set()
}

class ChatMessage(BaseModel):
    message: str
    session_id: str
    intent: Optional[str] = None

class ResumeData(BaseModel):
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

class CareerGuidanceRequest(BaseModel):
    skills: List[str]
    interests: List[str]
    education: str
    session_id: str


class ResumeSubmissionPayload(BaseModel):
    """
    Payload received when a resume has been fully collected by the chatbot.

    In production, this payload is typically sent to a no-code automation
    platform (Relay) first, which then forwards a structured version of this
    data to the AI workflow endpoint.
    """

    session_id: str
    user_id: Optional[str] = None
    answers: Dict  # raw chatbot answers / resume fields

@app.get("/")
async def root():
    return {"message": "AI Resume & Career Assistant API", "status": "running"}

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/chat")
async def chat(chat_message: ChatMessage, request: Request):
    """Main chat endpoint - AI Agent workflow for resume help and career guidance"""
    try:
        # Basic logging
        print("📩 /api/chat request:", {
            "session_id": chat_message.session_id,
            "intent": chat_message.intent,
            "message_preview": chat_message.message[:80],
        })

        response = await agent_workflow.process_message(
            chat_message.message,
            chat_message.session_id,
            chat_message.intent
        )
        
        # Track user engagement
        metrics["users_engaged"].add(chat_message.session_id)
        
        return {
            "response": response["message"],
            "intent": response.get("intent"),
            "resume_complete": response.get("resume_complete", False),
            "career_complete": response.get("career_complete", False),
            "current_state": response.get("state"),
            "current_field": response.get("current_field")
        }
    except Exception as e:
        # Enable traceback so full Python error prints in backend terminal
        print("❌ ERROR IN /api/chat:", repr(e))
        traceback.print_exc()  # <--- THIS WILL SHOW THE FULL ERROR
        # Keep the response shape consistent for the frontend
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Chat processing failed",
                "message": str(e),
            },
        )


@app.post("/webhook/resume-submitted")
async def resume_submitted(
    payload: ResumeSubmissionPayload,
    background_tasks: BackgroundTasks,
):
    """
    Webhook entrypoint for completed resume chatbot flows.

    - Accepts raw chatbot answers
    - Does NOT run heavy AI logic synchronously
    - Only triggers the AI workflow pipeline via a background task

    Relay (no-code automation) typically sits between the chatbot and this
    workflow:
    - This step is handled by Relay (no-code automation):
      * Receive chatbot payload
      * Clean/validate/augment fields
      * Forward structured JSON to this backend for processing
    """
    # Persist raw answers for observability / debugging
    try:
        supabase_service.save_chatbot_answers(
            session_id=payload.session_id,
            answers=payload.answers,
            user_id=payload.user_id,
        )
    except Exception:
        # Storage is best-effort in this MVP; failures should not break the webhook
        pass

    # Trigger background AI workflow (non-blocking)
    background_tasks.add_task(
        run_ai_resume_workflow,
        payload.session_id,
        payload.answers,
        supabase_service,
        payload.user_id,
    )

    return {"status": "processing_started", "session_id": payload.session_id}

@app.get("/api/resume/{session_id}")
async def get_resume(session_id: str):
    """Get the generated resume for a session"""
    try:
        resume = await agent_workflow.get_resume(session_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        return resume
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resume/generate")
async def generate_resume(request: Dict):
    """Generate final polished resume from collected data"""
    try:
        print("📄 /api/resume/generate request keys:", list(request.keys()) if isinstance(request, dict) else type(request))
        session_id = request.get("session_id") if isinstance(request, dict) else None
        resume_data = {k: v for k, v in request.items() if k != "session_id"} if isinstance(request, dict) else {}
        
        if not resume_data or not any(resume_data.values()):
            # Try to get from session
            if session_id:
                resume_data = await agent_workflow.get_resume(session_id)
                if not resume_data:
                    raise HTTPException(status_code=404, detail="Resume data not found")
            else:
                raise HTTPException(status_code=400, detail="Resume data or session_id required")
        
        resume_html = await agent_workflow.generate_polished_resume(resume_data, session_id or "default")
        metrics["resumes_generated"] += 1
        return {"html": resume_html, "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        print("❌ ERROR IN /api/resume/generate:", repr(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/career/guidance")
async def career_guidance(request: CareerGuidanceRequest):
    """Get career guidance based on user profile"""
    try:
        # If session_id provided, try to get data from agent workflow
        if request.session_id:
            career_data = await agent_workflow.get_career_data(request.session_id)
            if career_data and career_data.get("career_complete"):
                skills = career_data.get("skills", []) or request.skills
                interests = career_data.get("interests", []) or request.interests
                education = career_data.get("education", "") or request.education
            else:
                skills = request.skills
                interests = request.interests
                education = request.education
        else:
            skills = request.skills
            interests = request.interests
            education = request.education
        
        suggestions = await career_service.get_career_suggestions(
            skills,
            interests,
            education,
            request.session_id
        )
        metrics["career_suggestions"] += 1
        metrics["users_engaged"].add(request.session_id)
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_metrics():
    """Get application metrics"""
    return {
        "resumes_generated": metrics["resumes_generated"],
        "career_suggestions": metrics["career_suggestions"],
        "users_engaged": len(metrics["users_engaged"])
    }

@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    """Clear session data"""
    try:
        await agent_workflow.clear_session(session_id)
        return {"message": "Session cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_resume/{session_id}")
def download_resume(session_id: str):
    # Resume files are generated server-side into backend/generated_resumes/
    pdf_file = f"generated_resumes/{session_id}_resume.pdf"
    
    if not os.path.exists(pdf_file):
        return {"error": "Resume not found"}
    
    return FileResponse(
        path=pdf_file,
        media_type="application/pdf",
        filename="resume.pdf"
    )


@app.get("/download_resume_docx/{session_id}")
def download_resume_docx(session_id: str):
    # Resume DOCX is generated server-side into backend/generated_resumes/
    docx_file = f"generated_resumes/{session_id}_resume.docx"

    if not os.path.exists(docx_file):
        return {"error": "Resume not found"}

    return FileResponse(
        path=docx_file,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="resume.docx",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
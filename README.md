# AI Resume & Career Assistant

A comprehensive AI-powered Resume & Career Assistant for college students and freshers, fully aligned with SDG 8 (Decent Work & Economic Growth).

## Features

### Resume Building
- **Step-by-step data collection**: Interactive chat interface that collects resume information one field at a time
- **Professional formatting**: Automatically generates polished, professionally formatted resumes
- **Missing skills detection**: Highlights missing key skills based on your profile
- **Language improvement**: Enhances phrasing and presentation
- **PDF export**: Ready for PDF export functionality

### Career Guidance
- **Personalized recommendations**: Career path suggestions based on skills, interests, and education
- **Actionable advice**: Provides concrete steps for career development
- **SDG 8 aligned**: Focuses on decent work and economic growth opportunities

## Tech Stack

- **Frontend**: React (Vite) + Tailwind CSS
- **Backend**: Python + FastAPI
- **Workflow**: Custom state machine for step-by-step data collection + background AI pipeline
- **Database**: Supabase (for persistence) + in-memory sessions (for live chat)

## Project Structure

```
AI Resume & Career Assistant/
├── backend/
│   ├── main.py              # FastAPI app: chat API + webhook + background tasks
│   ├── agent_workflow.py    # Chat state machine + AI agent workflow pipeline
│   ├── resume_workflow.py   # Legacy resume collection workflow (kept for compatibility)
│   ├── resume_generator.py  # HTML → PDF/DOCX resume generator
│   ├── career_guidance.py   # Career guidance service
│   ├── supabase_service.py  # Minimal Supabase wrapper (auth, data, file storage)
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx
│   │   │   └── ResumePreview.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Architecture Flow (High-Level)

- **User → Frontend Chatbot**: User chats with the React-based assistant to provide resume and career details.
- **Chatbot → Backend `/api/chat`**: Messages are sent to the FastAPI backend, which uses `AgentWorkflow` to manage state and prompts.
- **Chatbot Completion → Webhook Trigger**: Once resume data is complete, the frontend (or an automation tool) sends a payload to `POST /webhook/resume-submitted`.
- **Webhook → Background AI Pipeline**: The webhook *only* enqueues work via `BackgroundTasks`; heavy processing is handled asynchronously.
- **AI Pipeline → Supabase**: The background workflow generates resume files (PDF/DOCX), computes scores and skill gaps, builds a career roadmap, and stores everything in Supabase.

This pattern keeps the user-facing APIs fast while allowing longer AI processing to run in the background.

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the FastAPI server:
   ```bash
   python main.py
   ```
   
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:5173`

## Usage

### Creating a Resume

1. Open the application in your browser
2. Start a conversation with the AI assistant
3. The assistant will ask for information step-by-step:
   - Name and Contact Information
   - Career Summary/Objective
   - Education Details
   - Skills (Technical & Soft)
   - Work Experience/Internships
   - Projects
   - Achievements & Certifications
4. Once all information is collected, your resume will be automatically generated
5. Preview and export your resume as PDF, DOCX, or HTML

### Career Guidance

Use the chat interface to ask for career guidance. Provide your:
- Skills
- Interests
- Education background

The system will provide personalized career path recommendations and actionable advice.

## API Endpoints

- `POST /api/chat` - Main chat endpoint for resume help and career guidance
- `GET /api/resume/{session_id}` - Get resume data for a session
- `POST /api/resume/generate` - Generate polished resume HTML
- `POST /api/career/guidance` - Get career guidance suggestions
- `GET /api/metrics` - Get application metrics (resumes generated, career suggestions, users engaged)
- `DELETE /api/session/{session_id}` - Clear session data
- `POST /webhook/resume-submitted` - Webhook to trigger the background AI resume workflow (Relay entrypoint)

## AI Agent Workflow (Background Pipeline)

The non-chat AI workflow is implemented at the bottom of `agent_workflow.py` and is designed to be called from a background task:

1. **ResumeBuilderAgent**: Normalizes raw chatbot/Relay payload into structured resume JSON.
2. **ResumeAnalyzerAgent**: Assigns a simple resume score (0–100) based on presence of key sections.
3. **SkillGapAgent**: Detects basic skill gaps (e.g., Git, web fundamentals, problem solving, communication).
4. **CareerAdvisorAgent**: Creates a short, actionable career roadmap using the score and gaps.
5. **Persistence**: The pipeline uses `ResumeGenerator` to create PDF + DOCX files and `SupabaseService` to store:
   - Structured resume JSON
   - Resume score
   - Skill gaps
   - Career roadmap
   - Resume files in a Supabase Storage bucket (`resumes`)

This pipeline is invoked via `run_ai_resume_workflow`, which is used in a FastAPI `BackgroundTasks` context.

## Relay & Webhook Integration

Relay is treated as an external **no-code automation** layer that orchestrates the workflow:

- The backend exposes `POST /webhook/resume-submitted` as the main trigger for completed resume sessions.
- **This step is handled by Relay (no-code automation)**:
  - Receive chatbot data (raw answers and metadata)
  - Clean, validate, and transform it into a structured JSON payload
  - Forward the structured payload to the backend (same webhook or a dedicated AI endpoint)
- The webhook does not perform heavy AI work directly; instead, it schedules `run_ai_resume_workflow` as a background task.

Comments in `main.py` and `agent_workflow.py` explicitly mark where Relay would sit in a production setup.

## Supabase Usage

Supabase is used in a minimal, MVP-friendly way via `supabase_service.py`:

- **Configuration** (environment variables):
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY` or `SUPABASE_SERVICE_ROLE_KEY`
- **Tables (expected)**:
  - `chatbot_answers`: stores raw chatbot answers per session
  - `resume_results`: stores resume JSON, score, skill gaps, and career roadmap
- **Storage**:
  - Bucket: `resumes` (used for PDF/DOCX upload)
- The service is defensive: if Supabase is not configured or fails, it becomes a no-op so the rest of the system keeps working.

This keeps Supabase integration simple while still being realistic and production-inspired.

## Metrics Tracking

The application tracks:
- Number of resumes generated
- Number of career suggestions provided
- Users engaged

Access metrics via the `/api/metrics` endpoint.

## SDG 8 Alignment

This project aligns with Sustainable Development Goal 8 (Decent Work & Economic Growth) by:
- Helping students and freshers prepare for employment
- Providing career guidance and skill development recommendations
- Supporting economic growth through workforce development
- Making professional resume creation accessible

## Future Enhancements

- Richer Supabase schema (user profiles, multi-resume history, analytics dashboards)
- Advanced PDF/DOCX templates and theming
- Resume templates selection
- ATS (Applicant Tracking System) optimization
- Integration with job boards and career platforms
- Multi-language support

## MVP Disclaimer

This project is intentionally scoped as an **MVP for an AI internship**:

- Logic is kept simple and readable rather than fully optimized.
- Supabase integration uses basic inserts/uploads without complex error handling.
- Relay is represented via webhooks and comments instead of a full SDK integration.
- Background processing uses FastAPI `BackgroundTasks` only (no queues or workers).

The goal is **architecture clarity and completeness**, not production perfection.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available for educational and professional use.

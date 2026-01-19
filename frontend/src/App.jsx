import { useState, useEffect, useRef } from 'react'
import ChatInterface from './components/ChatInterface'
import ResumePreview from './components/ResumePreview'
import { generateSessionId } from './utils'

function App() {
  const [sessionId] = useState(() => generateSessionId())
  const [showResume, setShowResume] = useState(false)
  const [resumeHtml, setResumeHtml] = useState(null)

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-7xl mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-indigo-900 mb-2">
            AI Resume & Career Assistant
          </h1>
          <p className="text-indigo-700">
            Your personal assistant for creating professional resumes and career guidance
            <br />
          </p>
        </header>

        <div className="flex gap-6 flex-col lg:flex-row">
          <div className={`${showResume ? 'lg:w-1/2' : 'w-full'} transition-all duration-300`}>
            <ChatInterface 
              sessionId={sessionId} 
              onResumeReady={(html) => {
                setResumeHtml(html)
                setShowResume(true)
              }}
            />
          </div>

          {showResume && (
            <div className="lg:w-1/2">
              <ResumePreview 
                resumeHtml={resumeHtml}
                onClose={() => setShowResume(false)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App

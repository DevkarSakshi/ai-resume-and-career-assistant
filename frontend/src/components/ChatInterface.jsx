import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const ChatInterface = ({ sessionId }) => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello! 👋 I'm your AI Resume & Career Assistant. I can help you create a professional resume or provide career guidance. How would you like to start?"
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [resumeComplete, setResumeComplete] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState(null);

  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const backendUrl = process.env.NODE_ENV === 'production'
        ? 'https://ai-resume-and-career-assistant.onrender.com'
        : 'http://localhost:8000';

      const response = await axios.post(`${backendUrl}/api/chat`, {
        message: input.trim(),
        session_id: sessionId
      });

      const assistantMessage = { role: 'assistant', content: response.data.response };
      setMessages(prev => [...prev, assistantMessage]);

      if (response.data.resume_complete) {
        setResumeComplete(true);
        fetchResume();
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const fetchResume = async () => {
    try {
      const backendUrl = process.env.NODE_ENV === 'production'
        ? 'https://ai-resume-and-career-assistant.onrender.com'
        : 'http://localhost:8000';

      // 1️⃣ Fetch stored resume data from backend
      const response = await axios.get(`${backendUrl}/api/resume/${sessionId}`);
      const resumeData = response.data;

      // 2️⃣ Trigger PDF generation on backend
      await axios.post(`${backendUrl}/api/resume/generate`, {
        ...resumeData,
        session_id: sessionId
      });

      // 3️⃣ Set download URL pointing to backend
      setDownloadUrl(`${backendUrl}/download_resume/${sessionId}`);
    } catch (error) {
      console.error('Error fetching resume:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-xl h-[600px] flex flex-col overflow-hidden">
      {/* Chat Header */}
      <div className="bg-emerald-600 text-white px-6 py-4 rounded-t-lg flex-shrink-0">
        <h2 className="text-xl font-semibold">Chat Assistant</h2>

        {resumeComplete && (
          <p className="text-sm text-emerald-100 mt-1">✓ Resume data collected successfully!</p>
        )}

        {resumeComplete && downloadUrl && (
          <div className="mt-2">
            <a
              href={downloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white text-emerald-600 px-4 py-2 rounded-lg font-semibold hover:bg-emerald-50 transition-colors"
            >
              Download Resume
            </a>
          </div>
        )}
      </div>

      {/* Chat Messages */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-6 space-y-4 min-h-0"
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[80%] rounded-lg px-4 py-2 ${
              msg.role === 'user' ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-gray-800'
            }`}>
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-emerald-50 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <div className="border-t border-gray-200 p-4 flex-shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="bg-emerald-600 text-white px-6 py-2 rounded-lg hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

import { useEffect, useRef } from 'react'

const ResumePreview = ({ resumeHtml, onClose }) => {
  const iframeRef = useRef(null)

  useEffect(() => {
    if (iframeRef.current && resumeHtml) {
      const iframe = iframeRef.current
      const doc = iframe.contentDocument || iframe.contentWindow.document
      doc.open()
      doc.write(resumeHtml)
      doc.close()
    }
  }, [resumeHtml])

  const handleExportPDF = () => {
    if (!iframeRef.current || !resumeHtml) return

    const printWindow = window.open('', '_blank')
    printWindow.document.write(resumeHtml)
    printWindow.document.close()
    
    printWindow.onload = () => {
      printWindow.print()
    }
  }

  const handleDownloadHTML = () => {
    if (!resumeHtml) return
    
    const blob = new Blob([resumeHtml], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'resume.html'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="bg-white rounded-lg shadow-xl h-[600px] flex flex-col">
      <div className="bg-indigo-600 text-white px-6 py-4 rounded-t-lg flex justify-between items-center">
        <h2 className="text-xl font-semibold">Resume Preview</h2>
        <div className="flex gap-2">
          <button
            onClick={handleDownloadHTML}
            className="bg-indigo-500 hover:bg-indigo-400 px-4 py-2 rounded-lg text-sm transition-colors"
          >
            Download HTML
          </button>
          <button
            onClick={handleExportPDF}
            className="bg-indigo-500 hover:bg-indigo-400 px-4 py-2 rounded-lg text-sm transition-colors"
          >
            Export PDF
          </button>
          <button
            onClick={onClose}
            className="bg-red-500 hover:bg-red-400 px-4 py-2 rounded-lg text-sm transition-colors"
          >
            Close
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <iframe
          ref={iframeRef}
          className="w-full h-full border-0"
          title="Resume Preview"
        />
      </div>
    </div>
  )
}

export default ResumePreview

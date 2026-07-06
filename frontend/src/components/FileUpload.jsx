import { useRef, useState } from 'react'
import { Upload, X, FileText } from 'lucide-react'

export default function FileUpload({ file, setFile }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()

  const accept = ['.pdf', '.docx']

  const handleFile = (f) => {
    if (!f) return
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    if (!accept.includes(ext)) return
    setFile(f)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)
  const onChange = (e) => handleFile(e.target.files[0])

  if (file) {
    return (
      <div className="border border-hairline rounded-md p-4 flex items-center justify-between bg-canvas">
        <div className="flex items-center gap-3">
          <FileText size={20} className="text-mint-teal" />
          <span className="font-body text-sm text-ink truncate max-w-xs">{file.name}</span>
        </div>
        <button
          type="button"
          onClick={() => setFile(null)}
          className="text-ink-muted hover:text-ink transition-colors"
        >
          <X size={18} />
        </button>
      </div>
    )
  }

  return (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onClick={() => inputRef.current.click()}
      className={`border-2 border-dashed rounded-md p-8 flex flex-col items-center justify-center cursor-pointer transition-colors
        ${dragging ? 'border-mint-teal bg-secondary-container/20' : 'border-surface-dim hover:border-ink-muted'}`}
    >
      <Upload size={24} className="text-ink-muted mb-3" />
      <p className="font-body text-sm font-medium text-ink">Drop your CV here</p>
      <p className="font-body text-xs text-ink-muted mt-1">PDF or DOCX · click to browse</p>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx"
        className="hidden"
        onChange={onChange}
      />
    </div>
  )
}

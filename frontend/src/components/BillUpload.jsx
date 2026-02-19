import { useState, useCallback } from 'react'

function BillUpload({ onUploadSuccess }) {
  const [file, setFile] = useState(null)
  const [processing, setProcessing] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState(null)

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const dropped = e.dataTransfer.files[0]
      if (validateFile(dropped)) {
        setFile(dropped)
        setError(null)
      }
    }
  }, [])

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0]
      if (validateFile(selected)) {
        setFile(selected)
        setError(null)
      }
    }
  }

  const validateFile = (f) => {
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
    if (!allowedTypes.includes(f.type)) {
      setError('Please upload a PDF, JPG, or PNG file')
      return false
    }
    if (f.size > 16 * 1024 * 1024) {
      setError('File size must be less than 16MB')
      return false
    }
    return true
  }

  const handleProcess = async () => {
    if (!file) { setError('Please select a file first'); return }

    setProcessing(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:5001/process', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Processing failed')
      }

      setFile(null)
      if (onUploadSuccess) onUploadSuccess(data)

    } catch (err) {
      setError(err.message || 'Processing failed. Please try again.')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="bill-upload">
      <div
        className={`drop-zone ${dragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {!file ? (
          <>
            <div className="drop-icon">📄</div>
            <p className="drop-text">Drag and drop your medical bill here, or</p>
            <label className="file-input-label">
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <span className="button primary">Browse Files</span>
            </label>
            <p className="drop-hint">Supports PDF, JPG, PNG (max 16MB)</p>
          </>
        ) : (
          <div className="file-preview">
            <div className="file-icon">{file.type === 'application/pdf' ? '📑' : '🖼️'}</div>
            <div className="file-info">
              <p className="file-name">{file.name}</p>
              <p className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
            <button className="remove-file" onClick={() => setFile(null)} type="button">✕</button>
          </div>
        )}
      </div>

      {error && <div className="error-message">⚠️ {error}</div>}

      {file && (
        <button
          className="button primary upload-btn"
          onClick={handleProcess}
          disabled={processing}
        >
          {processing ? (
            <span className="processing-label">
              <span className="processing-dot" />
              Uploading & analyzing...
            </span>
          ) : 'Upload & Analyze'}
        </button>
      )}
    </div>
  )
}

export default BillUpload

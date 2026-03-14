import { useState, useRef } from 'react';
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadResume } from '../../services/api';

const ResumeUploader = ({ onUploadSuccess, onClose }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
        setMessage(null);
      } else {
        setMessage({ type: 'error', text: 'Please upload a PDF file' });
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type === 'application/pdf') {
        setFile(selectedFile);
        setMessage(null);
      } else {
        setMessage({ type: 'error', text: 'Please upload a PDF file' });
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    try {
      setUploading(true);
      setMessage(null);
      const result = await uploadResume(file);
      setMessage({ type: 'success', text: 'Resume uploaded successfully!' });
      
      // Call success callback after a short delay
      setTimeout(() => {
        if (onUploadSuccess) onUploadSuccess(result.data);
        if (onClose) onClose();
      }, 1500);
    } catch (error) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail;
      if (status === 409) {
        setMessage({ type: 'duplicate', text: detail || 'Duplicate resume detected. This candidate already exists.' });
      } else {
        setMessage({ 
          type: 'error', 
          text: detail || 'Upload failed. Please try again.' 
        });
      }
    } finally {
      setUploading(false);
    }
  };

  const removeFile = () => {
    setFile(null);
    setMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl border border-border/60 max-w-lg w-full p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-foreground">Upload Resume</h2>
          <button
            onClick={onClose}
            className="text-slate-600 hover:text-foreground transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {message && (
          <div className={`mb-4 p-3 rounded-lg border flex items-center gap-2 ${
            message.type === 'success' 
              ? 'bg-success/10 border-green-500/20 text-success' 
              : message.type === 'duplicate'
              ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'
              : 'bg-destructive/10 border-red-500/20 text-destructive'
          }`}>
            {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
            <span className="text-sm">{message.text}</span>
          </div>
        )}

        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive 
              ? 'border-blue-500 bg-primary/10' 
              : 'border-border hover:border-gray-500'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {!file ? (
            <>
              <Upload className="mx-auto text-slate-600 mb-4" size={48} />
              <p className="text-slate-700 mb-2">Drag and drop your resume here</p>
              <p className="text-muted-foreground text-sm mb-4">or</p>
              <label className="inline-block px-4 py-2 bg-primary hover:bg-primary/90 text-foreground rounded-lg cursor-pointer transition-colors">
                Browse Files
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
              <p className="text-muted-foreground text-xs mt-4">PDF files only, max 10MB</p>
            </>
          ) : (
            <div className="flex items-center justify-between bg-white rounded-lg p-4">
              <div className="flex items-center gap-3">
                <FileText className="text-blue-500" size={32} />
                <div className="text-left">
                  <p className="text-foreground font-medium">{file.name}</p>
                  <p className="text-slate-600 text-sm">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                onClick={removeFile}
                className="text-slate-600 hover:text-destructive transition-colors"
              >
                <X size={20} />
              </button>
            </div>
          )}
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 bg-white border border-border text-slate-700 hover:bg-slate-50 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="flex-1 px-4 py-2.5 bg-primary hover:bg-primary/90 disabled:bg-gray-600 disabled:cursor-not-allowed text-foreground rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {uploading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Uploading...
              </>
            ) : (
              <>
                <Upload size={18} />
                Upload Resume
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResumeUploader;

import { useState, useRef } from 'react';
import axios from 'axios';
import { UploadCloud, FileText, CheckCircle2, Loader2, AlertCircle, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API = 'http://localhost:8000/api/v1';

export const UploadForm = ({ onUploadSuccess, candidateId }) => {
  const [file, setFile] = useState(null);
  const [isPending, setIsPending] = useState(false);
  const [isError, setIsError] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);
  const [parseResult, setParseResult] = useState(null);
  const [uploadPhase, setUploadPhase] = useState('idle'); // idle | uploading | parsing | done
  const [isDragging, setIsDragging] = useState(false);
  
  const fileInputRef = useRef(null);

  const processFile = (selected) => {
    if (selected && (selected.type === 'application/pdf' || selected.name.endsWith('.docx'))) {
      setFile(selected);
      setIsError(false);
      setErrorMsg('');
    } else {
      setIsError(true);
      setErrorMsg('Please upload a valid .pdf or .docx file.');
    }
  };

  const handleFileChange = (e) => {
    processFile(e.target.files[0]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    setIsPending(true);
    setIsError(false);
    setErrorMsg('');
    setUploadPhase('uploading');

    try {
      const token = localStorage.getItem('access_token');
      const formData = new FormData();
      formData.append('file', file);

      const url = candidateId 
        ? `${API}/candidates/${candidateId}/upload-resume`
        : `${API}/candidates/upload`;

      setUploadPhase('parsing');

      const response = await axios.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      const data = response.data;
      setParseResult({
        skillsFound: data.skills_found || data.skills?.length || 0,
        experience: data.experience_years || 0,
        message: data.message || 'Resume parsed successfully!',
      });

      setUploadPhase('done');
      setIsSuccess(true);
      
      setTimeout(() => {
        if (onUploadSuccess) onUploadSuccess();
      }, 3000);
    } catch (err) {
      console.error('Upload failed:', err);
      setIsError(true);
      const detail = err.response?.data?.detail;
      setErrorMsg(typeof detail === 'string' ? detail : 'Upload failed. Please try again.');
      setUploadPhase('idle');
    } finally {
      setIsPending(false);
    }
  };

  if (isSuccess && parseResult) {
    return (
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-success/5 border border-success/20 rounded-2xl p-8 text-center"
      >
        <motion.div 
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', delay: 0.2 }}
          className="w-16 h-16 bg-success rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-success/20"
        >
          <CheckCircle2 className="w-8 h-8 text-white" />
        </motion.div>
        
        <h3 className="text-xl font-bold text-success mb-2">Resume Parsed Successfully!</h3>
        
        <div className="flex justify-center gap-4 my-6">
          <motion.div 
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
            className="bg-white rounded-xl p-4 border border-success/10 shadow-sm w-32"
          >
            <div className="text-3xl font-bold text-success mb-1">{parseResult.skillsFound}</div>
            <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Skills</div>
          </motion.div>
          <motion.div 
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
            className="bg-white rounded-xl p-4 border border-primary/10 shadow-sm w-32"
          >
            <div className="text-3xl font-bold text-primary mb-1">{parseResult.experience}</div>
            <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Years Exp</div>
          </motion.div>
        </div>
        
        <p className="text-sm text-success font-medium animate-pulse">
          Moving to screening...
        </p>
      </motion.div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <motion.div 
        animate={{
          borderColor: isDragging ? '#2563eb' : (file ? '#10b981' : '#e2e8f0'),
          backgroundColor: isDragging ? '#eff6ff' : (uploadPhase === 'parsing' ? '#f0fdf4' : '#fafafa')
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-3xl p-10 text-center relative transition-colors duration-300 ${isDragging ? 'shadow-inner' : ''}`}
      >
        {uploadPhase === 'idle' && (
          <input
            type="file"
            ref={fileInputRef}
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={handleFileChange}
            className="hidden"
            disabled={isPending}
          />
        )}

        <AnimatePresence mode="wait">
          {(uploadPhase === 'parsing' || uploadPhase === 'uploading') ? (
            <motion.div 
              key="processing"
              initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-4"
            >
              <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mb-4 relative">
                {uploadPhase === 'uploading' ? (
                  <Loader2 className="w-8 h-8 text-primary animate-spin" />
                ) : (
                  <>
                    <motion.div animate={{ scale: [1, 1.2, 1], rotate: [0, 180, 360] }} transition={{ duration: 3, repeat: Infinity }} className="absolute inset-0 border-2 border-primary border-dashed rounded-2xl opacity-30"></motion.div>
                    <Sparkles className="w-8 h-8 text-primary" />
                  </>
                )}
              </div>
              <p className="text-lg font-semibold text-foreground">
                {uploadPhase === 'uploading' ? 'Uploading resume...' : 'AI is parsing your resume...'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {uploadPhase === 'uploading' ? 'Please wait...' : 'Extracting skills, experience, and qualifications'}
              </p>
            </motion.div>
          ) : !file ? (
            <motion.div 
              key="upload"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-4 cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-colors ${isDragging ? 'bg-primary text-white scale-110 shadow-lg shadow-primary/30' : 'bg-primary/10 text-primary group-hover:bg-primary/20'}`}>
                <UploadCloud className="w-8 h-8" />
              </div>
              <p className="text-lg font-semibold text-foreground">
                <span className="text-primary">Click to upload</span> or drag and drop
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                PDF or DOCX format supported
              </p>
            </motion.div>
          ) : (
            <motion.div 
              key="file-ready"
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-4"
            >
              <div className="w-16 h-16 bg-success/10 rounded-2xl flex items-center justify-center mb-4">
                <FileText className="w-8 h-8 text-success" />
              </div>
              <p className="text-lg font-semibold text-foreground">{file.name}</p>
              <p className="text-sm text-muted-foreground mt-1">
                {(file.size / 1024).toFixed(0)} KB — Ready to upload
              </p>
              <button 
                type="button" 
                onClick={() => setFile(null)}
                className="mt-4 text-sm text-destructive hover:underline font-medium"
              >
                Remove file
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <AnimatePresence>
        {isError && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
            className="mt-4 flex items-center justify-center gap-2 text-sm text-destructive bg-destructive/10 p-3 rounded-xl border border-destructive/20"
          >
            <AlertCircle className="w-4 h-4" />
            {errorMsg}
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {file && uploadPhase === 'idle' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="mt-6 flex justify-center">
            <button
              type="submit"
              disabled={isPending}
              className="flex items-center justify-center px-8 py-3.5 border border-transparent rounded-xl shadow-md shadow-primary/20 text-base font-semibold text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 transition-all active:scale-95"
            >
              Upload & Parse Resume
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </form>
  );
};

export default UploadForm;

import { useState, useRef } from 'react';
import axios from 'axios';
import { UploadCloud, FileText, CheckCircle2, Loader2, AlertCircle, Sparkles, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

const VALID_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

export const UploadForm = ({ onUploadSuccess, candidateId }) => {
  const [file, setFile] = useState(null);
  const [isPending, setIsPending] = useState(false);
  const [isError, setIsError] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);
  const [parseResult, setParseResult] = useState(null);
  const [uploadPhase, setUploadPhase] = useState('idle');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const processFile = (selected) => {
    if (!selected) return;
    if (!VALID_TYPES.includes(selected.type) && !selected.name.endsWith('.docx')) {
      setIsError(true);
      setErrorMsg('Only PDF or DOCX files are supported.');
      return;
    }
    if (selected.size > MAX_FILE_SIZE) {
      setIsError(true);
      setErrorMsg(`File is too large (${(selected.size / 1024 / 1024).toFixed(1)} MB). Maximum size is 10 MB.`);
      return;
    }
    setFile(selected);
    setIsError(false);
    setErrorMsg('');
  };

  const handleFileChange = (e) => processFile(e.target.files[0]);
  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setIsDragging(false); };
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) processFile(e.dataTransfer.files[0]);
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
        timeout: 90000,
      });
      const data = response.data;
      setParseResult({
        skillsFound: data.skills_found ?? data.skills?.length ?? 0,
        experience: data.experience_years ?? 0,
        name: data.full_name || '',
      });
      setUploadPhase('done');
      setIsSuccess(true);
      setTimeout(() => { if (onUploadSuccess) onUploadSuccess(); }, 2500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setIsError(true);
      setErrorMsg(typeof detail === 'string' ? detail : 'Upload failed. Please try again.');
      setUploadPhase('idle');
    } finally {
      setIsPending(false);
    }
  };

  if (isSuccess && parseResult) {
    return (
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-emerald-50 border border-emerald-200 rounded-2xl p-8 text-center">
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.15 }}
          className="w-16 h-16 bg-success rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-success/25">
          <CheckCircle2 className="w-8 h-8 text-white" />
        </motion.div>
        <h3 className="text-lg font-bold text-emerald-800 mb-1">Resume Parsed Successfully!</h3>
        {parseResult.name && <p className="text-sm text-emerald-700 mb-4">Detected: <span className="font-semibold">{parseResult.name}</span></p>}
        <div className="flex justify-center gap-4 my-5">
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
            className="bg-white rounded-xl p-4 border border-emerald-100 shadow-sm w-28 text-center">
            <div className="text-3xl font-black text-success mb-0.5">{parseResult.skillsFound}</div>
            <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Skills Found</div>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
            className="bg-white rounded-xl p-4 border border-primary/10 shadow-sm w-28 text-center">
            <div className="text-3xl font-black text-primary mb-0.5">{parseResult.experience}</div>
            <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Yrs Exp</div>
          </motion.div>
        </div>
        <p className="text-xs text-emerald-600 font-medium animate-pulse">Moving to screening...</p>
      </motion.div>
    );
  }

  const isProcessing = uploadPhase === 'uploading' || uploadPhase === 'parsing';

  return (
    <form onSubmit={handleSubmit} className="w-full">
      {/* Drop zone */}
      <motion.div
        animate={{
          borderColor: isDragging ? '#2563eb' : file ? '#10b981' : '#e2e8f0',
          backgroundColor: isDragging ? '#eff6ff' : file ? '#f0fdf4' : '#fafafa',
        }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className="border-2 border-dashed rounded-2xl p-10 text-center transition-colors duration-200 cursor-pointer"
        onClick={() => !isProcessing && !file && fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          onChange={handleFileChange}
          className="hidden"
          disabled={isPending}
        />

        <AnimatePresence mode="wait">
          {isProcessing ? (
            <motion.div key="processing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center py-2">
              <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center mb-4 relative">
                {uploadPhase === 'uploading'
                  ? <Loader2 className="w-7 h-7 text-primary animate-spin" />
                  : <>
                      <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                        className="absolute inset-0 border-2 border-primary border-dashed rounded-2xl opacity-40" />
                      <Sparkles className="w-7 h-7 text-primary" />
                    </>
                }
              </div>
              <p className="text-base font-semibold text-foreground">
                {uploadPhase === 'uploading' ? 'Uploading...' : 'AI is parsing your resume...'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {uploadPhase === 'uploading' ? 'Please wait' : 'Extracting skills, experience & qualifications'}
              </p>
            </motion.div>
          ) : file ? (
            <motion.div key="file" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex flex-col items-center py-2">
              <div className="w-14 h-14 bg-success/10 rounded-2xl flex items-center justify-center mb-3">
                <FileText className="w-7 h-7 text-success" />
              </div>
              <p className="text-base font-semibold text-foreground truncate max-w-xs">{file.name}</p>
              <p className="text-sm text-muted-foreground mt-1">{(file.size / 1024).toFixed(0)} KB — Ready to upload</p>
              <button type="button" onClick={(e) => { e.stopPropagation(); setFile(null); }}
                className="mt-3 flex items-center gap-1 text-xs text-red-500 hover:text-red-700 font-medium transition-colors">
                <X className="w-3.5 h-3.5" /> Remove file
              </button>
            </motion.div>
          ) : (
            <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center py-2">
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-all ${isDragging ? 'bg-primary text-white scale-110 shadow-lg shadow-primary/30' : 'bg-primary/10 text-primary'}`}>
                <UploadCloud className="w-7 h-7" />
              </div>
              <p className="text-base font-semibold text-foreground">
                <span className="text-primary">Click to upload</span> or drag & drop
              </p>
              <p className="text-sm text-muted-foreground mt-1">PDF or DOCX · Max 10 MB</p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Error */}
      <AnimatePresence>
        {isError && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
            className="mt-3 flex items-center gap-2 text-sm text-red-700 bg-red-50 p-3 rounded-xl border border-red-200">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className="flex-1">{errorMsg}</span>
            <button type="button" onClick={() => setIsError(false)} className="text-red-400 hover:text-red-600">&times;</button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Submit */}
      <AnimatePresence>
        {file && uploadPhase === 'idle' && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="mt-5">
            <button type="submit" disabled={isPending}
              className="w-full flex items-center justify-center gap-2 py-4 px-6 rounded-xl text-base font-semibold text-white bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-600/90 shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/35 transition-all active:scale-[0.98] disabled:opacity-50">
              <Sparkles className="w-5 h-5" />
              Upload & Parse Resume
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </form>
  );
};

export default UploadForm;

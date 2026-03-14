import { useState, useEffect } from 'react';
import BasicDetailsForm from '../components/candidate/BasicDetailsForm';
import UploadForm from '../components/candidate/UploadForm';
import VideoScreeningSimple from '../components/candidate/VideoScreeningSimple';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { User, FileText, Video, CheckCircle2, ChevronRight, AlertCircle, ArrowLeft } from 'lucide-react';

const API = 'http://localhost:8000/api/v1';

const steps = [
  { id: 1, label: 'Basic Info', icon: <User className="w-5 h-5" /> },
  { id: 2, label: 'Resume', icon: <FileText className="w-5 h-5" /> },
  { id: 3, label: 'Screening', icon: <Video className="w-5 h-5" /> }
];

const CandidatePortal = () => {
  const [step, setStep] = useState(1);
  const [candidateId, setCandidateId] = useState(null);
  const [userEmail, setUserEmail] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      setUserEmail(user.email || '');
    } catch (_) {}
  }, []);

  const handleBasicDetailsSubmit = async (formData) => {
    setError('');
    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await axios.post(
        `${API}/candidates/basic-details`,
        {
          first_name: formData.firstName,
          last_name: formData.lastName,
          email: formData.email,
          mobile_number: formData.mobileNumber,
          place_of_residence: formData.placeOfResidence,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.data?.id) {
        setCandidateId(res.data.id);
        setStep(2);
      } else {
        setError('Unexpected response from server. Please try again.');
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 409) {
        const existingId = typeof detail === 'object' ? detail?.existing_id : null;
        if (existingId) {
          setCandidateId(existingId);
          setStep(2);
        } else {
          setError('A candidate with this email or phone already exists. Please contact HR if this error persists.');
        }
      } else if (err.response?.status === 401) {
        setError('Session expired. Please log in again.');
      } else if (err.response?.status === 405) {
        setError('Server configuration error. Please contact support.');
      } else {
        setError(typeof detail === 'string' ? detail : 'Failed to submit details. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8 font-sans selection:bg-primary/20">
      <div className="max-w-3xl mx-auto">

        {/* Header */}
        <div className="text-center mb-12">
          <motion.div 
            initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 200, damping: 20 }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary text-white mb-6 shadow-xl shadow-primary/30"
          >
             <User className="w-8 h-8" />
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-extrabold text-foreground tracking-tight mb-2"
          >
            Candidate Portal
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
            className="text-muted-foreground font-medium"
          >
            Complete your application in 3 simple steps
          </motion.p>
        </div>

        {/* Stepper */}
        <div className="flex justify-center items-center mb-12 relative z-10">
          {steps.map((s, i) => {
            const isDone = step > s.id;
            const isActive = step === s.id;
            
            return (
              <div key={s.id} className="flex items-center">
                <div className="flex flex-col items-center relative">
                  <motion.div 
                    layout
                    className={`w-12 h-12 rounded-full flex items-center justify-center border-2 z-10 bg-white transition-colors duration-300 ${isDone ? 'border-success bg-success text-white' : isActive ? 'border-primary text-primary shadow-md shadow-primary/20' : 'border-slate-200 text-slate-400'}`}
                  >
                    {isDone ? <CheckCircle2 className="w-6 h-6" /> : s.icon}
                  </motion.div>
                  <div className={`absolute top-14 text-xs font-semibold whitespace-nowrap ${isDone ? 'text-success' : isActive ? 'text-primary' : 'text-slate-400'}`}>
                    {s.label}
                  </div>
                </div>
                {i < steps.length - 1 && (
                  <div className={`w-16 sm:w-24 h-1 mx-2 rounded-full transition-colors duration-500 mb-6 ${step > s.id ? 'bg-success' : 'bg-slate-200'}`} />
                )}
              </div>
            );
          })}
        </div>

        {/* Error Banner */}
        <AnimatePresence>
          {error && (
            <motion.div 
              initial={{ opacity: 0, y: -10, height: 0 }} animate={{ opacity: 1, y: 0, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
              className="bg-destructive/10 border border-destructive/20 rounded-xl p-4 mb-6 flex items-center gap-3 text-destructive"
            >
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{error}</span>
              <button onClick={() => setError('')} className="ml-auto text-destructive hover:text-red-700 p-1">
                &times;
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Card */}
        <motion.div 
          layout
          className="bg-white rounded-3xl p-8 sm:p-10 shadow-glass border border-slate-100 relative overflow-hidden"
        >
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}>
                <div className="mb-8">
                  <h2 className="text-2xl font-bold text-foreground mb-2">Basic Information</h2>
                  <p className="text-muted-foreground text-sm">Tell us a bit about yourself to get started.</p>
                </div>
                <BasicDetailsForm onSubmit={handleBasicDetailsSubmit} initialEmail={userEmail} disabled={submitting} />
              </motion.div>
            )}

            {step === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}>
                <div className="mb-8">
                  <h2 className="text-2xl font-bold text-foreground mb-2">Upload Resume</h2>
                  <p className="text-muted-foreground text-sm">Our AI will automatically parse your skills and experience.</p>
                </div>
                <UploadForm onUploadSuccess={() => setStep(3)} candidateId={candidateId} />
                <button
                  onClick={() => setStep(1)}
                  className="mt-6 flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Basic Info
                </button>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div key="step3" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}>
                <div className="mb-8">
                  <h2 className="text-2xl font-bold text-foreground mb-2">Quick Screening</h2>
                  <p className="text-muted-foreground text-sm">Answer a few short situational questions to complete your profile.</p>
                </div>
                <VideoScreeningSimple candidateId={candidateId} onComplete={() => setStep(4)} />
                <button
                  onClick={() => setStep(2)}
                  className="mt-6 flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Resume Upload
                </button>
              </motion.div>
            )}

            {step === 4 && (
              <motion.div key="step4" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-10">
                <div className="w-24 h-24 bg-success/20 rounded-full flex items-center justify-center mx-auto mb-6">
                  <div className="w-16 h-16 bg-success rounded-full flex items-center justify-center shadow-lg shadow-success/30">
                    <CheckCircle2 className="w-8 h-8 text-white" />
                  </div>
                </div>
                <h2 className="text-3xl font-extrabold text-foreground mb-4">Application Submitted!</h2>
                <p className="text-muted-foreground mb-8 max-w-md mx-auto">
                  Your profile, resume, and screening responses have been recorded. Our AI has matched you with open roles, and HR will review your application shortly.
                </p>
                <div className="bg-primary/5 border border-primary/20 rounded-2xl p-5 text-sm font-medium text-primary flex items-center justify-center gap-3">
                  <CheckCircle2 className="w-5 h-5" />
                  You'll be notified via email about next steps.
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {step < 4 && (
          <p className="text-center text-muted-foreground/60 text-xs mt-8 font-medium">
            Your data is securely processed by HireAI.
          </p>
        )}
      </div>
    </div>
  );
};

export default CandidatePortal;

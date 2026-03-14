import { useState, useEffect } from 'react';
import BasicDetailsForm from '../components/candidate/BasicDetailsForm';
import UploadForm from '../components/candidate/UploadForm';
import VideoScreeningSimple from '../components/candidate/VideoScreeningSimple';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { User, FileText, Video, CheckCircle2, AlertCircle, ArrowLeft, Sparkles, Mail } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const steps = [
  { id: 1, label: 'Basic Info', icon: User },
  { id: 2, label: 'Resume', icon: FileText },
  { id: 3, label: 'Screening', icon: Video },
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
          const msg = typeof detail === 'object' ? detail?.message : detail;
          setError(msg || 'A candidate with this email or phone already exists.');
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-slate-50 py-10 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-2xl mx-auto">

        {/* Header */}
        <div className="text-center mb-10">
          <motion.div
            initial={{ scale: 0, rotate: -10 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: 'spring', stiffness: 260, damping: 20 }}
            className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-blue-700 text-white mb-5 shadow-xl shadow-primary/30"
          >
            <Sparkles className="w-7 h-7" />
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: -16 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-extrabold text-foreground tracking-tight mb-1"
          >
            Candidate Portal
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-muted-foreground text-sm"
          >
            Complete your application in 3 simple steps
          </motion.p>
        </div>

        {/* Stepper */}
        <div className="flex justify-center items-center mb-10">
          {steps.map((s, i) => {
            const isDone = step > s.id;
            const isActive = step === s.id;
            const Icon = s.icon;
            return (
              <div key={s.id} className="flex items-center">
                <div className="flex flex-col items-center">
                  <motion.div
                    layout
                    className={`w-11 h-11 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                      isDone
                        ? 'border-success bg-success text-white shadow-md shadow-success/30'
                        : isActive
                        ? 'border-primary bg-white text-primary shadow-md shadow-primary/20'
                        : 'border-slate-200 bg-white text-slate-400'
                    }`}
                  >
                    {isDone ? <CheckCircle2 className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                  </motion.div>
                  <span className={`mt-2 text-xs font-semibold whitespace-nowrap ${isDone ? 'text-success' : isActive ? 'text-primary' : 'text-slate-400'}`}>
                    {s.label}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div className={`w-16 sm:w-24 h-0.5 mx-2 mb-5 rounded-full transition-colors duration-500 ${step > s.id ? 'bg-success' : 'bg-slate-200'}`} />
                )}
              </div>
            );
          })}
        </div>

        {/* Error Banner */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8, height: 0 }}
              animate={{ opacity: 1, y: 0, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-red-50 border border-red-200 rounded-xl p-4 mb-5 flex items-start gap-3 text-red-700"
            >
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span className="text-sm font-medium flex-1">{error}</span>
              <button onClick={() => setError('')} className="text-red-400 hover:text-red-600 text-lg leading-none">&times;</button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Card */}
        <motion.div layout className="bg-white rounded-3xl shadow-glass border border-slate-100 overflow-hidden">
          <AnimatePresence mode="wait">

            {/* Step 1 — Basic Info */}
            {step === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 24 }} className="p-8 sm:p-10">
                <div className="mb-7">
                  <div className="flex items-center gap-3 mb-1">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <User className="w-4 h-4 text-primary" />
                    </div>
                    <h2 className="text-xl font-bold text-foreground">Basic Information</h2>
                  </div>
                  <p className="text-muted-foreground text-sm ml-11">Tell us a bit about yourself to get started.</p>
                </div>
                <BasicDetailsForm onSubmit={handleBasicDetailsSubmit} initialEmail={userEmail} disabled={submitting} />
              </motion.div>
            )}

            {/* Step 2 — Resume */}
            {step === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 24 }} className="p-8 sm:p-10">
                <div className="mb-7">
                  <div className="flex items-center gap-3 mb-1">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <FileText className="w-4 h-4 text-primary" />
                    </div>
                    <h2 className="text-xl font-bold text-foreground">Upload Resume</h2>
                  </div>
                  <p className="text-muted-foreground text-sm ml-11">Our AI will automatically parse your skills and experience.</p>
                </div>
                <UploadForm onUploadSuccess={() => setStep(3)} candidateId={candidateId} />
                <button
                  onClick={() => setStep(1)}
                  className="mt-6 flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" /> Back to Basic Info
                </button>
              </motion.div>
            )}

            {/* Step 3 — Screening */}
            {step === 3 && (
              <motion.div key="step3" initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 24 }} className="p-8 sm:p-10">
                <div className="mb-7">
                  <div className="flex items-center gap-3 mb-1">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Video className="w-4 h-4 text-primary" />
                    </div>
                    <h2 className="text-xl font-bold text-foreground">Quick Screening</h2>
                  </div>
                  <p className="text-muted-foreground text-sm ml-11">Answer a few short questions to complete your profile.</p>
                </div>
                <VideoScreeningSimple candidateId={candidateId} onComplete={() => setStep(4)} />
                <button
                  onClick={() => setStep(2)}
                  className="mt-6 flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" /> Back to Resume Upload
                </button>
              </motion.div>
            )}

            {/* Step 4 — Done */}
            {step === 4 && (
              <motion.div key="step4" initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} className="p-8 sm:p-10 text-center">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', delay: 0.1 }}
                  className="w-20 h-20 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-6"
                >
                  <div className="w-14 h-14 bg-success rounded-full flex items-center justify-center shadow-lg shadow-success/30">
                    <CheckCircle2 className="w-7 h-7 text-white" />
                  </div>
                </motion.div>

                <h2 className="text-2xl font-extrabold text-foreground mb-3">Application Submitted!</h2>
                <p className="text-muted-foreground text-sm mb-8 max-w-sm mx-auto">
                  Your profile, resume, and screening responses have been recorded. HR will review your application shortly.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
                  {[
                    { icon: User, label: 'Profile', desc: 'Saved' },
                    { icon: FileText, label: 'Resume', desc: 'Parsed by AI' },
                    { icon: CheckCircle2, label: 'Screening', desc: 'Completed' },
                  ].map(({ icon: Icon, label, desc }) => (
                    <div key={label} className="bg-slate-50 border border-slate-100 rounded-xl p-4 flex flex-col items-center gap-1">
                      <Icon className="w-5 h-5 text-success mb-1" />
                      <span className="text-xs font-bold text-foreground">{label}</span>
                      <span className="text-xs text-muted-foreground">{desc}</span>
                    </div>
                  ))}
                </div>

                <div className="bg-primary/5 border border-primary/20 rounded-2xl p-4 text-sm font-medium text-primary flex items-center justify-center gap-2">
                  <Mail className="w-4 h-4" />
                  You'll be notified via email about next steps.
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </motion.div>

        {step < 4 && (
          <p className="text-center text-muted-foreground/50 text-xs mt-6">
            Your data is securely processed by HireAI.
          </p>
        )}
      </div>
    </div>
  );
};

export default CandidatePortal;

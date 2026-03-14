import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Clock, Code, MessageCircle } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const allQuestions = [
  {
    id: 1, type: 'Communication', timer: 45,
    question: 'During a team project, a colleague disagrees with your approach. How do you handle this?',
    options: [
      'Ignore them and continue with your approach',
      'Listen to their perspective, discuss pros/cons, and find common ground',
      'Escalate to your manager immediately',
      'Agree with them to avoid conflict',
    ],
    correct: 1,
  },
  {
    id: 2, type: 'Communication', timer: 45,
    question: 'You need to present a complex technical concept to a non-technical stakeholder. What is the best approach?',
    options: [
      'Use all technical terminology to sound credible',
      'Send them documentation and skip the meeting',
      'Use simple analogies, visual aids, and focus on business impact',
      'Tell them it is too complex to explain',
    ],
    correct: 2,
  },
  {
    id: 3, type: 'Communication', timer: 45,
    question: "You realize you won't meet a project deadline. What do you do?",
    options: [
      'Wait until the deadline passes, then explain',
      'Inform stakeholders early, explain the situation, and propose a revised timeline',
      'Work overtime without telling anyone',
      'Blame other team members for the delay',
    ],
    correct: 1,
  },
  {
    id: 4, type: 'Technical', timer: 60,
    question: 'What is the time complexity of searching in a balanced Binary Search Tree?',
    options: ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'],
    correct: 2,
  },
  {
    id: 5, type: 'Technical', timer: 60,
    question: 'Which design pattern creates objects without specifying their exact class?',
    options: ['Observer Pattern', 'Factory Pattern', 'Singleton Pattern', 'Decorator Pattern'],
    correct: 1,
  },
  {
    id: 6, type: 'Technical', timer: 60,
    question: 'Which HTTP status code indicates a resource was successfully created?',
    options: ['200 OK', '201 Created', '204 No Content', '301 Moved Permanently'],
    correct: 1,
  },
  {
    id: 7, type: 'Technical', timer: 60,
    question: 'What is the primary purpose of database indexing?',
    options: [
      'To encrypt data at rest',
      'To speed up data retrieval at the cost of write performance',
      'To compress the database size',
      'To create automatic backups',
    ],
    correct: 1,
  },
  {
    id: 8, type: 'Technical', timer: 60,
    question: 'Which SOLID principle states a class should have only one reason to change?',
    options: [
      'Open/Closed Principle',
      'Liskov Substitution Principle',
      'Single Responsibility Principle',
      'Dependency Inversion Principle',
    ],
    correct: 2,
  },
];

const COMM_COUNT = allQuestions.filter(q => q.type === 'Communication').length;
const TECH_COUNT = allQuestions.filter(q => q.type === 'Technical').length;

const VideoScreeningSimple = ({ candidateId, onComplete }) => {
  const [qIndex, setQIndex] = useState(0);
  const [phase, setPhase] = useState('question'); // question | review | timeout
  const [timeLeft, setTimeLeft] = useState(allQuestions[0].timer);
  const [selected, setSelected] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [isPaused, setIsPaused] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [scores, setScores] = useState(null);
  const timerRef = useRef(null);

  // Start/restart timer when question phase begins
  useEffect(() => {
    if (phase !== 'question' || isPaused) return;
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setTimeLeft(t => {
        if (t <= 1) {
          clearInterval(timerRef.current);
          setPhase('timeout');
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [phase, qIndex, isPaused]);

  // Auto-advance after review
  useEffect(() => {
    if (phase !== 'review') return;
    const t = setTimeout(advanceQuestion, 3500);
    return () => clearTimeout(t);
  }, [phase, qIndex]);

  const handleSelect = (idx) => {
    if (phase !== 'question') return;
    clearInterval(timerRef.current);
    setSelected(idx);
    const correct = idx === allQuestions[qIndex].correct;
    setAnswers(prev => [...prev, { qId: allQuestions[qIndex].id, type: allQuestions[qIndex].type, correct, selected: idx }]);
    setPhase('review');
  };

  const handleTimeoutSkip = () => {
    setAnswers(prev => [...prev, { qId: allQuestions[qIndex].id, type: allQuestions[qIndex].type, correct: false, selected: -1 }]);
    advanceQuestion();
  };

  const togglePause = () => {
    if (phase !== 'question') return;
    if (isPaused) {
      setIsPaused(false);
    } else {
      clearInterval(timerRef.current);
      setIsPaused(true);
    }
  };

  const advanceQuestion = () => {
    if (qIndex < allQuestions.length - 1) {
      setQIndex(i => i + 1);
      setPhase('question');
      setSelected(null);
      setIsPaused(false);
      setTimeLeft(allQuestions[qIndex + 1]?.timer ?? 60);
    } else {
      finishScreening();
    }
  };

  const finishScreening = async () => {
    const allAnswers = [...answers];
    const comm = allAnswers.filter(a => a.type === 'Communication');
    const tech = allAnswers.filter(a => a.type === 'Technical');
    const commCorrect = comm.filter(a => a.correct).length;
    const techCorrect = tech.filter(a => a.correct).length;
    const communicationScore = parseFloat(((commCorrect / Math.max(comm.length, 1)) * 10).toFixed(1));
    const technicalScore = parseFloat(((techCorrect / Math.max(tech.length, 1)) * 10).toFixed(1));
    const confidenceScore = parseFloat((communicationScore * 0.4 + technicalScore * 0.6).toFixed(1));
    const result = { communicationScore, technicalScore, confidenceScore, commCorrect, techCorrect };
    setScores(result);
    setCompleted(true);
    try {
      const token = localStorage.getItem('access_token');
      if (candidateId && token) {
        await fetch(
          `${API}/candidates/${candidateId}/video-scores?confidence_score=${confidenceScore}&technical_score=${technicalScore}`,
          { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
        );
      }
    } catch (e) { /* non-blocking */ }
    if (onComplete) setTimeout(onComplete, 3000);
  };

  // ── Completion screen ──────────────────────────────────────────────────────
  if (completed && scores) {
    return (
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-6">
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring' }}
          className="w-18 h-18 w-[72px] h-[72px] bg-success/10 rounded-full flex items-center justify-center mx-auto mb-5">
          <CheckCircle2 className="w-9 h-9 text-success" />
        </motion.div>
        <h3 className="text-2xl font-bold text-foreground mb-6">Screening Complete!</h3>
        <div className="grid grid-cols-3 gap-3 mb-6">
          {[
            { label: 'Communication', value: scores.communicationScore, correct: scores.commCorrect, total: COMM_COUNT, color: 'blue' },
            { label: 'Technical', value: scores.technicalScore, correct: scores.techCorrect, total: TECH_COUNT, color: 'purple' },
            { label: 'Overall', value: scores.confidenceScore, correct: scores.commCorrect + scores.techCorrect, total: allQuestions.length, color: 'green' },
          ].map(({ label, value, correct, total, color }, i) => (
            <motion.div key={label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
              className={`rounded-2xl p-4 text-center border ${color === 'green' ? 'bg-success/5 border-success/20' : color === 'blue' ? 'bg-blue-50 border-blue-100' : 'bg-purple-50 border-purple-100'}`}>
              <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">{label}</div>
              <div className={`text-3xl font-black mb-0.5 ${color === 'green' ? 'text-success' : color === 'blue' ? 'text-blue-600' : 'text-purple-600'}`}>
                {value}<span className="text-base opacity-50">/10</span>
              </div>
              <div className="text-xs text-muted-foreground">{correct}/{total} correct</div>
            </motion.div>
          ))}
        </div>
        <p className="text-sm text-muted-foreground animate-pulse">Responses recorded. Proceeding...</p>
      </motion.div>
    );
  }

  const q = allQuestions[qIndex];
  const progress = (qIndex / allQuestions.length) * 100;
  const isCorrect = selected === q.correct;
  const timerPct = (timeLeft / q.timer) * 100;

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold text-muted-foreground">
          Question {qIndex + 1} <span className="text-slate-300">/</span> {allQuestions.length}
        </span>
        <div className="flex items-center gap-2">
          {phase === 'question' && (
            <button onClick={togglePause}
              className="text-xs font-semibold px-3 py-1.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors">
              {isPaused ? '▶ Resume' : '⏸ Pause'}
            </button>
          )}
          <span className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full ${q.type === 'Technical' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>
            {q.type === 'Technical' ? <Code className="w-3.5 h-3.5" /> : <MessageCircle className="w-3.5 h-3.5" />}
            {q.type}
          </span>
          <span className={`flex items-center gap-1.5 text-sm font-bold px-3 py-1.5 rounded-full border transition-colors ${
            isPaused ? 'bg-amber-50 text-amber-600 border-amber-200'
            : timeLeft <= 10 ? 'bg-red-50 text-red-600 border-red-200 animate-pulse'
            : 'bg-slate-50 text-slate-700 border-slate-200'
          }`}>
            <Clock className="w-4 h-4" />
            {isPaused ? 'Paused' : `${timeLeft}s`}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 w-full bg-slate-100 rounded-full mb-6 overflow-hidden">
        <motion.div className="h-full bg-primary rounded-full" animate={{ width: `${progress}%` }} transition={{ duration: 0.4 }} />
      </div>

      {/* Timer ring bar */}
      {phase === 'question' && !isPaused && (
        <div className="h-1 w-full bg-slate-100 rounded-full mb-5 overflow-hidden">
          <motion.div
            className={`h-full rounded-full transition-colors ${timeLeft <= 10 ? 'bg-red-400' : 'bg-emerald-400'}`}
            animate={{ width: `${timerPct}%` }}
            transition={{ duration: 0.9, ease: 'linear' }}
          />
        </div>
      )}

      {/* Question */}
      <motion.div key={`q-${q.id}`} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }}
        className="bg-slate-50 border border-slate-200 rounded-2xl p-6 mb-5 shadow-sm">
        <p className="text-base sm:text-lg font-bold text-foreground leading-relaxed">{q.question}</p>
      </motion.div>

      {/* Options / Timeout / Review */}
      <AnimatePresence mode="wait">
        {phase === 'timeout' && (
          <motion.div key="timeout" initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }}
            className="bg-amber-50 border-2 border-amber-200 rounded-2xl p-8 text-center">
            <div className="w-14 h-14 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Clock className="w-7 h-7 text-amber-600" />
            </div>
            <h3 className="text-lg font-bold text-amber-900 mb-2">Time's Up!</h3>
            <p className="text-sm text-amber-700 mb-5">No worries — let's move to the next question.</p>
            <button onClick={handleTimeoutSkip}
              className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-white rounded-xl font-semibold text-sm transition-colors shadow-md shadow-amber-200">
              Continue →
            </button>
          </motion.div>
        )}

        {phase === 'question' && (
          <motion.div key="options" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-2.5">
            {q.options.map((opt, i) => (
              <motion.button key={i} whileHover={{ scale: 1.01, x: 3 }} whileTap={{ scale: 0.99 }}
                onClick={() => handleSelect(i)}
                className="w-full text-left p-4 rounded-xl border-2 border-slate-100 bg-white hover:border-primary/40 hover:bg-primary/5 hover:shadow-sm text-foreground text-sm font-medium transition-all group">
                <span className="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-slate-100 text-slate-500 font-bold text-xs mr-3 group-hover:bg-primary group-hover:text-white transition-colors">
                  {String.fromCharCode(65 + i)}
                </span>
                {opt}
              </motion.button>
            ))}
          </motion.div>
        )}

        {phase === 'review' && (
          <motion.div key="review" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-2.5">
            {q.options.map((opt, i) => {
              const isSel = i === selected;
              const isCorr = i === q.correct;
              return (
                <div key={i} className={`w-full p-4 rounded-xl border-2 text-sm font-medium flex items-center justify-between transition-all ${
                  isCorr ? 'border-success bg-success/5' : isSel && !isCorrect ? 'border-red-300 bg-red-50' : 'border-slate-100 bg-white opacity-60'
                }`}>
                  <div className="flex items-center gap-3">
                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-lg font-bold text-xs ${
                      isCorr ? 'bg-success text-white' : isSel && !isCorrect ? 'bg-red-400 text-white' : 'bg-slate-100 text-slate-400'
                    }`}>{String.fromCharCode(65 + i)}</span>
                    <span>{opt}</span>
                  </div>
                  {isCorr && <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0" />}
                  {isSel && !isCorrect && <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />}
                </div>
              );
            })}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}
              className="mt-4 p-3 bg-slate-50 rounded-xl border border-slate-200 text-center text-sm text-muted-foreground">
              {isCorrect ? '🎉 Correct!' : '📝 See the correct answer above.'} Next question in a moment...
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default VideoScreeningSimple;

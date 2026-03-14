import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Clock, Video, Code, MessageCircle } from 'lucide-react';

const communicationQuestions = [
  {
    id: 1, type: 'Communication', timer: 30,
    question: 'During a team project, a colleague disagrees with your approach. How do you handle this?',
    options: [
      'Ignore them and continue with your approach',
      'Listen to their perspective, discuss pros/cons, and find common ground',
      'Escalate to your manager immediately',
      'Agree with them to avoid conflict'
    ],
    correct: 1,
  },
  {
    id: 2, type: 'Communication', timer: 30,
    question: 'You need to present a complex technical concept to a non-technical stakeholder. What is the best approach?',
    options: [
      'Use all technical terminology to sound credible',
      'Send them documentation and skip the meeting',
      'Use simple analogies, visual aids, and focus on business impact',
      'Tell them it is too complex to explain'
    ],
    correct: 2,
  },
  {
    id: 3, type: 'Communication', timer: 30,
    question: "You realize you won't meet a project deadline. What do you do?",
    options: [
      'Wait until the deadline passes, then explain',
      'Inform stakeholders early, explain the situation, and propose a revised timeline',
      'Work overtime without telling anyone to meet the deadline',
      'Blame other team members for the delay'
    ],
    correct: 1,
  },
];

const technicalQuestions = [
  {
    id: 4, type: 'Technical', timer: 45,
    question: 'What is the time complexity of searching for an element in a balanced Binary Search Tree?',
    options: ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'],
    correct: 2,
  },
  {
    id: 5, type: 'Technical', timer: 45,
    question: 'Which design pattern is used when you want to create objects without specifying their exact class?',
    options: ['Observer Pattern', 'Factory Pattern', 'Singleton Pattern', 'Decorator Pattern'],
    correct: 1,
  },
  {
    id: 6, type: 'Technical', timer: 45,
    question: 'In REST API design, which HTTP status code indicates a resource was successfully created?',
    options: ['200 OK', '201 Created', '204 No Content', '301 Moved Permanently'],
    correct: 1,
  },
  {
    id: 7, type: 'Technical', timer: 45,
    question: 'What is the primary purpose of database indexing?',
    options: [
      'To encrypt data at rest',
      'To speed up data retrieval operations at the cost of write performance',
      'To compress the database size',
      'To create backups automatically'
    ],
    correct: 1,
  },
  {
    id: 8, type: 'Technical', timer: 45,
    question: 'Which principle states that a class should have only one reason to change?',
    options: [
      'Open/Closed Principle',
      'Liskov Substitution Principle',
      'Single Responsibility Principle',
      'Dependency Inversion Principle'
    ],
    correct: 2,
  },
];

const allQuestions = [...communicationQuestions, ...technicalQuestions];

const VideoScreeningSimple = ({ candidateId, onComplete }) => {
  const [qIndex, setQIndex] = useState(0);
  const [phase, setPhase] = useState('question'); // question | review | timeout | done
  const [timeLeft, setTimeLeft] = useState(allQuestions[0].timer);
  const [selected, setSelected] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [completed, setCompleted] = useState(false);
  const [scores, setScores] = useState(null);
  const [isPaused, setIsPaused] = useState(false);
  const timerRef = useRef(null);

  // Question timer countdown
  useEffect(() => {
    if (phase !== 'question') return;
    setTimeLeft(allQuestions[qIndex].timer);
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(timerRef.current);
          // Don't auto-select - just show time's up message
          setPhase('timeout');
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [phase, qIndex]);

  // Review phase timer (5 seconds)
  useEffect(() => {
    if (phase !== 'review') return;
    const reviewTimer = setTimeout(() => {
      handleNext();
    }, 4000);
    return () => clearTimeout(reviewTimer);
  }, [phase, qIndex]);

  const handleSelect = (idx) => {
    if (phase !== 'question' && phase !== 'timeout') return;
    clearInterval(timerRef.current);
    setSelected(idx);
    const correct = idx === allQuestions[qIndex].correct;
    setAnswers((prev) => [...prev, { qId: allQuestions[qIndex].id, type: allQuestions[qIndex].type, correct, selected: idx }]);
    setPhase('review');
  };

  const handleSkip = () => {
    if (phase !== 'timeout') return;
    clearInterval(timerRef.current);
    setSelected(-1);
    setAnswers((prev) => [...prev, { qId: allQuestions[qIndex].id, type: allQuestions[qIndex].type, correct: false, selected: -1 }]);
    handleNext();
  };

  const togglePause = () => {
    if (phase !== 'question') return;
    if (isPaused) {
      // Resume
      setIsPaused(false);
      timerRef.current = setInterval(() => {
        setTimeLeft((t) => {
          if (t <= 1) {
            clearInterval(timerRef.current);
            setPhase('timeout');
            return 0;
          }
          return t - 1;
        });
      }, 1000);
    } else {
      // Pause
      setIsPaused(true);
      clearInterval(timerRef.current);
    }
  };

  const handleNext = () => {
    if (qIndex < allQuestions.length - 1) {
      setQIndex((i) => i + 1);
      setPhase('question');
      setSelected(null);
    } else {
      finishScreening();
    }
  };

  const finishScreening = async () => {
    const commAnswers = answers.filter(a => a.type === 'Communication');
    const techAnswers = answers.filter(a => a.type === 'Technical');
    const commCorrect = commAnswers.filter(a => a.correct).length;
    const techCorrect = techAnswers.filter(a => a.correct).length;
    
    const communicationScore = parseFloat(((commCorrect / Math.max(commAnswers.length, 1)) * 10).toFixed(1));
    const technicalScore = parseFloat(((techCorrect / Math.max(techAnswers.length, 1)) * 10).toFixed(1));
    const confidenceScore = parseFloat(((communicationScore * 0.4 + technicalScore * 0.6)).toFixed(1));

    setScores({ communicationScore, technicalScore, confidenceScore, commCorrect, techCorrect, total: answers.length });

    try {
      const token = localStorage.getItem('access_token');
      if (candidateId && token) {
        await fetch(
          `http://localhost:8000/api/v1/candidates/${candidateId}/video-scores?confidence_score=${confidenceScore}&technical_score=${technicalScore}`,
          { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
        );
      }
    } catch (e) {
      console.error('Score save failed:', e);
    }

    setCompleted(true);
    if (onComplete) setTimeout(() => onComplete(), 3000);
  };

  if (completed && scores) {
    return (
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-8">
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }} className="w-20 h-20 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle2 className="w-10 h-10 text-success" />
        </motion.div>
        <h3 className="text-2xl font-bold text-foreground mb-6">Screening Complete!</h3>
        
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-blue-50/50 border border-blue-100 rounded-2xl p-5 text-center shadow-sm">
            <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Communication</div>
            <div className="text-3xl font-black text-blue-600 mb-1">{scores.communicationScore}<span className="text-lg text-blue-400">/10</span></div>
            <div className="text-xs text-muted-foreground">{scores.commCorrect}/{communicationQuestions.length} correct</div>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-purple-50/50 border border-purple-100 rounded-2xl p-5 text-center shadow-sm">
            <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Technical</div>
            <div className="text-3xl font-black text-purple-600 mb-1">{scores.technicalScore}<span className="text-lg text-purple-400">/10</span></div>
            <div className="text-xs text-muted-foreground">{scores.techCorrect}/{technicalQuestions.length} correct</div>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-success/5 border border-success/20 rounded-2xl p-5 text-center shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 bg-success/10 rounded-bl-full"></div>
            <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1 relative z-10">Overall</div>
            <div className="text-3xl font-black text-success mb-1 relative z-10">{scores.confidenceScore}<span className="text-lg text-success/60">/10</span></div>
            <div className="text-xs text-muted-foreground relative z-10">{scores.commCorrect + scores.techCorrect}/{scores.total} total</div>
          </motion.div>
        </div>
        
        <p className="text-sm text-muted-foreground animate-pulse">Your responses have been recorded and analyzed. Proceeding...</p>
      </motion.div>
    );
  }

  const q = allQuestions[qIndex];
  const progress = ((qIndex) / allQuestions.length) * 100;
  const isCorrect = selected === q.correct;

  return (
    <div className="w-full">
      {/* Header Info */}
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm font-semibold text-muted-foreground">Question {qIndex + 1} of {allQuestions.length}</span>
        <div className="flex items-center gap-3">
          {phase === 'question' && (
            <button
              onClick={togglePause}
              className="flex items-center text-xs font-bold px-3 py-1.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
            >
              {isPaused ? '▶️ Resume' : '⏸️ Pause'}
            </button>
          )}
          <span className={`flex items-center text-xs font-bold px-3 py-1.5 rounded-full ${q.type === 'Technical' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>
            {q.type === 'Technical' ? <Code className="w-3.5 h-3.5 mr-1.5" /> : <MessageCircle className="w-3.5 h-3.5 mr-1.5" />}
            {q.type}
          </span>
          <span className={`flex items-center text-sm font-bold px-3 py-1.5 rounded-full border ${timeLeft <= 10 ? 'bg-red-50 text-red-600 border-red-200 animate-pulse' : isPaused ? 'bg-amber-50 text-amber-600 border-amber-200' : 'bg-slate-50 text-slate-700 border-slate-200'}`}>
            <Clock className="w-4 h-4 mr-1.5" />
            {isPaused ? 'Paused' : `${timeLeft}s`}
          </span>
        </div>
      </div>
      
      {/* Progress Bar */}
      <div className="h-2 w-full bg-slate-100 rounded-full mb-8 overflow-hidden">
        <motion.div 
          className="h-full bg-primary"
          initial={{ width: `${((qIndex) / allQuestions.length) * 100}%` }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>

      {/* Question Card */}
      <motion.div 
        key={`q-${q.id}`}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        className="bg-slate-50/80 border border-slate-200 rounded-2xl p-6 sm:p-8 mb-6 shadow-sm"
      >
        <h3 className="text-lg sm:text-xl font-bold text-foreground leading-relaxed">{q.question}</h3>
      </motion.div>

      {/* Options */}
      <div className="space-y-3">
        <AnimatePresence mode="wait">
          {phase === 'timeout' ? (
            <motion.div 
              key="timeout" 
              initial={{ opacity: 0, scale: 0.95 }} 
              animate={{ opacity: 1, scale: 1 }}
              className="bg-amber-50 border-2 border-amber-200 rounded-2xl p-8 text-center"
            >
              <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Clock className="w-8 h-8 text-amber-600" />
              </div>
              <h3 className="text-xl font-bold text-amber-900 mb-2">Time's Up!</h3>
              <p className="text-amber-700 mb-6">You didn't answer this question in time. Don't worry, let's move to the next one.</p>
              <button
                onClick={handleSkip}
                className="px-6 py-3 bg-amber-600 hover:bg-amber-700 text-white rounded-xl font-semibold transition-colors"
              >
                Continue to Next Question
              </button>
            </motion.div>
          ) : phase === 'question' ? (
            <motion.div 
              key="options" 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="space-y-3"
            >
              {q.options.map((opt, i) => (
                <motion.button
                  key={i}
                  whileHover={{ scale: 1.01, x: 4 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => handleSelect(i)}
                  className="w-full text-left p-4 rounded-xl border-2 border-slate-100 bg-white hover:border-primary/50 hover:bg-primary/5 hover:shadow-sm text-foreground text-sm sm:text-base font-medium transition-all group"
                >
                  <span className="inline-block w-8 h-8 rounded-lg bg-slate-100 text-slate-500 font-bold text-center leading-8 mr-4 group-hover:bg-primary group-hover:text-white transition-colors">
                    {String.fromCharCode(65 + i)}
                  </span>
                  {opt}
                </motion.button>
              ))}
            </motion.div>
          ) : (
            <motion.div 
              key="review" 
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              className="space-y-3"
            >
              {q.options.map((opt, i) => {
                const isSelectedOpt = i === selected;
                const isCorrectOpt = i === q.correct;
                
                let containerClass = "w-full text-left p-4 rounded-xl border-2 text-sm sm:text-base font-medium flex items-center justify-between ";
                let optLetterClass = "inline-block w-8 h-8 rounded-lg font-bold text-center leading-8 mr-4 ";
                
                if (isCorrectOpt) {
                  containerClass += "border-success bg-success/5 text-foreground";
                  optLetterClass += "bg-success text-white";
                } else if (isSelectedOpt && !isCorrect) {
                  containerClass += "border-destructive bg-destructive/5 text-foreground";
                  optLetterClass += "bg-destructive text-white";
                } else {
                  containerClass += "border-slate-100 bg-white text-muted-foreground opacity-60";
                  optLetterClass += "bg-slate-100 text-slate-400";
                }

                return (
                  <div key={i} className={containerClass}>
                    <div className="flex items-center">
                      <span className={optLetterClass}>{String.fromCharCode(65 + i)}</span>
                      <span>{opt}</span>
                    </div>
                    {isCorrectOpt && <CheckCircle2 className="w-6 h-6 text-success flex-shrink-0 ml-4" />}
                    {isSelectedOpt && !isCorrect && <AlertCircle className="w-6 h-6 text-destructive flex-shrink-0 ml-4" />}
                  </div>
                );
              })}
              
              <motion.div 
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
                className="mt-6 p-4 bg-slate-50 rounded-xl border border-slate-200 text-center text-sm text-muted-foreground"
              >
                {isCorrect ? '🎉 Great job!' : '📝 Review the correct answer above.'} Moving to next question shortly...
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default VideoScreeningSimple;

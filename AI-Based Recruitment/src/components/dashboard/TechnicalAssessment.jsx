import { useState, useEffect, useRef } from 'react';
import { X, Clock, CheckCircle, XCircle, ChevronRight, Award, RotateCcw } from 'lucide-react';

// Question banks by assessment type
const QUESTION_BANKS = {
  coding: [
    { q: 'What is the output of `typeof null` in JavaScript?', options: ['"null"', '"undefined"', '"object"', '"boolean"'], correct: 2, time: 30 },
    { q: 'Which data structure uses LIFO (Last In, First Out)?', options: ['Queue', 'Stack', 'Linked List', 'Hash Map'], correct: 1, time: 30 },
    { q: 'What is the time complexity of binary search?', options: ['O(n)', 'O(n²)', 'O(log n)', 'O(1)'], correct: 2, time: 30 },
    { q: 'Which keyword is used to handle exceptions in Python?', options: ['catch', 'except', 'handle', 'error'], correct: 1, time: 25 },
    { q: 'What does the `===` operator check in JavaScript?', options: ['Value only', 'Type only', 'Value and type', 'Reference'], correct: 2, time: 25 },
    { q: 'Which sorting algorithm has the best average time complexity?', options: ['Bubble Sort O(n²)', 'Merge Sort O(n log n)', 'Selection Sort O(n²)', 'Insertion Sort O(n²)'], correct: 1, time: 30 },
    { q: 'What is a closure in programming?', options: ['A function with no return value', 'A function that captures variables from its outer scope', 'A class constructor', 'A loop termination condition'], correct: 1, time: 35 },
    { q: 'What is the purpose of the `virtual` keyword in C++?', options: ['Memory allocation', 'Enable polymorphism via dynamic dispatch', 'Create constants', 'Thread safety'], correct: 1, time: 30 },
    { q: 'In SQL, which command is used to remove duplicate rows from a result?', options: ['UNIQUE', 'DISTINCT', 'REMOVE', 'FILTER'], correct: 1, time: 25 },
    { q: 'What is Big O notation for?', options: ['Measuring exact runtime', 'Describing upper bound of algorithm growth rate', 'Counting lines of code', 'Measuring memory usage only'], correct: 1, time: 30 },
  ],
  'system-design': [
    { q: 'Which load balancing algorithm distributes requests in sequential order?', options: ['Random', 'Round Robin', 'Least Connections', 'IP Hash'], correct: 1, time: 40 },
    { q: 'What is the CAP theorem about?', options: ['CPU, API, Performance', 'Consistency, Availability, Partition tolerance — pick 2', 'Cache, Application, Persistence', 'Compute, Access, Protocol'], correct: 1, time: 40 },
    { q: 'Which pattern is best for handling 10M concurrent WebSocket connections?', options: ['Single monolithic server', 'Event-driven architecture with horizontal scaling', 'Synchronous request-response', 'Batch processing'], correct: 1, time: 45 },
    { q: 'What is the primary benefit of database sharding?', options: ['Data encryption', 'Horizontal scalability by distributing data across servers', 'Faster single queries', 'Simpler schema design'], correct: 1, time: 40 },
    { q: 'In microservices, what is a circuit breaker pattern used for?', options: ['Load balancing', 'Preventing cascading failures across services', 'Database replication', 'API versioning'], correct: 1, time: 40 },
    { q: 'What caching strategy updates cache only when data is requested?', options: ['Write-through', 'Write-behind', 'Cache-aside (lazy loading)', 'Write-around'], correct: 2, time: 40 },
    { q: 'Which message broker supports publish/subscribe at massive scale?', options: ['SQLite', 'Apache Kafka', 'Redis only', 'MongoDB'], correct: 1, time: 35 },
    { q: 'What is event sourcing?', options: ['Logging errors', 'Storing state changes as a sequence of events', 'Real-time monitoring', 'Load testing'], correct: 1, time: 40 },
  ],
  'take-home': [
    { q: 'You are designing a URL shortener. Which data structure is most efficient for mapping short URLs to original URLs?', options: ['Array', 'Hash Map', 'Binary Tree', 'Stack'], correct: 1, time: 60 },
    { q: 'For a real-time chat application, which protocol is most suitable?', options: ['HTTP polling every 1 second', 'WebSocket for persistent bidirectional communication', 'FTP', 'SMTP'], correct: 1, time: 50 },
    { q: 'If designing a rate limiter, which algorithm allows burst traffic while maintaining average rate?', options: ['Fixed Window', 'Token Bucket', 'Simple Counter', 'Random Delay'], correct: 1, time: 50 },
    { q: 'How would you handle file uploads for a document management system?', options: ['Store files in the database as BLOBs', 'Use object storage (S3) with metadata in database', 'Store on local disk only', 'Email files to admin'], correct: 1, time: 50 },
    { q: 'Which approach is best for searching through millions of text documents?', options: ['Linear scan', 'Full-text search engine like Elasticsearch', 'SQL LIKE queries', 'Manual review'], correct: 1, time: 50 },
  ],
  mcq: [
    { q: 'What is the purpose of Docker?', options: ['Code editor', 'Containerization of applications', 'Database management', 'Network monitoring'], correct: 1, time: 25 },
    { q: 'Which HTTP method is idempotent?', options: ['POST', 'PATCH', 'PUT', 'None of the above'], correct: 2, time: 25 },
    { q: 'What does CI/CD stand for?', options: ['Code Integration / Code Deployment', 'Continuous Integration / Continuous Delivery', 'Cloud Infrastructure / Cloud Design', 'Component Interface / Component Design'], correct: 1, time: 25 },
    { q: 'Which is NOT a valid JavaScript data type?', options: ['Symbol', 'BigInt', 'Float', 'Undefined'], correct: 2, time: 25 },
    { q: 'What is the purpose of a foreign key in a database?', options: ['Primary index', 'Establish a relationship between tables', 'Encrypt data', 'Auto-increment values'], correct: 1, time: 25 },
    { q: 'What does the `async` keyword do in JavaScript?', options: ['Makes function synchronous', 'Makes function return a Promise', 'Creates a new thread', 'Stops execution'], correct: 1, time: 25 },
    { q: 'What is the difference between TCP and UDP?', options: ['TCP is faster', 'TCP guarantees delivery, UDP does not', 'UDP is more secure', 'No difference'], correct: 1, time: 30 },
    { q: 'Which design principle suggests depending on abstractions, not concretions?', options: ['DRY', 'KISS', 'Dependency Inversion', 'YAGNI'], correct: 2, time: 30 },
    { q: 'What is a deadlock?', options: ['A slow query', 'Two processes blocking each other indefinitely', 'Memory overflow', 'Network timeout'], correct: 1, time: 25 },
    { q: 'Which Git command combines changes from one branch into another?', options: ['git push', 'git merge', 'git clone', 'git init'], correct: 1, time: 20 },
    { q: 'What is the primary advantage of NoSQL databases?', options: ['ACID compliance', 'Flexible schema and horizontal scalability', 'Better for joins', 'Smaller storage'], correct: 1, time: 25 },
    { q: 'What does CORS stand for?', options: ['Cross-Origin Resource Sharing', 'Common Object Request System', 'Client-Origin Response Service', 'Cross-Object Resource Standard'], correct: 0, time: 25 },
  ],
};

const TYPE_META = {
  coding: { label: 'Coding Challenge', color: '#2563eb', bgColor: '#eff6ff', icon: '💻', totalTime: 300 },
  'system-design': { label: 'System Design', color: '#7c3aed', bgColor: '#f5f3ff', icon: '🏗️', totalTime: 360 },
  'take-home': { label: 'Take-Home Project', color: '#ea580c', bgColor: '#fff7ed', icon: '📋', totalTime: 300 },
  mcq: { label: 'MCQ Assessment', color: '#16a34a', bgColor: '#f0fdf4', icon: '📝', totalTime: 300 },
};

const TechnicalAssessment = ({ type, candidateName, candidateSkills = [], onClose, onComplete }) => {
  const questions = QUESTION_BANKS[type] || QUESTION_BANKS.mcq;
  const meta = TYPE_META[type] || TYPE_META.mcq;
  
  const [qIndex, setQIndex] = useState(0);
  const [phase, setPhase] = useState('intro'); // intro | question | review | results
  const [timeLeft, setTimeLeft] = useState(questions[0]?.time || 30);
  const [totalTime, setTotalTime] = useState(meta.totalTime);
  const [selected, setSelected] = useState(null);
  const [answers, setAnswers] = useState([]);
  const timerRef = useRef(null);
  const totalTimerRef = useRef(null);

  // Per-question timer
  useEffect(() => {
    if (phase !== 'question') return;
    setTimeLeft(questions[qIndex]?.time || 30);
    timerRef.current = setInterval(() => {
      setTimeLeft(t => {
        if (t <= 1) {
          clearInterval(timerRef.current);
          handleSelect(-1); // auto-skip
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [phase, qIndex]);

  // Total assessment timer
  useEffect(() => {
    if (phase !== 'question' && phase !== 'review') return;
    totalTimerRef.current = setInterval(() => {
      setTotalTime(t => {
        if (t <= 1) {
          clearInterval(totalTimerRef.current);
          finishAssessment();
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(totalTimerRef.current);
  }, [phase]);

  const handleSelect = (idx) => {
    if (phase !== 'question') return;
    clearInterval(timerRef.current);
    setSelected(idx);
    const correct = idx === questions[qIndex].correct;
    setAnswers(prev => [...prev, { qIndex, correct, selected: idx, timedOut: idx === -1 }]);
    setPhase('review');
    setTimeout(() => handleNext(), 3000);
  };

  const handleNext = () => {
    if (qIndex < questions.length - 1) {
      setQIndex(i => i + 1);
      setPhase('question');
      setSelected(null);
    } else {
      finishAssessment();
    }
  };

  const finishAssessment = () => {
    clearInterval(timerRef.current);
    clearInterval(totalTimerRef.current);
    setPhase('results');
  };

  const score = answers.filter(a => a.correct).length;
  const total = questions.length;
  const percentage = Math.round((score / total) * 100);
  const totalMins = Math.floor(totalTime / 60);
  const totalSecs = totalTime % 60;

  // --- Intro screen ---
  if (phase === 'intro') {
    return (
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div className="bg-slate-50 rounded-2xl border border-border/60 shadow-2xl w-full max-w-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-border/60 bg-white flex justify-between items-center">
            <h2 className="text-lg font-bold text-foreground">{meta.icon} {meta.label}</h2>
            <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-full text-slate-600"><X className="w-5 h-5" /></button>
          </div>
          <div className="p-8 text-center space-y-4">
            <div className="w-20 h-20 rounded-full flex items-center justify-center text-4xl mx-auto" style={{ backgroundColor: meta.bgColor }}>
              {meta.icon}
            </div>
            <h3 className="text-xl font-bold text-foreground">{meta.label}</h3>
            <p className="text-sm text-slate-600">For: <span className="text-foreground font-medium">{candidateName}</span></p>
            <div className="grid grid-cols-3 gap-3 text-center mt-4">
              <div className="bg-white rounded-lg p-3 border border-border/60">
                <div className="text-lg font-bold text-foreground">{questions.length}</div>
                <div className="text-xs text-muted-foreground">Questions</div>
              </div>
              <div className="bg-white rounded-lg p-3 border border-border/60">
                <div className="text-lg font-bold text-foreground">{Math.floor(meta.totalTime / 60)}m</div>
                <div className="text-xs text-muted-foreground">Total Time</div>
              </div>
              <div className="bg-white rounded-lg p-3 border border-border/60">
                <div className="text-lg font-bold text-foreground">Auto</div>
                <div className="text-xs text-muted-foreground">Timed Each</div>
              </div>
            </div>
            {candidateSkills.length > 0 && (
              <div className="mt-4">
                <p className="text-xs text-muted-foreground mb-2">Aligned with candidate skills:</p>
                <div className="flex flex-wrap gap-1 justify-center">
                  {candidateSkills.slice(0, 5).map(s => (
                    <span key={s} className="px-2 py-0.5 bg-primary/10 text-primary/80 text-xs rounded border border-primary/20">{s}</span>
                  ))}
                </div>
              </div>
            )}
            <button
              onClick={() => setPhase('question')}
              className="mt-6 w-full py-3 font-semibold text-foreground rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
              style={{ backgroundColor: meta.color }}
            >
              Start Assessment <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- Results screen ---
  if (phase === 'results') {
    const grade = percentage >= 80 ? 'Excellent' : percentage >= 60 ? 'Good' : percentage >= 40 ? 'Average' : 'Needs Improvement';
    const gradeColor = percentage >= 80 ? '#16a34a' : percentage >= 60 ? '#2563eb' : percentage >= 40 ? '#ea580c' : '#dc2626';
    
    return (
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
        <div className="bg-slate-50 rounded-2xl border border-border/60 shadow-2xl w-full max-w-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-border/60 bg-white flex justify-between items-center">
            <h2 className="text-lg font-bold text-foreground">{meta.icon} {meta.label} — Results</h2>
            <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-full text-slate-600"><X className="w-5 h-5" /></button>
          </div>
          <div className="p-8 text-center space-y-6">
            <div className="w-24 h-24 rounded-full flex items-center justify-center mx-auto" style={{ backgroundColor: meta.bgColor, border: `3px solid ${gradeColor}` }}>
              <div className="text-center">
                <div className="text-2xl font-black" style={{ color: gradeColor }}>{percentage}%</div>
              </div>
            </div>
            <div>
              <p className="text-xl font-bold text-foreground">{candidateName}</p>
              <p className="text-sm font-semibold mt-1" style={{ color: gradeColor }}>{grade}</p>
            </div>
            
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-success/10 border border-success/20 rounded-lg p-3">
                <div className="text-lg font-bold text-success">{score}</div>
                <div className="text-xs text-muted-foreground">Correct</div>
              </div>
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
                <div className="text-lg font-bold text-destructive">{total - score}</div>
                <div className="text-xs text-muted-foreground">Wrong</div>
              </div>
              <div className="bg-primary/10 border border-primary/30 rounded-lg p-3">
                <div className="text-lg font-bold text-primary">{total}</div>
                <div className="text-xs text-muted-foreground">Total</div>
              </div>
            </div>

            {/* Per-question review */}
            <div className="text-left space-y-2 max-h-48 overflow-y-auto">
              {questions.map((q, i) => {
                const ans = answers.find(a => a.qIndex === i);
                const isCorrect = ans?.correct;
                return (
                  <div key={i} className="flex items-center gap-2 bg-white rounded-lg p-2 border border-border/60 text-xs">
                    {isCorrect ? <CheckCircle className="w-4 h-4 text-success shrink-0" /> : <XCircle className="w-4 h-4 text-destructive shrink-0" />}
                    <span className="text-slate-700 truncate flex-1">Q{i+1}: {q.q}</span>
                    {ans?.timedOut && <span className="text-yellow-400 text-xs shrink-0">Timed out</span>}
                  </div>
                );
              })}
            </div>

            <div className="flex gap-3 mt-4">
              <button onClick={onClose} className="flex-1 py-2.5 bg-white border border-border text-slate-700 rounded-lg text-sm font-medium hover:bg-[#243044] transition-colors">
                Close
              </button>
              {onComplete && (
                <button onClick={() => { onComplete({ type, score, total, percentage, grade }); onClose(); }}
                  className="flex-1 py-2.5 text-foreground rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                  style={{ backgroundColor: meta.color }}>
                  <Award className="w-4 h-4" /> Save Results
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // --- Question screen ---
  const q = questions[qIndex];
  const isCorrect = selected === q.correct;
  const progress = ((qIndex + (phase === 'review' ? 1 : 0)) / questions.length) * 100;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-slate-50 rounded-2xl border border-border/60 shadow-2xl w-full max-w-2xl overflow-hidden">
        <div className="px-6 py-3 border-b border-border/60 bg-white flex justify-between items-center">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-foreground">{meta.icon} {meta.label}</span>
            <span className="text-xs text-muted-foreground">Question {qIndex + 1}/{questions.length}</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-sm">
              <Clock className="w-4 h-4 text-muted-foreground" />
              <span className={`font-mono font-bold ${timeLeft <= 10 ? 'text-destructive' : 'text-slate-700'}`}>{timeLeft}s</span>
            </div>
            <div className="text-xs text-muted-foreground">
              Total: {totalMins}:{String(totalSecs).padStart(2, '0')}
            </div>
            <button onClick={onClose} className="p-1.5 hover:bg-gray-700 rounded-full text-slate-600"><X className="w-4 h-4" /></button>
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-1 bg-slate-100">
          <div className="h-full transition-all duration-300" style={{ width: `${progress}%`, backgroundColor: meta.color }} />
        </div>

        <div className="p-6 space-y-5">
          <div className="bg-white border border-border/60 rounded-xl p-5">
            <p className="text-base font-semibold text-foreground leading-relaxed">{q.q}</p>
          </div>

          <div className="space-y-3">
            {q.options.map((opt, i) => {
              let classes = 'w-full text-left p-4 rounded-xl border-2 text-sm font-medium transition-all cursor-pointer ';
              
              if (phase === 'review') {
                if (i === q.correct) {
                  classes += 'border-green-500 bg-success/10 text-success';
                } else if (i === selected && !isCorrect) {
                  classes += 'border-red-500 bg-destructive/10 text-destructive';
                } else {
                  classes += 'border-border/60 bg-white text-muted-foreground cursor-default';
                }
              } else {
                classes += 'border-border/60 bg-white text-slate-700 hover:border-blue-500/50 hover:bg-blue-500/5';
              }

              return (
                <button key={i} onClick={() => handleSelect(i)} disabled={phase !== 'question'} className={classes}>
                  <span className="font-bold mr-3 text-muted-foreground">{String.fromCharCode(65 + i)}</span>
                  {opt}
                  {phase === 'review' && i === q.correct && <span className="float-right">✓</span>}
                  {phase === 'review' && i === selected && !isCorrect && <span className="float-right">✗</span>}
                </button>
              );
            })}
          </div>

          {/* Score bar */}
          <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border/60">
            <span>Score: {answers.filter(a => a.correct).length}/{answers.length} answered</span>
            <span>{candidateName}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TechnicalAssessment;

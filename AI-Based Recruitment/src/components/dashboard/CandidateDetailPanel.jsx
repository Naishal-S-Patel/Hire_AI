import { useState, useEffect } from 'react';
import { Mail, Phone, Calendar, MapPin, Briefcase, Building2, GraduationCap, Award, Eye, CheckCircle, ClipboardCheck, BookOpen, Trash2, Loader2, UserCheck, Send } from 'lucide-react';
import FraudBadge from './FraudBadge';
import AISummaryBox from './AISummaryBox';
import SkillGraph from './SkillGraph';
import FraudReportPanel from './FraudReportPanel';
import InterviewScheduler from './InterviewScheduler';
import TechnicalAssessment from './TechnicalAssessment';
import ResumeViewer from './ResumeViewer';
import { useCandidateSummary } from '../../hooks/useCandidates';
import { getFraudReport, getSkillGraph, getResumeUrl, deleteCandidate, hireCandidate, sendAssessment } from '../../services/api';

export const CandidateDetailPanel = ({ candidate, onReject }) => {
  const [showScheduler, setShowScheduler] = useState(false);
  const [fraudData, setFraudData] = useState(null);
  const [fraudLoading, setFraudLoading] = useState(false);
  const [skillGraphData, setSkillGraphData] = useState(null);
  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [shortlisted, setShortlisted] = useState(false);
  const [showAssessment, setShowAssessment] = useState(false);
  const [assessmentType, setAssessmentType] = useState(null);
  const [assessmentResults, setAssessmentResults] = useState({});
  const [rejecting, setRejecting] = useState(false);
  const [rejected, setRejected] = useState(false);
  const [hiring, setHiring] = useState(false);
  const [hired, setHired] = useState(false);
  const [hireResult, setHireResult] = useState(null);
  const [showHireModal, setShowHireModal] = useState(false);
  const [hireForm, setHireForm] = useState({ position: 'Software Engineer', salary: 'As per company standards', department: 'Engineering' });
  const [sendingAssessment, setSendingAssessment] = useState(false);
  const [assessmentSentResult, setAssessmentSentResult] = useState(null);
  const { data: fetchedSummary, isLoading: summaryLoading } = useCandidateSummary(candidate?.id);

  const resumeUrl = candidate?.id ? getResumeUrl(candidate.id) : null;
  const summary = fetchedSummary || candidate?.summary || null;

  // Reset state when candidate changes
  useEffect(() => {
    setShortlisted(false);
    setShowAssessment(false);
    setAssessmentType(null);
    setRejected(false);
    setAssessmentResults({});
    setHired(false);
    setHireResult(null);
    setShowHireModal(false);
    setAssessmentSentResult(null);
  }, [candidate?.id]);

  useEffect(() => {
    if (!candidate?.id) return;
    if (candidate.skillMatches && candidate.skillMatches.length > 0) {
      setSkillGraphData(candidate.skillMatches);
      return;
    }
    getSkillGraph(candidate.id).then(graph => {
      if (graph?.skills) {
        setSkillGraphData(graph.skills.map(s => ({
          skill: s.name || s.skill,
          candidate_score: s.candidate_score || s.score || 0,
          jd_required: s.jd_required || 80,
        })));
      }
    }).catch(() => {});
  }, [candidate?.id]);

  useEffect(() => {
    if (!candidate?.id) return;
    if (candidate.fraudFlags && candidate.fraudFlags.length > 0) {
      setFraudData({ riskLevel: candidate.fraudRisk, fraudScore: candidate.fraudScore, flags: candidate.fraudFlags });
      return;
    }
    setFraudLoading(true);
    getFraudReport(candidate.id)
      .then(report => {
        if (report) {
          const score = report.risk_score ?? 0;
          const level = report.risk_level || (score >= 40 ? 'HIGH' : score >= 15 ? 'MEDIUM' : 'LOW');
          setFraudData({ riskLevel: level, fraudScore: score, flags: report.flags || [] });
        }
      })
      .catch(() => {})
      .finally(() => setFraudLoading(false));
  }, [candidate?.id]);

  const activeFraud = fraudData || { riskLevel: candidate?.fraudRisk || 'LOW', fraudScore: candidate?.fraudScore || 0, flags: candidate?.fraudFlags || [] };

  const handleReject = async () => {
    if (!candidate?.id) return;
    if (!confirm(`Are you sure you want to reject and remove ${(candidate.full_name || candidate.name || 'Unknown')}? This will permanently delete them from the database.`)) return;
    
    setRejecting(true);
    try {
      await deleteCandidate(candidate.id);
      setRejected(true);
      if (onReject) onReject(candidate.id);
    } catch (err) {
      console.error('Failed to reject candidate:', err);
      alert('Failed to reject candidate. Please try again.');
    } finally {
      setRejecting(false);
    }
  };

  const handleStartAssessment = (type) => {
    setAssessmentType(type);
  };

  const handleAssessmentComplete = (result) => {
    setAssessmentResults(prev => ({ ...prev, [result.type]: result }));
  };

  const handleHire = async () => {
    if (!candidate?.id) return;
    setHiring(true);
    try {
      const result = await hireCandidate(candidate.id, hireForm);
      setHired(true);
      setHireResult(result);
      setShowHireModal(false);
    } catch (err) {
      console.error('Failed to hire candidate:', err);
      alert('Failed to hire candidate. Please try again.');
    } finally {
      setHiring(false);
    }
  };

  const handleSendAssessmentEmail = async (type) => {
    if (!candidate?.id) return;
    setSendingAssessment(true);
    try {
      const result = await sendAssessment(candidate.id, type);
      setAssessmentSentResult(result);
      setTimeout(() => setAssessmentSentResult(null), 5000);
    } catch (err) {
      console.error('Failed to send assessment:', err);
      alert('Failed to send assessment email. Check candidate has a valid email.');
    } finally {
      setSendingAssessment(false);
    }
  };

  if (!candidate) {
    return (
      <div className="flex-1 h-full flex items-center justify-center bg-white border border-border/60 rounded-xl shadow-sm">
        <div className="text-center p-8">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Briefcase className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-medium text-foreground">No candidate selected</h3>
          <p className="mt-1 text-sm text-muted-foreground">Select a candidate from the list to view their full profile.</p>
        </div>
      </div>
    );
  }

  if (rejected) {
    return (
      <div className="flex-1 h-full flex items-center justify-center bg-white border border-border/60 rounded-xl shadow-sm">
        <div className="text-center p-8">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <Trash2 className="w-8 h-8 text-destructive" />
          </div>
          <h3 className="text-lg font-medium text-foreground">Candidate Rejected</h3>
          <p className="mt-1 text-sm text-muted-foreground">{(candidate.full_name || candidate.name || 'Unknown')} has been removed from the database.</p>
          <p className="mt-3 text-xs text-slate-400">Select another candidate to continue.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-white border border-border/60 rounded-xl shadow-sm overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b border-border/60 flex justify-between items-start bg-slate-50">
        <div className="flex items-center">
          <div className="w-16 h-16 bg-primary text-foreground rounded-full flex items-center justify-center text-2xl font-bold shadow-sm">
            {(candidate.full_name || candidate.name || 'Unknown').charAt(0)}
          </div>
          <div className="ml-5">
            <h2 className="text-2xl font-bold text-foreground tracking-tight">{(candidate.full_name || candidate.name || 'Unknown')}</h2>
            <p className="text-base font-medium text-primary mt-1">{candidate.role}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="inline-flex items-center px-3 py-1 bg-primary text-foreground rounded-lg text-sm font-medium shadow-sm mb-2">
            ATS Score: {(candidate.ats_score || candidate.atsScore || 0)}/100
          </div>
          <div>
            <FraudBadge riskLevel={activeFraud.riskLevel} />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar pb-20">
        {/* Contact Info */}
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border border-border/60">
            <Mail className="w-4 h-4 mr-3 text-muted-foreground" />
            {candidate.email || 'No email'}
          </div>
          <div className="flex items-center text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border border-border/60">
            <Phone className="w-4 h-4 mr-3 text-muted-foreground" />
            {candidate.phone || 'No phone'}
          </div>
          <div className="flex items-center text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border border-border/60">
            <MapPin className="w-4 h-4 mr-3 text-muted-foreground" />
            {candidate.location}
          </div>
          <div className="flex items-center text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border border-border/60">
            <Calendar className="w-4 h-4 mr-3 text-muted-foreground" />
            {(candidate.experience_years || candidate.experience || 0)}
          </div>
        </div>

        {/* AI Summary */}
        <section>
          <AISummaryBox summary={summary} isLoading={summaryLoading} />
        </section>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3 pt-4 border-t border-border/60">
          {!shortlisted ? (
            <button 
              onClick={() => setShortlisted(true)}
              className="flex-1 min-w-[120px] bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md hover:shadow-lg"
            >
              ✓ Shortlist
            </button>
          ) : (
            <div className="flex-1 min-w-[120px] bg-emerald-50 border-2 border-emerald-500 text-emerald-700 px-4 py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Shortlisted
            </div>
          )}
          
          <button 
            onClick={() => setShowScheduler(true)}
            className="flex-1 min-w-[140px] bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md hover:shadow-lg"
          >
            📅 Schedule Interview
          </button>

          {shortlisted && (
            <button 
              onClick={() => setShowAssessment(!showAssessment)}
              className="flex-1 min-w-[160px] bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2"
            >
              <ClipboardCheck className="w-4 h-4" />
              Technical Assessment
            </button>
          )}

          {resumeUrl && (
            <button
              onClick={() => setShowPdfViewer(true)}
              className="flex-none bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md hover:shadow-lg flex items-center gap-2"
            >
              <Eye size={16} />
              Preview Resume
            </button>
          )}

          {/* Hire Button */}
          {!hired && (
            <button
              onClick={() => setShowHireModal(true)}
              disabled={hiring}
              className="flex-1 min-w-[120px] bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-600 hover:to-emerald-700 text-white px-4 py-2.5 rounded-lg text-sm font-bold transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2"
            >
              {hiring ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Hiring...</>
              ) : (
                <><UserCheck className="w-4 h-4" /> Hire Candidate</>
              )}
            </button>
          )}
          {hired && (
            <div className="flex-1 min-w-[120px] bg-teal-50 border-2 border-teal-500 text-teal-700 px-4 py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Hired {hireResult?.offer_email_sent ? '✉️' : ''}
            </div>
          )}

          <button 
            onClick={handleReject}
            disabled={rejecting}
            className="flex-none bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md hover:shadow-lg flex items-center gap-2"
          >
            {rejecting ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Rejecting...</>
            ) : (
              <><Trash2 className="w-4 h-4" /> Reject</>
            )}
          </button>
        </div>

        {/* Hire Modal */}
        {showHireModal && (
          <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" onClick={() => setShowHireModal(false)}>
            <div className="bg-white border border-border/60 rounded-2xl p-6 w-full max-w-md shadow-2xl" onClick={e => e.stopPropagation()}>
              <h3 className="text-lg font-bold text-foreground mb-4 flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-teal-600" /> Hire {(candidate.full_name || candidate.name || 'Unknown')}
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Position</label>
                  <input
                    type="text"
                    value={hireForm.position}
                    onChange={e => setHireForm({...hireForm, position: e.target.value})}
                    className="w-full px-3 py-2 bg-white border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Salary / CTC</label>
                  <input
                    type="text"
                    value={hireForm.salary}
                    onChange={e => setHireForm({...hireForm, salary: e.target.value})}
                    className="w-full px-3 py-2 bg-white border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Department</label>
                  <input
                    type="text"
                    value={hireForm.department}
                    onChange={e => setHireForm({...hireForm, department: e.target.value})}
                    className="w-full px-3 py-2 bg-white border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowHireModal(false)}
                  className="flex-1 px-4 py-2.5 bg-white border border-border text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleHire}
                  disabled={hiring}
                  className="flex-1 px-4 py-2.5 bg-gradient-to-r from-teal-500 to-emerald-600 text-foreground rounded-lg text-sm font-bold hover:from-teal-600 hover:to-emerald-700 transition-all disabled:opacity-50"
                >
                  {hiring ? 'Sending Offer...' : '🎉 Confirm Hire & Send Offer'}
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-3 text-center">An offer letter will be emailed to {candidate.email}</p>
            </div>
          </div>
        )}

        {/* Assessment Sent Notification */}
        {assessmentSentResult && (
          <div className={`p-3 rounded-lg text-sm flex items-center gap-2 ${assessmentSentResult.email_sent ? 'bg-success/10 border border-success/20 text-success' : 'bg-destructive/10 border border-destructive/20 text-destructive'}`}>
            <Send className="w-4 h-4" />
            {assessmentSentResult.message}
          </div>
        )}

        {/* Technical Assessment Panel */}
        {showAssessment && shortlisted && (
          <div className="bg-purple-50 border border-purple-200 rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="w-5 h-5 text-purple-600" />
              <h3 className="text-lg font-semibold text-foreground">Technical Assessment</h3>
            </div>
            <p className="text-sm text-slate-600">Choose an assessment type for {(candidate.full_name || candidate.name || 'Unknown')}:</p>
            <div className="grid grid-cols-2 gap-3">
              {[
                { type: 'coding', label: 'Coding Challenge', desc: 'Live coding test with problem solving', icon: '💻' },
                { type: 'system-design', label: 'System Design', desc: 'Architecture and design questions', icon: '🏗️' },
                { type: 'take-home', label: 'Take-Home Project', desc: 'Assigned project with deadline', icon: '📋' },
                { type: 'mcq', label: 'MCQ Assessment', desc: 'Multiple choice technical quiz', icon: '📝' },
              ].map(item => {
                const result = assessmentResults[item.type];
                return (
                  <div key={item.type} className="relative">
                    <button 
                      onClick={() => handleStartAssessment(item.type)}
                      className={`w-full p-4 rounded-lg text-left transition-colors group ${
                        result 
                          ? 'bg-white border-2 border-success/50' 
                          : 'bg-white border border-border hover:border-purple-500/50'
                      }`}
                    >
                      <span className="text-lg mr-1">{item.icon}</span>
                      <p className="text-sm font-semibold text-slate-700 group-hover:text-purple-600 transition-colors">{item.label}</p>
                      <p className="text-xs text-muted-foreground mt-1">{item.desc}</p>
                      {result && (
                        <div className="mt-2 flex items-center gap-2">
                          <span className={`text-xs font-bold ${result.percentage >= 60 ? 'text-success' : 'text-destructive'}`}>
                            {result.percentage}% — {result.grade}
                          </span>
                          <span className="text-xs text-slate-400">({result.score}/{result.total})</span>
                        </div>
                      )}
                    </button>
                    {/* Send to Email button */}
                    <button
                      onClick={() => handleSendAssessmentEmail(item.type)}
                      disabled={sendingAssessment}
                      className="mt-1 w-full px-3 py-1.5 bg-purple-100 border border-purple-200 text-purple-700 rounded-lg text-xs font-medium hover:bg-purple-200 transition-colors flex items-center justify-center gap-1.5"
                    >
                      <Send className="w-3 h-3" />
                      {sendingAssessment ? 'Sending...' : 'Send to Candidate Email'}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Assessment Results Summary for HR */}
        {Object.keys(assessmentResults).length > 0 && (
          <div className="bg-primary/10 border border-primary/30 rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <Award className="w-4 h-4 text-primary" /> Assessment Scores
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(assessmentResults).map(([type, result]) => (
                <div key={type} className="bg-slate-50 rounded-lg p-3 border border-border/60">
                  <div className="text-xs text-muted-foreground uppercase font-semibold mb-1">{result.type.replace('-', ' ')}</div>
                  <div className={`text-xl font-bold ${result.percentage >= 60 ? 'text-success' : 'text-destructive'}`}>{result.percentage}%</div>
                  <div className="text-xs text-muted-foreground">{result.score}/{result.total} correct · {result.grade}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-8">
          {/* Skills */}
          <section>
            <h3 className="text-lg font-semibold text-foreground mb-4 tracking-tight">Technical Skills</h3>
            <div className="flex flex-wrap gap-2">
              {candidate.skills.map(skill => (
                <span key={skill} className="px-3 py-1.5 bg-primary/10 text-primary/80 rounded-lg text-sm font-medium border border-primary/20">
                  {skill}
                </span>
              ))}
            </div>
          </section>

          {/* Skill Radar Chart */}
          <section>
            <h3 className="text-lg font-semibold text-foreground mb-4 tracking-tight">Skill Match Analysis</h3>
            <div className="bg-slate-50 rounded-xl p-4 border border-border/60">
              <SkillGraph data={skillGraphData || candidate.skillMatches} />
            </div>
          </section>
        </div>
        
        <FraudReportPanel 
          riskLevel={activeFraud.riskLevel} 
          fraudScore={activeFraud.fraudScore} 
          flags={activeFraud.flags}
          isLoading={fraudLoading}
        />

        {/* Work Experience */}
        <section className="pt-2">
          <h3 className="text-lg font-semibold text-foreground mb-4 tracking-tight">Work Experience</h3>
          {candidate.work_experience && candidate.work_experience.length > 0 ? (
            <div className="space-y-3">
              {candidate.work_experience.map((exp, idx) => (
                <div key={idx} className="bg-slate-50 rounded-xl p-4 border border-border/60">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      {exp.is_internship ? (
                        <GraduationCap className="w-4 h-4 text-purple-600 mt-0.5 shrink-0" />
                      ) : (
                        <Building2 className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                      )}
                      <div>
                        <p className="text-sm font-semibold text-foreground">{exp.title}</p>
                        {exp.company && <p className="text-xs text-slate-600">{exp.company}</p>}
                      </div>
                    </div>
                    <div className="text-right shrink-0 ml-4">
                      <span className="text-xs text-muted-foreground">{exp.start} – {exp.end}</span>
                      {exp.is_internship && (
                        <span className="ml-2 px-2 py-0.5 bg-purple-500/20 text-purple-600 text-xs rounded-full border border-purple-200">
                          Internship
                        </span>
                      )}
                    </div>
                  </div>
                  {exp.description && (
                    <p className="mt-2 text-xs text-slate-600 leading-relaxed">{exp.description}</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground italic">No work experience data extracted from resume.</p>
          )}
        </section>

        {/* Certifications */}
        <section className="pt-2">
          <h3 className="text-lg font-semibold text-foreground mb-4 tracking-tight">Certifications</h3>
          {candidate.certifications && candidate.certifications.length > 0 ? (
            <div className="space-y-2">
              {candidate.certifications.map((cert, idx) => (
                <div key={idx} className="flex items-center justify-between bg-slate-50 rounded-xl px-4 py-3 border border-border/60">
                  <div className="flex items-center gap-2">
                    <Award className="w-4 h-4 text-yellow-500 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-foreground">{cert.name}</p>
                      {cert.issuer && <p className="text-xs text-slate-600">{cert.issuer}</p>}
                    </div>
                  </div>
                  {cert.year && (
                    <span className="text-xs text-muted-foreground shrink-0 ml-4">{cert.year}</span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground italic">No certifications found.</p>
          )}
        </section>

        {/* Resume Preview */}
        {resumeUrl && (
          <section className="pt-6 border-t border-border/60">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-foreground tracking-tight">Resume Preview</h3>
              <button
                onClick={() => setShowPdfViewer(true)}
                className="flex items-center gap-2 text-sm text-white bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 px-3 py-1.5 rounded-lg font-semibold shadow-md transition-all"
              >
                <Eye size={16} /> View Full Screen
              </button>
            </div>
            <div className="rounded-xl overflow-hidden border-2 border-border/60 bg-white shadow-lg" style={{ height: '600px' }}>
              <iframe
                src={`${resumeUrl}#view=FitH&toolbar=0&navpanes=0&scrollbar=1`}
                title="Resume Preview"
                className="w-full h-full"
                style={{ border: 'none', transform: 'scale(1)', transformOrigin: 'top left' }}
              />
            </div>
          </section>
        )}
      </div>

      {showScheduler && (
        <InterviewScheduler candidate={candidate} onClose={() => setShowScheduler(false)} />
      )}

      {showPdfViewer && resumeUrl && (
        <ResumeViewer url={resumeUrl} onClose={() => setShowPdfViewer(false)} />
      )}

      {assessmentType && (
        <TechnicalAssessment
          type={assessmentType}
          candidateName={(candidate.full_name || candidate.name || 'Unknown')}
          candidateSkills={candidate.skills}
          onClose={() => setAssessmentType(null)}
          onComplete={handleAssessmentComplete}
        />
      )}
    </div>
  );
};

export default CandidateDetailPanel;

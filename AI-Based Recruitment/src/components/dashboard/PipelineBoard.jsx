import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Linkedin, AlertTriangle, ShieldCheck, Mail, MapPin } from 'lucide-react';
import { useCandidates } from '../../hooks/useCandidates';
import { updateCandidateStage } from '../../services/api';

const PipelineBoard = ({ onSelectCandidate, selectedId }) => {
  const { data: fetchedCandidates, isLoading } = useCandidates();
  const [candidates, setCandidates] = useState([]);
  const [draggedId, setDraggedId] = useState(null);

  useEffect(() => {
    if (fetchedCandidates) {
      // Map valid backend candidates to the board. If no status, default to 'in-progress'
      const mapped = fetchedCandidates.map(c => ({
        ...c,
        stage: c.status || 'in-progress',
        score: c.atsScore || 0,
        risk: c.fraudRisk || 'LOW',
        full_name: c.name || c.full_name || 'Unknown'
      }));
      setCandidates(mapped);
    }
  }, [fetchedCandidates]);

  const columns = [
    { id: 'in-progress', title: 'In Progress', color: 'border-blue-500', headerBg: 'bg-blue-50', iconColor: 'text-blue-600' },
    { id: 'interview', title: 'Interview', color: 'border-purple-500', headerBg: 'bg-purple-50', iconColor: 'text-purple-600' },
    { id: 'hired', title: 'Hired', color: 'border-emerald-500', headerBg: 'bg-emerald-50', iconColor: 'text-emerald-600' },
    { id: 'rejected', title: 'Rejected', color: 'border-red-500', headerBg: 'bg-red-50', iconColor: 'text-red-600' },
  ];

  const handleDragStart = (e, id) => {
    setDraggedId(id);
    e.dataTransfer.setData('text/plain', id);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e, stageId) => {
    e.preventDefault();
    const id = e.dataTransfer.getData('text/plain');
    if (id && stageId) {
      // Optimistic update
      setCandidates(prev => 
        prev.map(c => c.id === id ? { ...c, stage: stageId } : c)
      );
      
      try {
        // Update backend to persist the change
        await updateCandidateStage(id, stageId);
      } catch (error) {
        console.error("Failed to update candidate stage:", error);
        // Revert on failure
        if (fetchedCandidates) {
          const original = fetchedCandidates.find(c => c.id === id);
          if (original) {
            setCandidates(prev => 
              prev.map(c => c.id === id ? { ...c, stage: original.status || 'in-progress' } : c)
            );
          }
        }
      }
    }
    setDraggedId(null);
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-success bg-success/10 border-success/20';
    if (score >= 60) return 'text-warning bg-warning/10 border-warning/20';
    return 'text-destructive bg-destructive/10 border-destructive/20';
  };

  const getRiskIcon = (risk) => {
    if (risk === 'LOW') return <ShieldCheck className="w-3.5 h-3.5 text-success inline mr-1" />;
    if (risk === 'HIGH') return <AlertTriangle className="w-3.5 h-3.5 text-destructive inline mr-1" />;
    return <AlertTriangle className="w-3.5 h-3.5 text-warning inline mr-1" />;
  };

  if (isLoading) {
    return (
      <div className="flex-1 w-full h-full flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 w-full h-full overflow-hidden flex gap-6 px-1 pb-4">
      {columns.map(col => {
        const stageCandidates = candidates.filter(c => c.stage === col.id);
        
        return (
          <div 
            key={col.id} 
            className={`flex flex-col flex-1 min-w-[280px] bg-slate-50/50 rounded-2xl border ${col.color.replace('border-', 'border-t-4 border-slate-200')} shadow-sm overflow-hidden`}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, col.id)}
          >
            {/* Column Header */}
            <div className={`p-4 ${col.headerBg} border-b border-border/50 flex justify-between items-center bg-opacity-70 backdrop-blur-sm`}>
              <h3 className={`font-semibold ${col.iconColor}`}>{col.title}</h3>
              <span className="bg-white px-2.5 py-0.5 rounded-full text-xs font-bold text-slate-700 shadow-sm">
                {stageCandidates.length}
              </span>
            </div>

            {/* Candidates List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
              <AnimatePresence>
                {stageCandidates.map(candidate => (
                  <motion.div
                    key={candidate.id}
                    layoutId={candidate.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    whileHover={{ y: -2, scale: 1.01 }}
                    draggable
                    onDragStart={(e) => handleDragStart(e, candidate.id)}
                    onClick={() => onSelectCandidate && onSelectCandidate(candidate)}
                    className={`bg-white p-4 rounded-xl shadow-sm border ${selectedId === candidate.id ? 'border-primary ring-2 ring-primary/20' : 'border-border/60'} cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow relative group ${draggedId === candidate.id ? 'opacity-50' : 'opacity-100'}`}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center space-x-3 isolate">
                        <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold shadow-sm">
                          {candidate.full_name?.charAt(0) || '?'}
                        </div>
                        <div>
                          <h4 className="font-semibold text-sm text-foreground truncate max-w-[120px]">{candidate.full_name || 'Unknown'}</h4>
                          <p className="text-xs text-muted-foreground truncate max-w-[120px]">{candidate.role || 'Candidate'}</p>
                        </div>
                      </div>
                      <a href="#" className="text-slate-300 hover:text-primary transition-colors">
                        <Linkedin className="w-5 h-5" />
                      </a>
                    </div>
                    
                    <div className="flex items-center text-xs text-slate-500 mb-3 ml-1">
                      <Mail className="w-3 h-3 mr-1.5 flex-shrink-0" />
                      <span className="truncate max-w-[170px]">{candidate.email || 'No email'}</span>
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                      <div className={`px-2 py-1 rounded-md border text-xs font-bold flex items-center ${getScoreColor(candidate.score)}`}>
                        Score: {candidate.score}
                      </div>
                      <div className="flex items-center text-xs font-medium text-slate-600 bg-slate-100 px-2 py-1 rounded-md">
                        {getRiskIcon(candidate.risk)}
                        {candidate.risk} Risk
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {stageCandidates.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-400">
                  <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mb-2">
                    <span className="text-xl font-medium">0</span>
                  </div>
                  <p className="text-sm font-medium">No candidates</p>
                  <p className="text-xs mt-1">Drag and drop here</p>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default PipelineBoard;

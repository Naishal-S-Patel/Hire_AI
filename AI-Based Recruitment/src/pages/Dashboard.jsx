import { useState } from 'react';
import PipelineBoard from '../components/dashboard/PipelineBoard';
import ResumeUploader from '../components/dashboard/ResumeUploader';
import { CandidateDetailPanel } from '../components/dashboard/CandidateDetailPanel';
import { Upload, Filter, Sparkles, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQueryClient } from '@tanstack/react-query';

const Dashboard = () => {
  const [showUploader, setShowUploader] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const queryClient = useQueryClient();

  const handleUploadSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['candidates'] });
  };

  const handleRejectCandidate = () => {
    setSelectedCandidate(null);
    queryClient.invalidateQueries({ queryKey: ['candidates'] });
  };

  return (
    <div className="font-sans h-full flex flex-col pt-2 bg-background relative overflow-hidden">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 px-1">
        <div>
          <h1 className="text-3xl font-bold text-foreground tracking-tight">Recruitment Pipeline</h1>
          <p className="text-muted-foreground text-sm mt-1.5 font-medium">
            Manage your candidates across different stages. Drag and drop to update.
          </p>
        </div>
        <div className="flex gap-3">
          <button 
            className="flex items-center px-4 py-2 bg-white border border-border shadow-sm text-foreground hover:bg-slate-50 hover:border-border/80 rounded-xl text-sm font-medium transition-all"
          >
            <Filter className="w-4 h-4 mr-2 text-muted-foreground" />
            Filter
          </button>
          <button 
            className="flex items-center px-4 py-2 bg-secondary text-white shadow-sm shadow-secondary/20 hover:bg-secondary/90 rounded-xl text-sm font-medium transition-all"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Auto-Match
          </button>
          <button 
            onClick={() => setShowUploader(true)}
            className="flex items-center px-4 py-2 bg-primary text-white shadow-md shadow-primary/20 hover:bg-primary/90 rounded-xl text-sm font-semibold transition-all"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Resume
          </button>
        </div>
      </div>

      {showUploader && (
        <ResumeUploader 
          onUploadSuccess={handleUploadSuccess}
          onClose={() => setShowUploader(false)}
        />
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex gap-6 overflow-hidden relative">
        {/* The Kanban Pipeline Board */}
        <div className={`transition-all duration-300 ease-in-out h-full ${selectedCandidate ? 'w-2/5 shrink-0' : 'w-full'}`}>
          <PipelineBoard 
            onSelectCandidate={setSelectedCandidate} 
            selectedId={selectedCandidate?.id}
          />
        </div>

        {/* Candidate Detail Panel Overlay */}
        <AnimatePresence>
          {selectedCandidate && (
            <motion.div 
              initial={{ x: '100%', opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: '100%', opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="w-3/5 bg-white shadow-2xl border-l border-border/60 flex flex-col rounded-l-2xl overflow-hidden"
            >
              <div className="flex justify-between items-center p-4 border-b border-border/50 bg-slate-50/50">
                <h3 className="font-semibold text-foreground">Candidate Profile</h3>
                <button 
                  onClick={() => setSelectedCandidate(null)}
                  className="p-2 hover:bg-slate-200 rounded-full text-muted-foreground transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="flex-1 overflow-hidden">
                 <CandidateDetailPanel 
                    candidate={selectedCandidate} 
                    onReject={handleRejectCandidate}
                 />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
    </div>
  );
};

export default Dashboard;

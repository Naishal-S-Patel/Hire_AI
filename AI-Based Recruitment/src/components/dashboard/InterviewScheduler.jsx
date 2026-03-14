import { X, Calendar as CalendarIcon, Clock } from 'lucide-react';
import { useState } from 'react';

export const InterviewScheduler = ({ candidate, onClose }) => {
  const [scheduled, setScheduled] = useState(false);

  if (!candidate) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-slate-50 rounded-2xl shadow-2xl border border-border/60 w-full max-w-md overflow-hidden">
        
        <div className="px-6 py-4 border-b border-border/60 flex justify-between items-center bg-white">
          <h2 className="text-lg font-bold text-foreground tracking-tight">Schedule Interview</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-full text-slate-600 hover:text-foreground transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {scheduled ? (
           <div className="p-8 text-center space-y-4">
             <div className="w-16 h-16 bg-green-500/20 text-success rounded-full flex items-center justify-center mx-auto">
               <CalendarIcon className="w-8 h-8" />
             </div>
             <h3 className="text-xl font-bold text-foreground">Invite Sent!</h3>
             <p className="text-sm text-slate-600">Google Calendar invite has been sent to candidate {(candidate.full_name || candidate.name || 'Unknown')}.</p>
             <button onClick={onClose} className="mt-4 px-6 py-2 bg-primary hover:bg-primary/90 text-foreground rounded-lg text-sm font-medium w-full transition-colors">
               Done
             </button>
           </div>
        ) : (
          <div className="p-6">
            <div className="mb-6 flex items-center bg-primary/10 p-3 rounded-lg border border-primary/20">
              <div className="w-10 h-10 bg-primary text-foreground rounded-full flex items-center justify-center font-bold mr-3 shadow-sm">
                {(candidate.full_name || candidate.name || 'Unknown').charAt(0)}
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">{(candidate.full_name || candidate.name || 'Unknown')}</p>
                <p className="text-xs text-slate-600">{candidate.role}</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Date</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <CalendarIcon className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <input type="date" className="block w-full pl-10 pr-3 py-2 bg-white border border-border rounded-lg text-sm text-foreground focus:ring-blue-500 focus:border-blue-500" />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Time (Local)</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <input type="time" defaultValue="10:00" className="block w-full pl-10 pr-3 py-2 bg-white border border-border rounded-lg text-sm text-foreground focus:ring-blue-500 focus:border-blue-500" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Interview Type</label>
                <select className="block w-full px-3 py-2 bg-white border border-border rounded-lg text-sm text-foreground focus:ring-blue-500 focus:border-blue-500">
                  <option>Technical Round (1hr)</option>
                  <option>HR Screening (30m)</option>
                  <option>System Design (1.5hr)</option>
                </select>
              </div>
            </div>

            <div className="mt-8 flex gap-3">
              <button onClick={onClose} className="flex-1 px-4 py-2 border border-border text-slate-700 rounded-lg text-sm font-medium hover:bg-white transition-colors">
                Cancel
              </button>
              <button onClick={() => setScheduled(true)} className="flex-1 px-4 py-2 bg-primary text-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors">
                Confirm & Send
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InterviewScheduler;

import { Sparkles, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

export const AISummaryBox = ({ summary, isLoading, className }) => {
  return (
    <div className={cn("bg-gradient-to-br from-blue-500/10 to-indigo-500/10 border border-blue-500/20 rounded-xl p-4 shadow-sm relative overflow-hidden", className)}>
      <div className="absolute top-0 right-0 w-32 h-32 bg-blue-400/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none"></div>
      
      <div className="flex items-center mb-3">
        <div className="bg-blue-500/20 text-blue-400 p-1.5 rounded-md mr-2 shadow-sm border border-blue-500/30">
          <Sparkles className="w-4 h-4" />
        </div>
        <h3 className="text-sm font-semibold text-white tracking-tight">AI Executive Summary</h3>
      </div>
      
      {isLoading ? (
        <div className="flex items-center text-sm text-gray-400 py-2">
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          Generating AI insights...
        </div>
      ) : summary ? (
        <p className="text-sm text-gray-300 leading-relaxed font-medium">{summary}</p>
      ) : (
        <p className="text-sm text-gray-500 italic">Summary not yet generated for this candidate.</p>
      )}
    </div>
  );
};

export default AISummaryBox;

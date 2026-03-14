import { useState } from 'react';
import { Video, Mic, CheckCircle2, PlaySquare } from 'lucide-react';

export const VideoAssessment = () => {
  const [status, setStatus] = useState('idle'); // idle -> recording -> analyzing -> complete

  const handleStart = () => {
    setStatus('recording');
    setTimeout(() => {
      setStatus('analyzing');
      setTimeout(() => setStatus('complete'), 2000);
    }, 4000);
  };

  return (
    <div className="bg-slate-50 border-2 border-dashed border-border/60 rounded-xl p-8 text-center mt-4">
      {status === 'idle' && (
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 bg-purple-500/20 text-purple-600 rounded-full flex items-center justify-center mb-4">
            <Video className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-foreground mb-2">Technical Video Assessment</h3>
          <p className="text-sm text-slate-600 mb-6 max-w-sm">
            Record a short 2-minute video answering: "Describe a challenging technical problem you solved recently."
          </p>
          <button 
            onClick={handleStart}
            className="flex items-center px-6 py-2.5 bg-purple-600 font-medium text-foreground text-sm rounded-lg hover:bg-purple-700 transition-colors"
          >
            <PlaySquare className="w-4 h-4 mr-2" /> Start Recording
          </button>
        </div>
      )}

      {status === 'recording' && (
        <div className="flex flex-col items-center">
          <div className="relative w-16 h-16 flex items-center justify-center mb-4">
            <div className="absolute inset-0 bg-red-500/20 rounded-full animate-ping opacity-75"></div>
            <div className="relative w-16 h-16 bg-red-500/20 text-destructive rounded-full flex items-center justify-center">
              <Mic className="w-8 h-8 animate-pulse" />
            </div>
          </div>
          <h3 className="text-lg font-bold text-foreground mb-2">Recording in progress...</h3>
          <p className="text-sm font-medium text-destructive">00:02 / 02:00</p>
        </div>
      )}

      {status === 'analyzing' && (
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 bg-blue-500/20 text-primary rounded-full flex items-center justify-center mb-4">
             <div className="h-8 w-8 border-4 border-blue-400/30 border-t-blue-400 rounded-full animate-spin"></div>
          </div>
          <h3 className="text-lg font-bold text-foreground mb-2">AI Analyzing Response...</h3>
          <p className="text-sm text-slate-600">Processing transcript and behavior metrics.</p>
        </div>
      )}

      {status === 'complete' && (
        <div className="flex items-start bg-white p-6 rounded-lg border border-border/60 text-left">
          <div className="mr-6 flex-shrink-0">
             <div className="w-32 h-24 bg-slate-100 rounded text-muted-foreground flex items-center justify-center relative overflow-hidden">
                <Video className="w-8 h-8 z-10" />
                <div className="absolute inset-0 bg-gray-900/20"></div>
             </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-foreground">AI Assessment Results</h3>
              <CheckCircle2 className="w-5 h-5 text-success" />
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-4 mt-4">
              <div className="bg-white p-3 rounded border border-border/60 shadow-sm">
                <div className="text-xs text-muted-foreground font-medium mb-1 uppercase tracking-wider">Communication</div>
                <div className="text-lg font-bold text-primary">9.2 / 10</div>
              </div>
              <div className="bg-white p-3 rounded border border-border/60 shadow-sm">
                <div className="text-xs text-muted-foreground font-medium mb-1 uppercase tracking-wider">Technical Relevance</div>
                <div className="text-lg font-bold text-purple-600">8.8 / 10</div>
              </div>
            </div>

            <div>
              <div className="text-xs font-semibold text-slate-600 mb-1">Generated Transcript Extract:</div>
              <p className="text-sm text-slate-600 italic border-l-2 border-border pl-3">
                "...we had a significant memory leak in the production Node service. I utilized Chrome DevTools to take heap snapshots and identified that the websocket connections weren't being properly garbage collected..."
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoAssessment;

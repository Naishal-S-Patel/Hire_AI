import { useState } from 'react';
import { Sparkles, Search, Loader2 } from 'lucide-react';
import { useSearchCandidates } from '../../hooks/useCandidates';

export const QueryAssistant = ({ onResults }) => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  
  const { refetch } = useSearchCandidates(query);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsSearching(true);
    
    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      const { data } = await refetch();
      if (onResults && data) {
        onResults(data);
      }
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="bg-white border border-border/60 rounded-xl shadow-sm p-1.5 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all">
      <form onSubmit={handleSearch} className="flex items-center">
        <div className="pl-3 pr-2 text-blue-500">
          <Sparkles className="w-5 h-5" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Find React developers in Gujarat with 3 years experience..."
          className="flex-1 py-2.5 px-2 bg-transparent border-none focus:outline-none text-foreground placeholder-gray-500"
        />
        <button
          type="submit"
          disabled={isSearching || !query.trim()}
          className="px-4 py-2 bg-primary text-foreground rounded-lg font-medium text-sm hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center"
        >
          {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
        </button>
      </form>
      
      {isSearching && (
        <div className="px-12 py-3 border-t border-border/60 flex items-center gap-2">
          <span className="text-xs text-slate-600 flex items-center font-medium">
            <Sparkles className="w-3 h-3 mr-1.5 text-primary" />
            AI is analyzing your query...
          </span>
        </div>
      )}
    </div>
  );
};

export default QueryAssistant;

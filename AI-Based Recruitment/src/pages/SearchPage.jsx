import { useState } from 'react';
import { searchCandidates } from '../services/api';
import { Search, Sparkles } from 'lucide-react';
import CandidateCard from '../components/dashboard/CandidateCard';

const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      setLoading(true);
      setSearched(true);
      const data = await searchCandidates(query);
      setResults(data);
    } catch (error) {
      console.error('Error searching candidates:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Sparkles className="text-blue-500" size={28} />
          AI-Powered Search
        </h1>
        <p className="text-gray-400 mt-1">Search candidates using natural language</p>
      </div>

      <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder='Try: "React developer with 3+ years experience in Mumbai"'
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-4 bg-[#0a0f1e] border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Searching...
              </>
            ) : (
              <>
                <Search size={20} />
                Search Candidates
              </>
            )}
          </button>
        </form>

        <div className="mt-6 flex flex-wrap gap-2">
          <span className="text-sm text-gray-400">Try:</span>
          {[
            'Python developer Gujarat',
            'Senior React engineer 5 years',
            'ML engineer with NLP experience',
            'Full stack developer startup experience'
          ].map((example) => (
            <button
              key={example}
              onClick={() => setQuery(example)}
              className="px-3 py-1 bg-[#0a0f1e] border border-gray-600 hover:border-blue-500 text-gray-300 text-sm rounded-full transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}

      {!loading && searched && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">
              {results.length} {results.length === 1 ? 'Result' : 'Results'} Found
            </h2>
          </div>

          {results.length === 0 ? (
            <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-12 text-center">
              <Search className="mx-auto text-gray-500 mb-4" size={48} />
              <p className="text-gray-400 text-lg">No candidates found matching your search</p>
              <p className="text-gray-500 text-sm mt-2">Try adjusting your search terms</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {results.map((candidate) => (
                <CandidateCard key={candidate.id} candidate={candidate} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchPage;

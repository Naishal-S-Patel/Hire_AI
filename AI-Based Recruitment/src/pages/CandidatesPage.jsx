import { useState, useEffect } from 'react';
import { getCandidates } from '../services/api';
import api from '../services/api';
import CandidateList from '../components/dashboard/CandidateList';
import ResumeUploader from '../components/dashboard/ResumeUploader';
import { Upload, Search, Filter, Trash2 } from 'lucide-react';

const CandidatesPage = () => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showUploader, setShowUploader] = useState(false);
  const [purging, setPurging] = useState(false);

  useEffect(() => {
    loadCandidates();
  }, []);

  const loadCandidates = async () => {
    try {
      setLoading(true);
      const data = await getCandidates();
      setCandidates(data);
    } catch (error) {
      console.error('Error loading candidates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePurgeDuplicates = async () => {
    if (!window.confirm('This will permanently delete duplicate candidate records. Continue?')) return;
    try {
      setPurging(true);
      const res = await api.post('/candidates/purge-duplicates');
      alert(`Removed ${res.deleted} duplicate(s).`);
      loadCandidates();
    } catch (e) {
      alert('Failed to purge duplicates.');
    } finally {
      setPurging(false);
    }
  };

  const handleUploadSuccess = () => {
    loadCandidates();
    setShowUploader(false);
  };

  const filteredCandidates = candidates.filter(candidate =>
    candidate.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    candidate.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    candidate.skills.some(skill => skill.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Candidates</h1>
          <p className="text-gray-400 mt-1">Manage and review all candidates</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handlePurgeDuplicates}
            disabled={purging}
            className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-red-400 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <Trash2 size={16} />
            {purging ? 'Removing...' : 'Remove Duplicates'}
          </button>
          <button 
            onClick={() => setShowUploader(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors"
          >
            <Upload size={18} />
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

      <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search candidates by name, email, or skills..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-[#0a0f1e] border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button className="px-4 py-2 bg-[#0a0f1e] border border-gray-600 hover:bg-[#141b2b] text-gray-300 rounded-lg flex items-center gap-2 transition-colors">
            <Filter size={18} />
            Filters
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
        <CandidateList candidates={filteredCandidates} onRefresh={loadCandidates} />
      )}
    </div>
  );
};

export default CandidatesPage;

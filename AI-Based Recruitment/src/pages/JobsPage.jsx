import { useState, useEffect } from 'react';
import { Briefcase, Plus, MapPin, DollarSign, Clock, X, Trash2, Users, Loader2, CheckCircle } from 'lucide-react';
import axios from 'axios';

const API = 'http://localhost:8000/api/v1';

const getToken = () => localStorage.getItem('access_token');
const headers = () => ({ Authorization: `Bearer ${getToken()}` });

const JobsPage = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [toast, setToast] = useState(null);
  const [form, setForm] = useState({
    title: '', description: '', location: '', company: 'TalentHire AI',
    required_skills: '', experience_required: '', salary: '', type: 'Full-time'
  });

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/jobs`, { headers: headers() });
      setJobs(res.data || []);
    } catch (e) {
      console.error('Failed to load jobs:', e);
      // Fallback to empty
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchJobs(); }, []);

  const handleCreate = async () => {
    if (!form.title || !form.description) {
      setToast({ type: 'error', msg: 'Title and description are required' });
      return;
    }
    setCreating(true);
    try {
      await axios.post(`${API}/jobs`, {
        title: form.title,
        description: form.description,
        location: form.location || null,
        company: form.company || null,
        required_skills: form.required_skills ? form.required_skills.split(',').map(s => s.trim()).filter(Boolean) : [],
        experience_required: form.experience_required ? parseFloat(form.experience_required) : null,
      }, { headers: headers() });
      setToast({ type: 'success', msg: 'Job created successfully!' });
      setShowCreate(false);
      setForm({ title: '', description: '', location: '', company: 'TalentHire AI', required_skills: '', experience_required: '', salary: '', type: 'Full-time' });
      fetchJobs();
    } catch (e) {
      const detail = e.response?.data?.detail || 'Failed to create job';
      setToast({ type: 'error', msg: typeof detail === 'string' ? detail : JSON.stringify(detail) });
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (jobId) => {
    if (!confirm('Delete this job posting?')) return;
    try {
      await axios.delete(`${API}/jobs/${jobId}`, { headers: headers() });
      setToast({ type: 'success', msg: 'Job deleted' });
      fetchJobs();
    } catch (e) {
      setToast({ type: 'error', msg: 'Failed to delete job' });
    }
  };

  // Auto-dismiss toast
  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(t);
    }
  }, [toast]);

  return (
    <div className="p-6 space-y-6">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl shadow-lg flex items-center gap-2 text-sm font-medium border ${
          toast.type === 'success' ? 'bg-green-500/20 border-green-500/30 text-green-400' : 'bg-red-500/20 border-red-500/30 text-red-400'
        }`}>
          {toast.type === 'success' ? <CheckCircle className="w-4 h-4" /> : '⚠️'}
          {toast.msg}
          <button onClick={() => setToast(null)} className="ml-2 text-gray-500 hover:text-white">×</button>
        </div>
      )}

      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Job Openings</h1>
          <p className="text-gray-400 mt-1">Manage your job postings and applications</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors"
        >
          <Plus size={18} />
          Create Job
        </button>
      </div>

      {/* Job Cards */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
        </div>
      ) : jobs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {jobs.map((job) => (
            <div key={job.id} className="bg-[#1a2332] rounded-xl border border-gray-700 p-6 hover:border-blue-500 transition-colors group">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-blue-600/20 rounded-lg flex items-center justify-center">
                  <Briefcase className="text-blue-500" size={24} />
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs font-medium rounded-full">
                    {job.is_active ? 'Active' : 'Closed'}
                  </span>
                  <button onClick={() => handleDelete(job.id)} className="p-1 text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all">
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              <h3 className="text-lg font-semibold text-white mb-2">{job.title}</h3>
              <p className="text-gray-400 text-sm mb-4 line-clamp-2">{job.description}</p>

              <div className="space-y-2 mb-4">
                {job.location && (
                  <div className="flex items-center gap-2 text-gray-400 text-sm">
                    <MapPin size={16} /> {job.location}
                  </div>
                )}
                {job.company && (
                  <div className="flex items-center gap-2 text-gray-400 text-sm">
                    <Briefcase size={16} /> {job.company}
                  </div>
                )}
                {job.experience_required && (
                  <div className="flex items-center gap-2 text-gray-400 text-sm">
                    <Clock size={16} /> {job.experience_required}+ years
                  </div>
                )}
              </div>

              {job.required_skills?.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-4">
                  {job.required_skills.slice(0, 4).map(s => (
                    <span key={s} className="px-2 py-0.5 bg-blue-500/10 text-blue-300 text-xs rounded border border-blue-500/20">{s}</span>
                  ))}
                  {job.required_skills.length > 4 && (
                    <span className="text-xs text-gray-500">+{job.required_skills.length - 4} more</span>
                  )}
                </div>
              )}

              <div className="pt-4 border-t border-gray-700 flex items-center justify-between">
                <span className="text-gray-500 text-xs">
                  {new Date(job.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-12 text-center">
          <Briefcase className="mx-auto text-gray-500 mb-4" size={48} />
          <p className="text-gray-400 text-lg">No job openings yet</p>
          <p className="text-gray-500 text-sm mt-2">Create your first job posting to get started</p>
          <button
            onClick={() => setShowCreate(true)}
            className="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 mx-auto transition-colors"
          >
            <Plus size={18} /> Create Job
          </button>
        </div>
      )}

      {/* Create Job Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0f1623] border border-gray-700 rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-700 bg-[#1a2332] flex justify-between items-center">
              <h2 className="text-lg font-bold text-white">Create New Job</h2>
              <button onClick={() => setShowCreate(false)} className="p-2 hover:bg-gray-700 rounded-full text-gray-400">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Job Title *</label>
                <input value={form.title} onChange={e => setForm({...form, title: e.target.value})}
                  placeholder="e.g. Senior React Developer"
                  className="w-full bg-[#1a2332] border border-gray-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Description *</label>
                <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})}
                  placeholder="Describe the role, responsibilities, and requirements..."
                  rows={4}
                  className="w-full bg-[#1a2332] border border-gray-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 resize-none" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Location</label>
                  <input value={form.location} onChange={e => setForm({...form, location: e.target.value})}
                    placeholder="e.g. Mumbai, India"
                    className="w-full bg-[#1a2332] border border-gray-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Company</label>
                  <input value={form.company} onChange={e => setForm({...form, company: e.target.value})}
                    placeholder="TalentHire AI"
                    className="w-full bg-[#1a2332] border border-gray-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Required Skills (comma-separated)</label>
                <input value={form.required_skills} onChange={e => setForm({...form, required_skills: e.target.value})}
                  placeholder="e.g. React, TypeScript, Node.js"
                  className="w-full bg-[#1a2332] border border-gray-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Experience Required (years)</label>
                  <input type="number" value={form.experience_required} onChange={e => setForm({...form, experience_required: e.target.value})}
                    placeholder="e.g. 3"
                    className="w-full bg-[#1a2332] border border-gray-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Job Type</label>
                  <select value={form.type} onChange={e => setForm({...form, type: e.target.value})}
                    className="w-full bg-[#1a2332] border border-gray-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500">
                    <option value="Full-time">Full-time</option>
                    <option value="Part-time">Part-time</option>
                    <option value="Contract">Contract</option>
                    <option value="Internship">Internship</option>
                    <option value="Remote">Remote</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-700 bg-[#1a2332] flex justify-end gap-3">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm font-medium transition-colors">
                Cancel
              </button>
              <button onClick={handleCreate} disabled={creating}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 disabled:opacity-50">
                {creating ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</> : <><Plus className="w-4 h-4" /> Create Job</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobsPage;

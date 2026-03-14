import { useState, useEffect } from 'react';
import { Users, UserPlus, CheckCircle, TrendingUp, Award, Target, RefreshCw } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, PieChart, Pie, Cell, LineChart, Line, Legend } from 'recharts';
import api from '../services/api';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'];

export const AnalyticsDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generatingSummaries, setGeneratingSummaries] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await api.get('/candidates/analytics');
      setAnalytics(response);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSummaries = async () => {
    try {
      setGeneratingSummaries(true);
      const result = await api.post('/candidates/generate-all-summaries');
      alert(`Done! Generated ${result.generated} summaries, ${result.failed} failed.`);
      fetchAnalytics(); // refresh stats
    } catch (error) {
      console.error('Error generating summaries:', error);
      alert('Failed to generate summaries. Make sure ML service is running.');
    } finally {
      setGeneratingSummaries(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-[#0a0f1e]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="flex items-center justify-center h-full bg-[#0a0f1e]">
        <div className="text-center">
          <p className="text-gray-400 text-lg mb-4">Failed to load analytics</p>
          <button 
            onClick={fetchAnalytics}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const hiringFunnel = [
    { name: 'Applied', value: analytics.hiring_funnel.applied, fill: '#3b82f6' },
    { name: 'Screening', value: analytics.hiring_funnel.screening, fill: '#8b5cf6' },
    { name: 'Interviewing', value: analytics.hiring_funnel.interviewing, fill: '#10b981' },
    { name: 'Offers', value: analytics.hiring_funnel.offers, fill: '#f59e0b' },
    { name: 'Hired', value: analytics.hiring_funnel.hired, fill: '#22c55e' },
  ];

  const sourceData = Object.entries(analytics.source_percentages || {})
    .map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value: value
    }))
    .filter(s => s.value > 0);

  return (
    <div className="p-6 bg-[#0a0f1e] min-h-screen space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Recruitment Analytics</h1>
          <p className="text-gray-400 mt-1">Real-time insights into your hiring pipeline</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleGenerateSummaries}
            disabled={generatingSummaries}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${generatingSummaries ? 'animate-spin' : ''}`} />
            {generatingSummaries ? 'Generating...' : 'Generate Missing Summaries'}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-6 hover:border-blue-500 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-blue-500" />
            </div>
            <span className="text-blue-500 text-sm font-medium">Total</span>
          </div>
          <h3 className="text-3xl font-bold text-white mb-1">{analytics.total_candidates}</h3>
          <p className="text-gray-400 text-sm">Candidates</p>
        </div>

        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-6 hover:border-purple-500 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-purple-500" />
            </div>
            <span className="text-purple-500 text-sm font-medium">30 Days</span>
          </div>
          <h3 className="text-3xl font-bold text-white mb-1">{analytics.recent_candidates_30d}</h3>
          <p className="text-gray-400 text-sm">New Candidates</p>
        </div>

        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-6 hover:border-green-500 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
              <Target className="w-6 h-6 text-green-500" />
            </div>
            <span className="text-green-500 text-sm font-medium">Average</span>
          </div>
          <h3 className="text-3xl font-bold text-white mb-1">{analytics.avg_ats_score.toFixed(1)}</h3>
          <p className="text-gray-400 text-sm">ATS Score / 100</p>
        </div>

        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-6 hover:border-orange-500 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-orange-500/20 rounded-lg flex items-center justify-center">
              <Award className="w-6 h-6 text-orange-500" />
            </div>
            <span className="text-orange-500 text-sm font-medium">AI Ready</span>
          </div>
          <h3 className="text-3xl font-bold text-white mb-1">{analytics.summary_completion_rate.toFixed(1)}%</h3>
          <p className="text-gray-400 text-sm">With AI Summary</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hiring Funnel */}
        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-6">
          <h3 className="text-xl font-bold text-white mb-6">Hiring Funnel</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={hiringFunnel} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis type="number" stroke="#9ca3af" />
              <YAxis dataKey="name" type="category" stroke="#9ca3af" width={100} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1a2332', 
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Bar dataKey="value" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Source Distribution */}
        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-6">
          <h3 className="text-xl font-bold text-white mb-6">Talent Pool by Source</h3>
          {sourceData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={sourceData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {sourceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1a2332', 
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No source data available
            </div>
          )}
        </div>
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-6">
          <h4 className="text-lg font-semibold text-white mb-4">Quick Stats</h4>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Candidates with Summaries</span>
              <span className="text-white font-semibold">{analytics.candidates_with_summaries}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Missing Summaries</span>
              <span className="text-white font-semibold">
                {analytics.total_candidates - analytics.candidates_with_summaries}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Completion Rate</span>
              <span className="text-green-500 font-semibold">{analytics.summary_completion_rate.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-6">
          <h4 className="text-lg font-semibold text-white mb-4">Source Breakdown</h4>
          <div className="space-y-3">
            {Object.entries(analytics.sources || {}).map(([source, count]) => (
              <div key={source} className="flex justify-between items-center">
                <span className="text-gray-400 capitalize">{source}</span>
                <span className="text-white font-semibold">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-[#1a2332] rounded-xl border border-gray-700 p-6">
          <h4 className="text-lg font-semibold text-white mb-4">Pipeline Health</h4>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-400">Screening Rate</span>
                <span className="text-white">60%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '60%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-400">Interview Rate</span>
                <span className="text-white">25%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-purple-500 h-2 rounded-full" style={{ width: '25%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-400">Offer Rate</span>
                <span className="text-white">5%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '5%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;

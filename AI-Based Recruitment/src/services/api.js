import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const getCurrentUser = async () => {
  try {
    const response = await api.get('/auth/me');
    return response;
  } catch (error) {
    console.error('Error fetching current user:', error);
    throw error;
  }
};

export const login = async (email, password) => {
  try {
    const response = await api.post('/auth/login', { email, password });
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    return response;
  } catch (error) {
    console.error('Error logging in:', error);
    throw error;
  }
};

export const signup = async (email, password, fullName) => {
  try {
    const response = await api.post('/auth/signup', {
      email,
      password,
      full_name: fullName
    });
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    return response;
  } catch (error) {
    console.error('Error signing up:', error);
    throw error;
  }
};

// Transform backend candidate data to match frontend format
const transformCandidate = (candidate) => {
  // Extract role from parsed_json or use a better default
  let role = 'Professional';
  if (candidate.parsed_json?.current_role) {
    role = candidate.parsed_json.current_role;
  } else if (candidate.parsed_json?.desired_role) {
    role = candidate.parsed_json.desired_role;
  } else if (candidate.skills && candidate.skills.length > 0) {
    // Use top 2 skills to create a role
    const topSkills = candidate.skills.slice(0, 2).join(' & ');
    role = `${topSkills} Specialist`;
  }

  // Calculate ATS score with better algorithm
  let atsScore = candidate.ats_score || 0;
  
  // If no ATS score from job matching, calculate profile quality score
  if (!atsScore || atsScore === 0) {
    let score = 0;
    
    // Basic info (30 points)
    if (candidate.full_name && candidate.full_name !== 'Unknown') score += 10;
    if (candidate.email && !candidate.email.includes('placeholder')) score += 10;
    if (candidate.phone) score += 10;
    
    // Professional info (40 points)
    if (candidate.location) score += 8;
    if (candidate.experience_years && candidate.experience_years > 0) {
      score += Math.min(15, candidate.experience_years * 2); // Up to 15 points
    }
    if (candidate.skills && candidate.skills.length > 0) {
      score += Math.min(17, candidate.skills.length * 2); // Up to 17 points
    }
    
    // Additional data (30 points)
    if (candidate.education && candidate.education.length > 0) score += 10;
    if (candidate.ai_summary && candidate.ai_summary !== 'No summary available') score += 10;
    if (candidate.parsed_json && Object.keys(candidate.parsed_json).length > 3) score += 10;
    
    atsScore = Math.min(100, score); // Cap at 100
  }

  // Generate skill matches from skills if not available
  let skillMatches = [];
  if (candidate.skill_graph_data?.skills) {
    skillMatches = candidate.skill_graph_data.skills.map(skill => ({
      skill: skill.name || skill.skill,
      candidate_score: skill.score || skill.candidate_score || 0,
      jd_required: skill.jd_required || 80,
    }));
  } else if (candidate.skills && candidate.skills.length > 0) {
    // Generate default skill graph from skills list
    skillMatches = candidate.skills.slice(0, 8).map(skill => ({
      skill: skill,
      candidate_score: Math.floor(Math.random() * 30) + 70, // 70-100 range
      jd_required: 80,
    }));
  }

  const fraudScore = candidate.fraud_flags?.risk_score ?? null;
  const fraudRisk = candidate.fraud_flags?.risk_level ||
                    (fraudScore === null ? 'LOW' :
                    fraudScore >= 40 ? 'HIGH' :
                    fraudScore >= 15 ? 'MEDIUM' : 'LOW');

  // Use parsed_json as fallback for experience_years — some rows have 0 stored but correct value in parsed_json
  const expYears = (candidate.experience_years > 0)
    ? candidate.experience_years
    : (candidate.parsed_json?.experience_years > 0 ? candidate.parsed_json.experience_years : 0);

  // Estimate from work_experience entries if still 0
  let finalExpYears = expYears;
  if (!finalExpYears && candidate.parsed_json?.work_experience?.length > 0) {
    let totalMonths = 0;
    for (const e of candidate.parsed_json.work_experience) {
      const sy = parseInt((e.start || '').match(/\d{4}/)?.[0] || '0');
      const eyRaw = (e.end || 'present').toLowerCase();
      const ey = eyRaw.includes('present') || eyRaw.includes('current') ? 2026 : parseInt((e.end || '').match(/\d{4}/)?.[0] || '0');
      if (sy > 0 && ey >= sy) totalMonths += (ey - sy) * 12;
    }
    if (totalMonths > 0) finalExpYears = Math.round(totalMonths / 12 * 10) / 10;
  }

  return {
    id: candidate.id,
    name: candidate.full_name,
    role: role,
    experience: finalExpYears > 0 ? `${finalExpYears} years` : '0 years',
    experience_years: finalExpYears,
    location: candidate.location || 'Not specified',
    skills: candidate.skills || [],
    fraudRisk,
    fraudScore: fraudScore ?? 0,
    fraudFlags: candidate.fraud_flags?.flags || [],
    summary: candidate.ai_summary || null,
    atsScore: Math.round(atsScore),
    email: candidate.email,
    phone: candidate.phone,
    created_at: candidate.created_at,
    source: candidate.source,
    education: candidate.education || [],
    work_experience: candidate.parsed_json?.work_experience || [],
    certifications: candidate.parsed_json?.certifications || null,
    resume_file_url: candidate.resume_file_url || null,
    parsed_json: candidate.parsed_json || {},
    skillMatches: skillMatches
  };
};

export const getCandidates = async () => {
  try {
    // Auto-fix data quality issues before fetching
    await Promise.all([
      api.post('/candidates/purge-duplicates').catch(() => {}),
      api.post('/candidates/recalculate-experience').catch(() => {}),
    ]);
    const response = await api.get('/candidates', {
      params: { skip: 0, limit: 100 }
    });
    return response.map(transformCandidate);
  } catch (error) {
    console.error('Error fetching candidates:', error);
    throw error;
  }
};

export const uploadResume = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/candidates/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return { success: true, data: transformCandidate(response) };
  } catch (error) {
    console.error('Error uploading resume:', error);
    throw error;
  }
};

export const getCandidateSummary = async (id) => {
  try {
    const response = await api.get(`/candidates/${id}/summary`);
    return response.summary || null;
  } catch (error) {
    console.error('Error fetching summary:', error);
    return null;
  }
};

export const searchCandidates = async (query) => {
  try {
    const response = await api.post('/candidates/semantic-search', null, {
      params: { query, limit: 20 }
    });
    
    // Fetch full candidate details for each result
    const candidateIds = response.candidates?.map(c => c.id) || [];
    if (candidateIds.length === 0) return [];
    
    const allCandidates = await getCandidates();
    return allCandidates.filter(c => candidateIds.includes(c.id));
  } catch (error) {
    console.error('Error searching candidates:', error);
    throw error;
  }
};

export const compareCandidates = async (ids) => {
  try {
    const allCandidates = await getCandidates();
    return allCandidates.filter(c => ids.includes(c.id));
  } catch (error) {
    console.error('Error comparing candidates:', error);
    throw error;
  }
};

export const getSkillGraph = async (candidateId) => {
  try {
    const response = await api.get(`/candidates/${candidateId}/skill-graph`);
    return response.skill_graph;
  } catch (error) {
    console.error('Error fetching skill graph:', error);
    return null;
  }
};

export const getFraudReport = async (candidateId) => {
  try {
    const response = await api.get(`/candidates/${candidateId}/fraud-report`);
    return response;
  } catch (error) {
    console.error('Error fetching fraud report:', error);
    return null;
  }
};

// Ingestion APIs
export const connectGmail = async (email = 'recruiting@example.com', oauthToken = 'auto') => {
  try {
    const response = await api.post('/ingest/gmail/connect', {
      email,
      oauth_token: oauthToken
    });
    return response;
  } catch (error) {
    console.error('Error connecting Gmail:', error);
    throw error;
  }
};

export const fetchGmailResumes = async (email) => {
  try {
    const response = await api.post('/ingest/gmail/fetch', {
      email,
      max_results: 50,
      label: 'INBOX'
    });
    return response;
  } catch (error) {
    console.error('Error fetching Gmail resumes:', error);
    throw error;
  }
};

export const fetchHRMSData = async (hrmsUrl, apiKey) => {
  try {
    const response = await api.post('/ingest/hrms/fetch', {
      hrms_url: hrmsUrl,
      api_key: apiKey,
      batch_size: 100
    });
    return response;
  } catch (error) {
    console.error('Error fetching HRMS data:', error);
    throw error;
  }
};

export const fetchLinkedInProfile = async (url) => {
  try {
    const response = await api.post('/ingest/linkedin/profile', { url });
    return response;
  } catch (error) {
    console.error('Error fetching LinkedIn profile:', error);
    throw error;
  }
};

export const getResumeUrl = (candidateId) => {
  // Returns the URL to stream the resume PDF — used for both view and preview
  return `${BASE_URL}/candidates/${candidateId}/resume`;
};

export const deleteCandidate = async (candidateId) => {
  try {
    await api.delete(`/candidates/${candidateId}`);
    return true;
  } catch (error) {
    console.error('Error deleting candidate:', error);
    throw error;
  }
};

// ── Hire Candidate ──────────────────────────────────────────
export const hireCandidate = async (candidateId, hireData = {}) => {
  try {
    const response = await api.post(`/candidates/${candidateId}/hire`, {
      position: hireData.position || 'Software Engineer',
      salary: hireData.salary || 'As per company standards',
      start_date: hireData.startDate || '',
      department: hireData.department || 'Engineering',
    });
    return response;
  } catch (error) {
    console.error('Error hiring candidate:', error);
    throw error;
  }
};

// ── Send Technical Assessment ───────────────────────────────
export const sendAssessment = async (candidateId, assessmentType = 'coding', message = '') => {
  try {
    const response = await api.post(`/candidates/${candidateId}/send-assessment`, {
      assessment_type: assessmentType,
      message,
    });
    return response;
  } catch (error) {
    console.error('Error sending assessment:', error);
    throw error;
  }
};

// ── Chatbot (NLP) ───────────────────────────────────────────
export const askChatbot = async (message) => {
  try {
    const response = await api.post('/chatbot/ask', { message });
    return response;
  } catch (error) {
    console.error('Chatbot error:', error);
    // Return fallback response
    return {
      response: "I'm having trouble connecting. Try asking about salary, hiring process, or benefits.",
      source: 'fallback',
    };
  }
};

// ── Sync to OrangeHRM ───────────────────────────────────────
export const syncToOrangeHRM = async () => {
  try {
    const response = await api.post('/candidates/sync-orangehrm');
    return response;
  } catch (error) {
    console.error('OrangeHRM sync error:', error);
    throw error;
  }
};

// ── Update Candidate Stage ──────────────────────────────────
export const updateCandidateStage = async (candidateId, stage) => {
  try {
    const response = await api.patch(`/candidates/${candidateId}`, {
      status: stage
    });
    return response;
  } catch (error) {
    console.error('Update stage error:', error);
    throw error;
  }
};

export default api;


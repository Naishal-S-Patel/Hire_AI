import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './components/layout/DashboardLayout';
import LoginPage from './pages/LoginPage';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import CandidatesPage from './pages/CandidatesPage';
import SearchPage from './pages/SearchPage';
import JobsPage from './pages/JobsPage';
import IngestionPage from './pages/IngestionPage';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import GoogleCallback from './pages/GoogleCallback';
import CandidatePortal from './pages/CandidatePortal';
import ChatbotWidget from './components/ChatbotWidget';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('access_token');
  return token ? children : <Navigate to="/login" replace />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/google/callback" element={<GoogleCallback />} />
        
        {/* Candidate Portal - Public after login */}
        <Route
          path="/candidate-portal"
          element={
            <ProtectedRoute>
              <CandidatePortal />
            </ProtectedRoute>
          }
        />
        
        {/* Protected Recruiter Dashboard */}
        <Route
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/candidates" element={<CandidatesPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/ingestion" element={<IngestionPage />} />
          <Route path="/analytics" element={<AnalyticsDashboard />} />
        </Route>
      </Routes>
      
      {/* Global Chatbot Widget - visible on all pages */}
      <ChatbotWidget />
    </BrowserRouter>
  );
}

export default App;

import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getCurrentUser } from '../services/api';

const GoogleCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const handleCallback = async () => {
      const accessToken = searchParams.get('access_token');
      const refreshToken = searchParams.get('refresh_token');
      const error = searchParams.get('error');

      if (error) {
        console.error('Google OAuth error:', error);
        navigate('/login?error=oauth_failed');
        return;
      }

      if (accessToken && refreshToken) {
        // Store tokens
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
        
        try {
          // Fetch user profile
          const user = await getCurrentUser();
          localStorage.setItem('user', JSON.stringify(user));
          
          // Redirect to dashboard
          navigate('/dashboard');
        } catch (error) {
          console.error('Error fetching user profile:', error);
          // Still redirect to dashboard even if profile fetch fails
          navigate('/dashboard');
        }
      } else {
        navigate('/login?error=no_tokens');
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-[#0a0f1e] flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-400">Completing sign in...</p>
      </div>
    </div>
  );
};

export default GoogleCallback;

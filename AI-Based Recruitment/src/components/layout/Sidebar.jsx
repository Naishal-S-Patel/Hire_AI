import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, Search, Upload, Database, Briefcase, LogOut, Cpu } from 'lucide-react';
import { useState, useEffect } from 'react';

const Sidebar = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Load user from localStorage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
  }, []);

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
    { name: 'Candidates', path: '/candidates', icon: <Users size={20} /> },
    { name: 'Analytics', path: '/analytics', icon: <Database size={20} /> },
    { name: 'Talent Ingestion', path: '/ingestion', icon: <Upload size={20} /> },
  ];

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  // Get user initials for avatar
  const getInitials = (name) => {
    if (!name) return 'HR';
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <aside className="w-64 bg-card border-r border-border h-full flex flex-col shadow-sm relative z-20">
      <div className="p-6 border-b border-border/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center shadow-md shadow-primary/20">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground tracking-tight">Hire<span className="text-primary">AI</span></h1>
            <p className="text-xs text-muted-foreground font-medium">HR Dashboard</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                isActive
                  ? 'bg-primary/10 text-primary shadow-sm ring-1 ring-primary/20'
                  : 'text-muted-foreground hover:bg-muted/80 hover:text-foreground'
              }`
            }
          >
            <span className="mr-3">{item.icon}</span>
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-border/50 space-y-4">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors group"
        >
          <LogOut size={18} className="group-hover:scale-110 transition-transform" />
          <span>Logout</span>
        </button>
        <div className="flex items-center px-2 py-2 rounded-xl bg-muted/30 border border-border/40">
          {user?.picture ? (
            <img 
              src={user.picture} 
              alt={user.full_name || 'User'} 
              className="w-9 h-9 rounded-lg object-cover shadow-sm"
            />
          ) : (
            <div className="w-9 h-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-semibold text-sm shadow-sm border border-primary/20">
              {getInitials(user?.full_name)}
            </div>
          )}
          <div className="ml-3 overflow-hidden flex-1">
            <p className="text-sm font-semibold text-foreground truncate">
              {user?.full_name || 'HR Admin'}
            </p>
            <p className="text-xs text-muted-foreground truncate font-medium">
              {user?.email || 'hr@company.com'}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;

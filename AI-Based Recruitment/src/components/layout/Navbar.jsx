import { Bell, Search } from 'lucide-react';

const Navbar = () => {
  return (
    <header className="h-16 bg-white border-b border-border/60 flex items-center justify-between px-8 shadow-sm relative z-10">
      <div className="flex-1 max-w-2xl">
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2.5 border border-border/80 rounded-xl leading-5 bg-slate-50/50 placeholder-muted-foreground text-foreground focus:outline-none focus:bg-white focus:border-primary/50 focus:ring-4 focus:ring-primary/10 sm:text-sm transition-all shadow-sm"
            placeholder="Search candidates, jobs, or skills..."
          />
        </div>
      </div>
      <div className="ml-4 flex items-center space-x-6">
        <button className="text-muted-foreground hover:text-foreground relative p-2 hover:bg-slate-100 rounded-full transition-colors">
          <span className="absolute top-1.5 right-1.5 block h-2.5 w-2.5 rounded-full bg-destructive ring-2 ring-white"></span>
          <Bell className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
};

export default Navbar;

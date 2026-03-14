import { useState, useMemo } from 'react';
import { X, Search } from 'lucide-react';
import SkillGraph from './SkillGraph';

export const CandidateComparison = ({ allCandidates, onClose }) => {
  const [searchA, setSearchA] = useState('');
  const [searchB, setSearchB] = useState('');
  const [candidateA, setCandidateA] = useState(null);
  const [candidateB, setCandidateB] = useState(null);
  const [showDropdownA, setShowDropdownA] = useState(false);
  const [showDropdownB, setShowDropdownB] = useState(false);

  const filteredA = useMemo(() => {
    if (!searchA.trim()) return allCandidates.slice(0, 8);
    return allCandidates.filter(c =>
      c.name.toLowerCase().includes(searchA.toLowerCase()) ||
      c.email?.toLowerCase().includes(searchA.toLowerCase()) ||
      c.skills?.some(s => s.toLowerCase().includes(searchA.toLowerCase()))
    ).slice(0, 8);
  }, [searchA, allCandidates]);

  const filteredB = useMemo(() => {
    if (!searchB.trim()) return allCandidates.filter(c => c.id !== candidateA?.id).slice(0, 8);
    return allCandidates.filter(c =>
      c.id !== candidateA?.id && (
        c.name.toLowerCase().includes(searchB.toLowerCase()) ||
        c.email?.toLowerCase().includes(searchB.toLowerCase()) ||
        c.skills?.some(s => s.toLowerCase().includes(searchB.toLowerCase()))
      )
    ).slice(0, 8);
  }, [searchB, allCandidates, candidateA]);

  const selectA = (c) => { setCandidateA(c); setSearchA(c.name); setShowDropdownA(false); };
  const selectB = (c) => { setCandidateB(c); setSearchB(c.name); setShowDropdownB(false); };

  const bothSelected = candidateA && candidateB;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-slate-50 rounded-2xl shadow-2xl border border-border/60 w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden">
        
        <div className="px-6 py-4 border-b border-border/60 flex justify-between items-center bg-white">
          <h2 className="text-xl font-bold text-foreground tracking-tight">Compare Candidates</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-full text-slate-600 hover:text-foreground transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Candidate Selection */}
        <div className="p-6 border-b border-border/60 grid grid-cols-2 gap-6">
          {/* Select Candidate A */}
          <div className="relative">
            <label className="block text-sm font-medium text-slate-600 mb-2">Candidate 1</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <input
                type="text"
                value={searchA}
                onChange={e => { setSearchA(e.target.value); setShowDropdownA(true); setCandidateA(null); }}
                onFocus={() => setShowDropdownA(true)}
                placeholder="Search by name, email, or skill..."
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-border rounded-lg text-foreground placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
            {showDropdownA && filteredA.length > 0 && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-border rounded-lg shadow-xl max-h-48 overflow-y-auto">
                {filteredA.map(c => (
                  <button key={c.id} onClick={() => selectA(c)}
                    className="w-full text-left px-4 py-2.5 hover:bg-[#243044] text-sm transition-colors flex justify-between items-center">
                    <span className="text-foreground">{c.name}</span>
                    <span className="text-xs text-muted-foreground">ATS: {c.atsScore}</span>
                  </button>
                ))}
              </div>
            )}
            {candidateA && (
              <div className="mt-2 flex items-center gap-2 bg-primary/10 border border-primary/30 rounded-lg px-3 py-2">
                <div className="w-8 h-8 bg-primary text-foreground rounded-full flex items-center justify-center text-sm font-bold">{candidateA.name.charAt(0)}</div>
                <div>
                  <p className="text-sm font-medium text-foreground">{candidateA.name}</p>
                  <p className="text-xs text-slate-600">{candidateA.role}</p>
                </div>
              </div>
            )}
          </div>

          {/* Select Candidate B */}
          <div className="relative">
            <label className="block text-sm font-medium text-slate-600 mb-2">Candidate 2</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <input
                type="text"
                value={searchB}
                onChange={e => { setSearchB(e.target.value); setShowDropdownB(true); setCandidateB(null); }}
                onFocus={() => setShowDropdownB(true)}
                placeholder="Search by name, email, or skill..."
                className="w-full pl-10 pr-4 py-2.5 bg-white border border-border rounded-lg text-foreground placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
            {showDropdownB && filteredB.length > 0 && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-border rounded-lg shadow-xl max-h-48 overflow-y-auto">
                {filteredB.map(c => (
                  <button key={c.id} onClick={() => selectB(c)}
                    className="w-full text-left px-4 py-2.5 hover:bg-[#243044] text-sm transition-colors flex justify-between items-center">
                    <span className="text-foreground">{c.name}</span>
                    <span className="text-xs text-muted-foreground">ATS: {c.atsScore}</span>
                  </button>
                ))}
              </div>
            )}
            {candidateB && (
              <div className="mt-2 flex items-center gap-2 bg-purple-50 border border-purple-200 rounded-lg px-3 py-2">
                <div className="w-8 h-8 bg-purple-600 text-foreground rounded-full flex items-center justify-center text-sm font-bold">{candidateB.name.charAt(0)}</div>
                <div>
                  <p className="text-sm font-medium text-foreground">{candidateB.name}</p>
                  <p className="text-xs text-slate-600">{candidateB.role}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Comparison Table */}
        <div className="flex-1 overflow-auto p-6">
          {bothSelected ? (
            <div className="grid grid-cols-3 gap-6">
              {/* Headers Col */}
              <div className="col-span-1 border-r border-border/60 pr-4 space-y-6 flex flex-col pt-24 font-medium text-muted-foreground text-sm">
                <div className="h-10 flex items-center border-b border-border/60/50">Role</div>
                <div className="h-10 flex items-center border-b border-border/60/50">Experience</div>
                <div className="h-10 flex items-center border-b border-border/60/50">Location</div>
                <div className="h-10 flex items-center border-b border-border/60/50">ATS Score</div>
                <div className="h-10 flex items-center border-b border-border/60/50">Risk Level</div>
                <div className="h-32 flex items-center border-b border-border/60/50 mt-4 pt-4 border-t border-border/60">Top Skills</div>
                <div className="h-48 flex flex-col justify-center mt-4">Skill Match</div>
              </div>

              {/* Candidate Columns */}
              {[candidateA, candidateB].map((candidate, idx) => (
                <div key={candidate.id} className="col-span-1 space-y-6">
                  <div className="text-center pb-6 border-b border-border/60 h-24">
                    <div className={`w-12 h-12 ${idx === 0 ? 'bg-primary' : 'bg-purple-600'} text-foreground rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-2`}>
                      {(candidate.full_name || candidate.name || 'Unknown').charAt(0)}
                    </div>
                    <h3 className="font-bold text-foreground">{(candidate.full_name || candidate.name || 'Unknown')}</h3>
                  </div>
                  <div className="h-10 flex items-center text-sm text-slate-700 border-b border-border/60/50 font-medium">{candidate.role}</div>
                  <div className="h-10 flex items-center text-sm text-slate-700 border-b border-border/60/50">{(candidate.experience_years || candidate.experience || 0)}</div>
                  <div className="h-10 flex items-center text-sm text-slate-700 border-b border-border/60/50">{candidate.location}</div>
                  <div className="h-10 flex items-center text-sm font-bold text-primary border-b border-border/60/50">
                    {(candidate.ats_score || candidate.atsScore || 0)}/100 Match
                  </div>
                  <div className={`h-10 flex items-center text-sm font-bold border-b border-border/60/50 ${
                    candidate.fraudRisk === 'HIGH' ? 'text-destructive' : candidate.fraudRisk === 'MEDIUM' ? 'text-yellow-400' : 'text-success'
                  }`}>
                    {candidate.fraudRisk || 'LOW'}
                  </div>
                  <div className="h-32 flex flex-wrap content-start gap-2 border-b border-border/60/50 mt-4 pt-4 border-t border-border/60 overflow-hidden">
                    {candidate.skills.slice(0, 6).map((skill) => (
                      <span key={skill} className="px-2 py-1 bg-primary/10 text-primary/80 rounded text-xs font-medium border border-primary/20">
                        {skill}
                      </span>
                    ))}
                    {candidate.skills.length > 6 && <span className="text-xs text-muted-foreground mt-1">+{candidate.skills.length - 6} more</span>}
                  </div>
                  <div className="h-48 mt-4">
                    <SkillGraph data={candidate.skillMatches} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <Search className="w-12 h-12 mb-4 text-slate-400" />
              <p className="text-lg font-medium text-slate-600">Select two candidates above to compare</p>
              <p className="text-sm text-muted-foreground mt-1">Search by name, email, or skills</p>
            </div>
          )}
        </div>
        
        <div className="p-4 border-t border-border/60 bg-white flex justify-end">
          <button onClick={onClose} className="px-4 py-2 bg-white border border-border rounded-lg text-sm font-medium text-slate-700 hover:bg-[#243044] transition-colors">
            Close Comparison
          </button>
        </div>
      </div>
    </div>
  );
};

export default CandidateComparison;

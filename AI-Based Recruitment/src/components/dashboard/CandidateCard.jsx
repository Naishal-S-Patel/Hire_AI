import { MapPin, Briefcase } from 'lucide-react';
import FraudBadge from './FraudBadge';

export const CandidateCard = ({ candidate, isSelected, onClick }) => {
  return (
    <div 
      onClick={() => onClick(candidate)}
      className={`bg-white border p-5 rounded-xl cursor-pointer transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/5 ${
        isSelected 
          ? 'border-blue-500 ring-1 ring-blue-500 shadow-sm shadow-blue-500/10' 
          : 'border-border/60 hover:border-blue-400/50'
      }`}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-bold text-foreground tracking-tight">{(candidate.full_name || candidate.name || 'Unknown')}</h3>
          <p className="text-sm font-medium text-primary">{candidate.role}</p>
        </div>
        <div className="flex gap-2">
          {candidate.confidence_score && (
            <div className="text-center">
              <div className="text-xs text-muted-foreground">Confidence</div>
              <div className="text-lg font-bold text-success">{candidate.confidence_score.toFixed(1)}/10</div>
            </div>
          )}
          {candidate.technical_score && (
            <div className="text-center ml-3">
              <div className="text-xs text-muted-foreground">Technical</div>
              <div className="text-lg font-bold text-primary">{candidate.technical_score.toFixed(1)}/10</div>
            </div>
          )}
          <FraudBadge riskLevel={candidate.fraudRisk} />
        </div>
      </div>
      
      <div className="flex flex-col space-y-2 mt-4">
        <div className="flex items-center text-sm text-slate-600">
          <Briefcase className="w-4 h-4 mr-2 text-muted-foreground" />
          {(candidate.experience_years || candidate.experience || 0)} experience
        </div>
        <div className="flex items-center text-sm text-slate-600">
          <MapPin className="w-4 h-4 mr-2 text-muted-foreground" />
          {candidate.location}
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-border/60 flex flex-wrap gap-2">
        {candidate.skills.slice(0, 3).map(skill => (
          <span key={skill} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-primary/10 text-primary/80 border border-primary/20">
            {skill}
          </span>
        ))}
        {candidate.skills.length > 3 && (
          <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-700/50 text-slate-600 border border-border">
            +{candidate.skills.length - 3}
          </span>
        )}
      </div>
    </div>
  );
};

export default CandidateCard;

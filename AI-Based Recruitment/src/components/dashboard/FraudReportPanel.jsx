import { AlertTriangle, Clock, GraduationCap, FileWarning, Layers, CheckCircle, Loader2 } from 'lucide-react';

const FLAG_ICONS = {
  inflated_experience: FileWarning,
  timeline_inconsistency: Clock,
  inflated_skills: Layers,
  template_resume: FileWarning,
};

const SEVERITY_COLORS = {
  high: { bg: 'bg-red-500/20', text: 'text-destructive', label: 'bg-red-500/20 text-destructive' },
  medium: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'bg-yellow-500/20 text-yellow-400' },
  low: { bg: 'bg-orange-500/20', text: 'text-orange-400', label: 'bg-orange-500/20 text-orange-400' },
};

export const FraudReportPanel = ({ riskLevel, fraudScore, flags = [], isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="mt-6 border border-border/60 rounded-xl p-4 bg-slate-50 flex items-center gap-3">
        <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
        <p className="text-sm text-muted-foreground">Running fraud analysis...</p>
      </div>
    );
  }
  const isHighRisk = riskLevel === 'HIGH';

  if (riskLevel === 'LOW' && flags.length === 0) {
    return (
      <div className="mt-6 border border-success/20 rounded-xl p-4 bg-success/10 flex items-center gap-3">
        <CheckCircle className="w-5 h-5 text-success shrink-0" />
        <div>
          <p className="text-sm font-semibold text-success">No fraud indicators detected</p>
          <p className="text-xs text-green-500/80 mt-0.5">This resume passed all automated checks.</p>
        </div>
      </div>
    );
  }

  const headerColor = isHighRisk ? 'bg-destructive/10 border-destructive/20' : 'bg-yellow-500/10 border-yellow-500/30';
  const titleColor = isHighRisk ? 'text-destructive' : 'text-yellow-400';
  const badgeColor = isHighRisk ? 'bg-red-500/20 text-destructive' : 'bg-yellow-500/20 text-yellow-400';
  const iconColor = isHighRisk ? 'text-destructive' : 'text-yellow-400';

  return (
    <div className={`mt-6 border rounded-xl overflow-hidden ${isHighRisk ? 'border-destructive/20' : 'border-yellow-500/30'}`}>
      <div className={`px-4 py-3 flex items-center justify-between ${headerColor}`}>
        <div className="flex items-center gap-2">
          <AlertTriangle className={`w-5 h-5 ${iconColor}`} />
          <h3 className={`font-semibold tracking-tight ${titleColor}`}>AI Fraud & Risk Report</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-600">Risk Score: {fraudScore ?? 0}/100</span>
          <span className={`px-2 py-1 text-xs font-bold rounded-lg uppercase ${badgeColor}`}>
            {riskLevel} RISK
          </span>
        </div>
      </div>

      <div className="p-4 bg-slate-50 space-y-3">
        {flags.length === 0 ? (
          <p className="text-sm text-muted-foreground italic">No specific flags recorded.</p>
        ) : (
          flags.map((flag, i) => {
            const Icon = FLAG_ICONS[flag.type] || AlertTriangle;
            const colors = SEVERITY_COLORS[flag.severity] || SEVERITY_COLORS.low;
            return (
              <div key={i} className="flex items-start gap-3">
                <div className={`p-1.5 rounded-md mt-0.5 shrink-0 ${colors.bg} ${colors.text}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-semibold text-foreground capitalize">
                      {flag.type.replace(/_/g, ' ')}
                    </h4>
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium uppercase ${colors.label}`}>
                      {flag.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5">{flag.message}</p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default FraudReportPanel;

import { AlertTriangle, ShieldCheck, AlertCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

export const FraudBadge = ({ riskLevel, className }) => {
  const getBadgeConfig = () => {
    switch (riskLevel?.toUpperCase()) {
      case 'LOW':
        return {
          color: 'bg-green-100 text-green-800 border-green-200',
          icon: <ShieldCheck className="w-4 h-4 mr-1 text-green-600" />,
          label: 'Low Risk',
        };
      case 'MEDIUM':
        return {
          color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          icon: <AlertCircle className="w-4 h-4 mr-1 text-yellow-600" />,
          label: 'Medium Risk',
        };
      case 'HIGH':
        return {
          color: 'bg-red-100 text-red-800 border-red-200',
          icon: <AlertTriangle className="w-4 h-4 mr-1 text-red-600" />,
          label: 'High Risk',
        };
      default:
        return {
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          icon: null,
          label: 'Unknown',
        };
    }
  };

  const config = getBadgeConfig();

  return (
    <div
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border shadow-sm',
        config.color,
        className
      )}
    >
      {config.icon}
      {config.label}
    </div>
  );
};

export default FraudBadge;

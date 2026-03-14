import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip, Legend } from 'recharts';

/**
 * Expected data format:
 * [
 *   { skill: "React", candidate_score: 85, jd_required: 90 },
 *   { skill: "Python", candidate_score: 70, jd_required: 60 }
 * ]
 */
export const SkillGraph = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center bg-slate-50 rounded-xl border border-border/60 text-sm text-muted-foreground">
        No skill data available
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis dataKey="skill" tick={{ fill: '#9ca3af', fontSize: 12 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 10 }} />
          
          <Radar
            name="Job Requirement"
            dataKey="jd_required"
            stroke="#94a3b8"
            fill="#94a3b8"
            fillOpacity={0.2}
            strokeDasharray="3 3"
          />
          <Radar
            name="Candidate"
            dataKey="candidate_score"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.4}
          />
          
          <Tooltip 
            contentStyle={{ backgroundColor: '#1a2332', border: '1px solid #374151', borderRadius: '8px', color: '#fff' }}
          />
          <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '10px', color: '#9ca3af' }} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SkillGraph;

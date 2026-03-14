import CandidateCard from './CandidateCard';

export const CandidateList = ({ candidates, isLoading, selectedId, onSelect }) => {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="animate-pulse bg-white border border-border/60 rounded-xl p-5 h-40">
            <div className="h-4 bg-gray-700 rounded w-1/2 mb-4"></div>
            <div className="h-3 bg-gray-700 rounded w-1/3 mb-2"></div>
            <div className="h-3 bg-gray-700 rounded w-1/4 mb-6"></div>
            <div className="flex gap-2">
              <div className="h-6 w-16 bg-gray-700 rounded"></div>
              <div className="h-6 w-16 bg-gray-700 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!candidates || candidates.length === 0) {
    return (
      <div className="mt-6 text-center text-muted-foreground p-8 border border-dashed border-border rounded-xl bg-white">
        No candidates found.
      </div>
    );
  }

  return (
    <div className="space-y-4 overflow-y-auto pr-2 h-full pb-20 custom-scrollbar">
      {candidates.map(candidate => (
        <CandidateCard 
          key={candidate.id}
          candidate={candidate}
          isSelected={selectedId === candidate.id}
          onClick={onSelect}
        />
      ))}
    </div>
  );
};

export default CandidateList;

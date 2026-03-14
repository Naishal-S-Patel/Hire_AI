import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCandidates, uploadResume, getCandidateSummary, searchCandidates, compareCandidates } from '../services/api';

export const useCandidates = () => {
  return useQuery({
    queryKey: ['candidates'],
    queryFn: getCandidates,
  });
};

export const useUploadResume = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadResume,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
    },
  });
};

export const useCandidateSummary = (id) => {
  return useQuery({
    queryKey: ['candidateSummary', id],
    queryFn: () => getCandidateSummary(id),
    enabled: !!id,
  });
};

export const useSearchCandidates = (query) => {
    return useQuery({
        queryKey: ['searchCandidates', query],
        queryFn: () => searchCandidates(query),
        enabled: !!query && query.length > 2,
    });
};

export const useCompareCandidates = (ids) => {
    return useQuery({
        queryKey: ['compareCandidates', ids],
        queryFn: () => compareCandidates(ids),
        enabled: ids.length > 0,
    });
};

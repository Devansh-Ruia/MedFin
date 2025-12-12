import { useState, useCallback } from 'react';
import type { ApiResponse, LoadingState } from '@/types';

interface UseApiState<T> extends LoadingState {
  data: T | null;
}

interface UseApiReturn<T, P extends unknown[]> extends UseApiState<T> {
  execute: (...params: P) => Promise<T | null>;
  reset: () => void;
}

export function useApi<T, P extends unknown[] = []>(
  apiFunction: (...params: P) => Promise<ApiResponse<T>>
): UseApiReturn<T, P> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const execute = useCallback(async (...params: P): Promise<T | null> => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    
    try {
      const response = await apiFunction(...params);
      
      if (response.success && response.data) {
        setState({ data: response.data, isLoading: false, error: null });
        return response.data;
      } else {
        const errorMsg = response.error?.message || 'Request failed';
        setState({ data: null, isLoading: false, error: errorMsg });
        return null;
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'An error occurred';
      setState({ data: null, isLoading: false, error: errorMsg });
      return null;
    }
  }, [apiFunction]);

  const reset = useCallback(() => {
    setState({ data: null, isLoading: false, error: null });
  }, []);

  return { ...state, execute, reset };
}
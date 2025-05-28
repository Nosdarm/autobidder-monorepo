import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchAIPrompts,
  fetchAIPrompt,
  createAIPrompt,
  updateAIPrompt,
  deleteAIPrompt,
  previewAIPrompt,
  AIPrompt,
  NewAIPromptData,
  UpdateAIPromptData,
  PreviewPromptResponse,
} from '@/services/aiPromptService';
import { aiPromptKeys } from '@/lib/queryKeys';
import { useToast } from '@/hooks/useToast';

// Hook to fetch all AI prompts
export function useAIPrompts() {
  return useQuery<AIPrompt[], Error>({
    queryKey: aiPromptKeys.lists(),
    queryFn: fetchAIPrompts,
  });
}

// Hook to fetch a single AI prompt by ID
export function useAIPrompt(promptId: string) {
  return useQuery<AIPrompt, Error>({
    queryKey: aiPromptKeys.detail(promptId),
    queryFn: () => fetchAIPrompt(promptId),
    enabled: !!promptId,
  });
}

// Hook to create a new AI prompt
export function useCreateAIPrompt() {
  const queryClient = useQueryClient();
  const { showToastSuccess, showToastError } = useToast();

  return useMutation<AIPrompt, Error, NewAIPromptData>({
    mutationFn: createAIPrompt,
    onSuccess: (newPrompt) => {
      queryClient.invalidateQueries({ queryKey: aiPromptKeys.lists() });
      showToastSuccess(`AI Prompt "${newPrompt.name}" created successfully!`);
    },
    onError: (error) => {
      showToastError(`Error creating AI prompt: ${error.message}`);
    },
  });
}

// Hook to update an existing AI prompt
export function useUpdateAIPrompt() {
  const queryClient = useQueryClient();
  const { showToastSuccess, showToastError } = useToast();

  return useMutation<AIPrompt, Error, { id: string; data: UpdateAIPromptData }>({
    mutationFn: ({ id, data }) => updateAIPrompt(id, data),
    onSuccess: (updatedPrompt) => {
      queryClient.invalidateQueries({ queryKey: aiPromptKeys.lists() });
      queryClient.invalidateQueries({ queryKey: aiPromptKeys.detail(updatedPrompt.id) });
      showToastSuccess(`AI Prompt "${updatedPrompt.name}" updated successfully!`);
    },
    onError: (error) => {
      showToastError(`Error updating AI prompt: ${error.message}`);
    },
  });
}

// Hook to delete an AI prompt
export function useDeleteAIPrompt() {
  const queryClient = useQueryClient();
  const { showToastSuccess, showToastError } = useToast();

  return useMutation<void, Error, string>({ // string is the promptId
    mutationFn: deleteAIPrompt,
    onSuccess: (_, promptId) => {
      queryClient.invalidateQueries({ queryKey: aiPromptKeys.lists() });
      queryClient.removeQueries({ queryKey: aiPromptKeys.detail(promptId) });
      showToastSuccess('AI Prompt deleted successfully!');
    },
    onError: (error) => {
      showToastError(`Error deleting AI prompt: ${error.message}`);
    },
  });
}

// Hook for AI Prompt Preview
export function usePreviewAIPrompt() {
  const { showToastError } = useToast();
  // No query invalidation needed for preview, it's a transient action.
  // Success toast is handled by the component upon receiving data.
  return useMutation<PreviewPromptResponse, Error, { promptText: string; testInput: string }>({
    mutationFn: ({ promptText, testInput }) => previewAIPrompt(promptText, testInput),
    onError: (error) => {
      showToastError(`Error generating preview: ${error.message}`);
    },
  });
}

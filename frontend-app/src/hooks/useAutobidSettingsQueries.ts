import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchAutobidSettingsForAllProfiles,
  updateAllAutobidSettings,
  ProfileWithSettings,
  // AutobidSettings, // Not directly used for updateAll
} from '@/services/autobidSettingsService';
import { autobidSettingsKeys } from '@/lib/queryKeys';
import { useToast } from '@/hooks/useToast';

// Hook to fetch autobid settings for all profiles
export function useAllAutobidSettings() {
  return useQuery<ProfileWithSettings[], Error>({
    queryKey: autobidSettingsKeys.settingsForAllProfiles(),
    queryFn: fetchAutobidSettingsForAllProfiles,
  });
}

// Hook to update all autobid settings (global save)
export function useUpdateAllAutobidSettings() {
  const queryClient = useQueryClient();
  const { showToastSuccess, showToastError } = useToast();

  return useMutation<void, Error, ProfileWithSettings[]>({
    mutationFn: updateAllAutobidSettings,
    onSuccess: () => {
      // Invalidate the query for all autobid settings to refetch fresh data
      queryClient.invalidateQueries({ queryKey: autobidSettingsKeys.settingsForAllProfiles() });
      showToastSuccess('All autobid settings saved successfully!');
    },
    onError: (error) => {
      showToastError(`Error saving autobid settings: ${error.message}`);
    },
  });
}

// Example of a hook for updating individual profile settings, if needed later
// export function useUpdateAutobidSettingForProfile() {
//   const queryClient = useQueryClient();
//   const { showToastSuccess, showToastError } = useToast();
//
//   return useMutation<AutobidSettings, Error, { profileId: string; settings: AutobidSettings }>({
//     mutationFn: ({ profileId, settings }) => updateAutobidSettingForProfile(profileId, settings),
//     onSuccess: (updatedSettings, { profileId }) => {
//       // Invalidate the global list
//       queryClient.invalidateQueries({ queryKey: autobidSettingsKeys.settingsForAllProfiles() });
//       // Optionally, update the specific profile's settings in the cache if you have a detailed query for it
//       // queryClient.setQueryData(autobidSettingsKeys.settingsForProfile(profileId), updatedSettings);
//       showToastSuccess(`Settings for profile updated successfully!`);
//     },
//     onError: (error) => {
//       showToastError(`Error updating settings: ${error.message}`);
//     },
//   });
// }

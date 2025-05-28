import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchProfiles,
  fetchProfile,
  createProfile,
  updateProfile,
  deleteProfile,
  Profile,
  NewProfileData,
  UpdateProfileData,
} from '@/services/profileService'; // Assuming this path is correct
import { profileKeys } from '@/lib/queryKeys';
import { useToast } from '@/hooks/useToast';

// Hook to fetch all profiles
export function useProfiles() {
  return useQuery<Profile[], Error>({
    queryKey: profileKeys.lists(),
    queryFn: fetchProfiles,
  });
}

// Hook to fetch a single profile by ID
export function useProfile(profileId: string) {
  return useQuery<Profile, Error>({
    queryKey: profileKeys.detail(profileId),
    queryFn: () => fetchProfile(profileId),
    enabled: !!profileId, // Only run query if profileId is truthy
  });
}

// Hook to create a new profile
export function useCreateProfile() {
  const queryClient = useQueryClient();
  const { showToastSuccess, showToastError } = useToast();

  return useMutation<Profile, Error, NewProfileData>({
    mutationFn: createProfile,
    onSuccess: (newProfile) => {
      queryClient.invalidateQueries({ queryKey: profileKeys.lists() });
      // Optionally, directly set the new data in the cache for the detail query if needed immediately
      // queryClient.setQueryData(profileKeys.detail(newProfile.id), newProfile);
      showToastSuccess(`Profile "${newProfile.name}" created successfully!`);
    },
    onError: (error) => {
      showToastError(`Error creating profile: ${error.message}`);
    },
  });
}

// Hook to update an existing profile
export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const { showToastSuccess, showToastError } = useToast();

  return useMutation<Profile, Error, { id: string; data: UpdateProfileData }>({
    mutationFn: ({ id, data }) => updateProfile(id, data),
    onSuccess: (updatedProfile) => {
      // Invalidate the list of profiles
      queryClient.invalidateQueries({ queryKey: profileKeys.lists() });
      // Invalidate the specific profile detail query
      queryClient.invalidateQueries({ queryKey: profileKeys.detail(updatedProfile.id) });
      // Or, update the cache directly
      // queryClient.setQueryData(profileKeys.detail(updatedProfile.id), updatedProfile);
      showToastSuccess(`Profile "${updatedProfile.name}" updated successfully!`);
    },
    onError: (error) => {
      showToastError(`Error updating profile: ${error.message}`);
    },
  });
}

// Hook to delete a profile
export function useDeleteProfile() {
  const queryClient = useQueryClient();
  const { showToastSuccess, showToastError } = useToast();

  return useMutation<void, Error, string>({ // string is the profileId
    mutationFn: deleteProfile,
    onSuccess: (_, profileId) => { // profileId is passed as context or directly if mutationFn is adapted
      queryClient.invalidateQueries({ queryKey: profileKeys.lists() });
      // If you also have detailed views, you might want to remove it from cache or invalidate
      queryClient.removeQueries({ queryKey: profileKeys.detail(profileId) });
      showToastSuccess('Profile deleted successfully!');
    },
    onError: (error) => {
      showToastError(`Error deleting profile: ${error.message}`);
    },
  });
}

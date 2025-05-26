import { authService } from './authService'; // To get the configured apiClient

const apiClient = authService.getClient(); // Use the same configured Axios instance

// Interface Definitions (matching backend schemas/models)
export interface Profile {
  id: string;
  user_id: string; // Owner User ID
  name: string;
  profile_type: 'personal' | 'agency';
  autobid_enabled: boolean;
  // New fields from a previous task (ensure they are included if your backend sends them)
  skills?: string[] | null; // Or List[str] - matching Pydantic Optional[List[str]]
  experience_level?: string | null;
}

export interface ProfileCreate {
  name: string;
  profile_type: 'personal' | 'agency';
  autobid_enabled?: boolean; // Optional on create, defaults to False on backend
  skills?: string[] | null;
  experience_level?: string | null;
}

export interface ProfileUpdate {
  name?: string;
  profile_type?: 'personal' | 'agency';
  autobid_enabled?: boolean;
  skills?: string[] | null;
  experience_level?: string | null;
}


// ProfileService Functions
export const profileService = {
  getAllProfiles: async (): Promise<Profile[]> => {
    try {
      const response = await apiClient.get<Profile[]>('/profiles/');
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch profiles.';
      throw new Error(errorMessage);
    }
  },

  getProfileById: async (id: string): Promise<Profile> => {
    try {
      const response = await apiClient.get<Profile>(`/profiles/${id}`);
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch profile.';
      throw new Error(errorMessage);
    }
  },

  createProfile: async (profileData: ProfileCreate): Promise<Profile> => {
    try {
      const response = await apiClient.post<Profile>('/profiles/', profileData);
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create profile.';
      throw new Error(errorMessage);
    }
  },

  updateProfile: async (id: string, profileData: ProfileUpdate): Promise<Profile> => {
    try {
      const response = await apiClient.put<Profile>(`/profiles/${id}`, profileData);
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to update profile.';
      throw new Error(errorMessage);
    }
  },

  deleteProfile: async (id: string): Promise<void> => {
    try {
      await apiClient.delete(`/profiles/${id}`);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to delete profile.';
      throw new Error(errorMessage);
    }
  },
};

export default profileService;

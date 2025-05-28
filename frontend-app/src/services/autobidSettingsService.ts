// frontend-app/src/services/autobidSettingsService.ts

// --- Interfaces ---
// Re-using from AutobidSettingsPage.tsx for consistency, ideally these would be shared types
export interface ProfileForSettings {
  id: string;
  name: string;
}

export interface AutobidSettings {
  isEnabled: boolean;
  interval: number;
  dailyLimit?: number;
}

export interface ProfileWithSettings {
  profile: ProfileForSettings;
  settings: AutobidSettings;
}

// --- Mock Data Store ---
const mockProfilesForService: ProfileForSettings[] = [
  { id: 'profile1', name: 'My Main Upwork Profile' },
  { id: 'profile2', name: 'Agency Client - Tech Lead Roles' },
  { id: 'profile3', name: 'Side Gig - Quick Projects' },
];

const defaultSettingsValues: AutobidSettings = {
  isEnabled: false,
  interval: 30,
  dailyLimit: 5,
};

let mockAutobidSettingsDB: ProfileWithSettings[] = mockProfilesForService.map((profile, index) => ({
  profile,
  settings: {
    ...defaultSettingsValues,
    isEnabled: index === 0, // Enable first profile by default
    interval: 15 + index * 5,
    dailyLimit: 5 + index * 2,
  },
}));

const simulateDelay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

// --- API Service Functions ---

export const fetchAutobidSettingsForAllProfiles = async (): Promise<ProfileWithSettings[]> => {
  await simulateDelay();
  console.log("API: Fetching autobid settings for all profiles");
  // Return a deep copy to prevent direct mutation of the mock DB by consumers
  return JSON.parse(JSON.stringify(mockAutobidSettingsDB));
};

// This function might be useful if individual profile settings could be updated separately
// For now, the main requirement is updateAllAutobidSettings
export const updateAutobidSettingForProfile = async (profileId: string, settings: AutobidSettings): Promise<AutobidSettings> => {
  await simulateDelay();
  console.log(`API: Updating autobid settings for profile ${profileId}`, settings);
  const profileIndex = mockAutobidSettingsDB.findIndex(pws => pws.profile.id === profileId);
  if (profileIndex === -1) {
    throw new Error(`Profile with id ${profileId} not found for settings update.`);
  }
  mockAutobidSettingsDB[profileIndex].settings = { ...settings };
  return JSON.parse(JSON.stringify(mockAutobidSettingsDB[profileIndex].settings));
};

export const updateAllAutobidSettings = async (allSettings: ProfileWithSettings[]): Promise<void> => {
  await simulateDelay(1000);
  console.log("API: Updating all autobid settings", allSettings);
  // Basic validation: ensure all provided profiles exist in our mock DB
  // In a real API, this would be handled by the backend.
  const allIdsExist = allSettings.every(s => mockProfilesForService.find(p => p.id === s.profile.id));
  if (!allIdsExist) {
    throw new Error("One or more profiles in the settings update do not exist.");
  }
  // Simulate a potential global error
  if (allSettings.some(s => s.profile.name.toLowerCase().includes("fail global save"))) {
      throw new Error("Simulated global save failure for autobid settings.");
  }

  // Update our mock DB
  mockAutobidSettingsDB = JSON.parse(JSON.stringify(allSettings)); // Replace entire DB state with new settings
  console.log("API: All autobid settings updated successfully in mock DB.");
  // No return value for a bulk update typically, or could return the updated set.
};

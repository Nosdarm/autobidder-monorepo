// frontend-app/src/services/aiPromptService.ts

// --- Interfaces ---
export interface AIPrompt {
  id: string;
  name: string;
  promptText: string;
  profileId?: string | null;
  isActive: boolean;
  createdAt: Date | string; // Store as ISO string, convert to Date on fetch
}

export interface NewAIPromptData {
  name: string;
  promptText: string;
  profileId?: string | null;
  isActive: boolean;
}

export interface UpdateAIPromptData extends Partial<NewAIPromptData> {}

export interface PreviewPromptResponse {
  previewText: string;
}

// --- Mock Data Store ---
let mockAIPromptsDB: AIPrompt[] = [
  { id: 'p1', name: 'Cover Letter Intro', promptText: 'Write a compelling opening paragraph for a cover letter for a {JOB_TITLE} role focusing on {SKILL_1} and {SKILL_2}. The company is {COMPANY_NAME}.', profileId: '1', isActive: true, createdAt: new Date(2023, 10, 20).toISOString() },
  { id: 'p2', name: 'Project Summary Generator', promptText: 'Summarize a project based on the following key points: {KEY_POINTS}. The project goal was {PROJECT_GOAL}.', profileId: null, isActive: false, createdAt: new Date(2023, 11, 5).toISOString() },
  { id: 'p3', name: 'Follow-up Email Template', promptText: 'Draft a polite follow-up email after a job application for {JOB_TITLE} at {COMPANY_NAME}. Mention interest in {SPECIFIC_ASPECT}.', profileId: '2', isActive: true, createdAt: new Date().toISOString() },
];

const simulateDelay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

// --- API Service Functions ---

export const fetchAIPrompts = async (): Promise<AIPrompt[]> => {
  await simulateDelay();
  console.log("API: Fetching all AI prompts");
  return mockAIPromptsDB.map(p => ({ ...p, createdAt: new Date(p.createdAt) }));
};

export const fetchAIPrompt = async (id: string): Promise<AIPrompt> => {
  await simulateDelay();
  console.log(`API: Fetching AI prompt with id ${id}`);
  const prompt = mockAIPromptsDB.find(p => p.id === id);
  if (!prompt) {
    throw new Error(`AI Prompt with id ${id} not found`);
  }
  return { ...prompt, createdAt: new Date(prompt.createdAt) };
};

export const createAIPrompt = async (data: NewAIPromptData): Promise<AIPrompt> => {
  await simulateDelay(700);
  console.log("API: Creating AI prompt with data:", data);
  if (data.name.toLowerCase().includes("error")) {
    throw new Error("Failed to create AI prompt due to an error keyword in name.");
  }
  const newPrompt: AIPrompt = {
    id: `p${Date.now()}`, // Simple ID generation
    ...data,
    createdAt: new Date().toISOString(),
  };
  mockAIPromptsDB.push(newPrompt);
  return { ...newPrompt, createdAt: new Date(newPrompt.createdAt) };
};

export const updateAIPrompt = async (id: string, data: UpdateAIPromptData): Promise<AIPrompt> => {
  await simulateDelay();
  console.log(`API: Updating AI prompt ${id} with data:`, data);
  const promptIndex = mockAIPromptsDB.findIndex(p => p.id === id);
  if (promptIndex === -1) {
    throw new Error(`AI Prompt with id ${id} not found for update`);
  }
  if (data.name && data.name.toLowerCase().includes("error")) {
    throw new Error("Failed to update AI prompt due to an error keyword in name.");
  }
  mockAIPromptsDB[promptIndex] = { ...mockAIPromptsDB[promptIndex], ...data };
  return { ...mockAIPromptsDB[promptIndex], createdAt: new Date(mockAIPromptsDB[promptIndex].createdAt) };
};

export const deleteAIPrompt = async (id: string): Promise<void> => {
  await simulateDelay(1000);
  console.log(`API: Deleting AI prompt with id ${id}`);
  const initialLength = mockAIPromptsDB.length;
  mockAIPromptsDB = mockAIPromptsDB.filter(p => p.id !== id);
  if (mockAIPromptsDB.length === initialLength) {
    throw new Error(`AI Prompt with id ${id} not found for deletion`);
  }
};

export const previewAIPrompt = async (promptText: string, testInput: string): Promise<PreviewPromptResponse> => {
  await simulateDelay(1000);
  console.log(`API: Generating preview for prompt text with input: "${testInput}"`);
  if (testInput.toLowerCase().includes("fail preview")) {
    throw new Error("Simulated failure generating preview.");
  }
  // Basic placeholder replacement simulation
  let generatedText = promptText.replace(/{[^{}]+}/g, `[${testInput || 'SAMPLE_INPUT'}]`);
  generatedText = `--- SIMULATED PREVIEW ---\n${generatedText}\n--- END SIMULATED PREVIEW ---`;
  return { previewText: generatedText };
};

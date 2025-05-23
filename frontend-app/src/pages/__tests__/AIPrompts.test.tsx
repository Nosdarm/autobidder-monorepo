import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom'; // For extended matchers like .toBeInTheDocument()
import { vi } from 'vitest'; // Assuming Vitest based on Vite in package.json

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ profileId: 'test-profile-123' }),
  };
});

// Mock the api module
vi.mock('../../lib/axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

// Import the component and the mocked api after all mocks are set up
import AIPrompts from '../AIPrompts';
import api from '../../lib/axios'; // This will be the mocked version

// Helper to create a mock AIPrompt
const createMockPrompt = (id: string, name: string, prompt_text: string, profile_id: string, is_active: boolean = false) => ({
  id,
  name,
  prompt_text,
  profile_id,
  is_active,
});

describe('AIPrompts Component', () => {
  // Placeholder for tests - will be filled in next steps
  const mockApi = api as vi.Mocked<typeof api>; // Type assertion for mocked api

  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks(); 
  });

  test('Test Initial Render and Fetching Prompts', async () => {
    const mockPrompts = [
      createMockPrompt('1', 'Prompt 1', 'Text 1', 'test-profile-123', true),
      createMockPrompt('2', 'Prompt 2', 'Text 2', 'test-profile-123'),
    ];
    mockApi.get.mockResolvedValueOnce({ data: mockPrompts });

    render(<AIPrompts />);

    expect(mockApi.get).toHaveBeenCalledWith('/prompts/profile/test-profile-123');
    
    // Wait for prompts to be displayed
    await waitFor(() => {
      expect(screen.getByText('Prompt 1')).toBeInTheDocument();
      expect(screen.getByText('Text 1')).toBeInTheDocument();
      expect(screen.getByText('[активный]')).toBeInTheDocument();
      expect(screen.getByText('Prompt 2')).toBeInTheDocument();
      expect(screen.getByText('Text 2')).toBeInTheDocument();
    });
  });

  test('Test Form Input for New Prompt', () => {
    render(<AIPrompts />);
    
    const nameInput = screen.getByPlaceholderText('Название') as HTMLInputElement;
    const promptTextInput = screen.getByPlaceholderText('Текст промта') as HTMLTextAreaElement;

    fireEvent.change(nameInput, { target: { value: 'New Test Prompt' } });
    fireEvent.change(promptTextInput, { target: { value: 'This is the prompt text.' } });

    expect(nameInput.value).toBe('New Test Prompt');
    expect(promptTextInput.value).toBe('This is the prompt text.');
  });

  test('Test Adding a New Prompt', async () => {
    const initialPrompts: any[] = []; // Start with no prompts
    const newPromptData = { name: 'Newly Added Prompt', prompt_text: 'Newly added text' };
    const newPromptFull = createMockPrompt('new-id-123', newPromptData.name, newPromptData.prompt_text, 'test-profile-123');

    // First call for initial fetch
    mockApi.get.mockResolvedValueOnce({ data: initialPrompts });
    // Mock for successful post
    mockApi.post.mockResolvedValueOnce({ data: newPromptFull }); // Assuming POST returns the created prompt
    // Second call for fetch after adding
    mockApi.get.mockResolvedValueOnce({ data: [newPromptFull] });


    render(<AIPrompts />);

    // Wait for initial render (even if no prompts)
    await screen.findByText('AI-промты для профиля #test-profile-123');

    const nameInput = screen.getByPlaceholderText('Название');
    const promptTextInput = screen.getByPlaceholderText('Текст промта');
    const addButton = screen.getByText('Добавить промт');

    // Fill the form
    fireEvent.change(nameInput, { target: { value: newPromptData.name } });
    fireEvent.change(promptTextInput, { target: { value: newPromptData.prompt_text } });
    
    // Submit the form
    fireEvent.click(addButton);

    // Check if api.post was called correctly
    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith('/prompts/', {
        name: newPromptData.name,
        prompt_text: newPromptData.prompt_text,
        profile_id: 'test-profile-123', // from useParams mock
        is_active: false, // default for new prompts in component logic
      });
    });

    // Check if api.get was called again to refresh
    await waitFor(() => {
      expect(mockApi.get).toHaveBeenCalledTimes(2); // Initial fetch + fetch after add
    });
    
    // Check if the new prompt is displayed
    await waitFor(() => {
      expect(screen.getByText(newPromptData.name)).toBeInTheDocument();
      expect(screen.getByText(newPromptData.prompt_text)).toBeInTheDocument();
    });
  });

  test('Test Generating a Preview Successfully', async () => {
    const promptId = 'p1';
    const mockPrompts = [createMockPrompt(promptId, 'Preview Test Prompt', 'Preview text {description}', 'test-profile-123')];
    mockApi.get.mockResolvedValueOnce({ data: mockPrompts });
    mockApi.post.mockResolvedValueOnce({ data: { preview: "Generated preview: Test description input" } });

    render(<AIPrompts />);

    // Wait for the prompt to render
    await screen.findByText('Preview Test Prompt');
    
    const previewTextareas = screen.getAllByPlaceholderText('Введите описание джобы для теста');
    // Assuming the first textarea corresponds to the first prompt
    const previewTextarea = previewTextareas[0]; 
    const previewButton = screen.getAllByText('Сгенерировать по описанию')[0];

    fireEvent.change(previewTextarea, { target: { value: "Test description input" } });
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith(`/prompts/${promptId}/preview`, {
        description: "Test description input",
      });
    });

    await waitFor(() => {
      expect(screen.getByText("Generated preview: Test description input")).toBeInTheDocument();
    });
  });

  test('Test Handling 429 Error on Preview', async () => {
    const promptId = 'p2';
    const mockPrompts = [createMockPrompt(promptId, '429 Error Test', 'Error test {description}', 'test-profile-123')];
    mockApi.get.mockResolvedValueOnce({ data: mockPrompts });

    // Mock api.post to simulate a 429 error
    mockApi.post.mockRejectedValueOnce({
      isAxiosError: true, // Important for AxiosError instance check
      response: { status: 429, data: { detail: "Rate limit exceeded" } },
    });

    render(<AIPrompts />);

    // Wait for the prompt to render
    await screen.findByText('429 Error Test');

    const previewTextareas = screen.getAllByPlaceholderText('Введите описание джобы для теста');
    const previewTextarea = previewTextareas[0]; // Assuming it's the first/only one for this test
    const previewButton = screen.getAllByText('Сгенерировать по описанию')[0];

    fireEvent.change(previewTextarea, { target: { value: "Trigger 429 error" } });
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(mockApi.post).toHaveBeenCalledWith(`/prompts/${promptId}/preview`, {
        description: "Trigger 429 error",
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Вы слишком часто делаете запросы. Пожалуйста, подождите минуту.')).toBeInTheDocument();
    });
  });
});

// If not using a global test setup file, you might need to configure Vitest/Jest globals
// or ensure necessary polyfills for things like 'fetch' if your component indirectly uses them,
// though with Axios mocking, direct fetch polyfills might not be needed for these tests.

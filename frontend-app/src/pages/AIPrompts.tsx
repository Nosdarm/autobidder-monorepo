import React, { useEffect, useState } from 'react';
import api from '@/lib/axios'; // Updated axios import
import { AxiosError } from 'axios'; // For type checking
import { useParams } from 'react-router-dom';

type AIPrompt = {
  id: string;          // Changed from number
  name: string;
  prompt_text: string;
  profile_id: string;  // Changed from number
  is_active: boolean;
};

const AIPrompts: React.FC = () => {
  const { profileId } = useParams<{ profileId: string }>(); // Ensure profileId is typed as string
  const [prompts, setPrompts] = useState<AIPrompt[]>([]);
  const [name, setName] = useState('');
  const [promptText, setPromptText] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null); // Changed to string
  const [previewInputs, setPreviewInputs] = useState<Record<string, string>>({}); // Key changed to string
  const [previewResults, setPreviewResults] = useState<Record<string, string>>({}); // Key changed to string
  const [previewErrorMessages, setPreviewErrorMessages] = useState<Record<string, string>>({}); // Key changed to string

  const fetchPrompts = async () => {
    if (!profileId) return;
    const res = await api.get(`/prompts/profile/${profileId}`); // Use api
    setPrompts(res.data);
  };

  useEffect(() => {
    fetchPrompts();
  }, [profileId]);

  const handleSave = async () => {
    if (!name || !promptText || !profileId) return;

    if (editingId) {
      await api.put(`/prompts/${editingId}`, { name, prompt_text: promptText }); 
    } else {
      // Ensure profileId is defined before using it. The check at the start of function should handle this.
      if (!profileId) {
        console.error("Profile ID is undefined, cannot save prompt.");
        // Optionally set an error message for the user here
        return;
      }
      await api.post(`/prompts/`, { 
        name,
        prompt_text: promptText,
        profile_id: profileId, // Changed from parseInt(profileId)
        is_active: false
      });
    }

    setName('');
    setPromptText('');
    setEditingId(null);
    fetchPrompts();
  };

  const handleEdit = (prompt: AIPrompt) => {
    setName(prompt.name);
    setPromptText(prompt.prompt_text);
    setEditingId(prompt.id); // prompt.id is now string
  };

  const handleDelete = async (id: string) => { // Changed id to string
    await api.delete(`/prompts/${id}`); 
    fetchPrompts();
  };

  const setActivePrompt = async (id: string) => { // Changed id to string
    await api.post(`/prompts/${id}/set-active`); 
    fetchPrompts();
  };

  const handlePreview = async (id: string, description: string) => { // Changed id to string
    // Clear previous errors and results for this prompt
    setPreviewErrorMessages(prev => ({ ...prev, [id]: '' }));
    setPreviewResults(prev => ({ ...prev, [id]: '' }));

    if (!description) {
      setPreviewErrorMessages(prev => ({ ...prev, [id]: 'Пожалуйста, введите описание джобы.' }));
      return;
    }

    try {
      const res = await api.post(`/prompts/${id}/preview`, { description }); // Use api
      setPreviewResults((prev) => ({ ...prev, [id]: res.data.preview }));
    } catch (error) {
      console.error("Error during preview generation:", error);
      if (error instanceof AxiosError && error.response?.status === 429) {
        setPreviewErrorMessages((prev) => ({
          ...prev,
          [id]: 'Вы слишком часто делаете запросы. Пожалуйста, подождите минуту.'
        }));
      } else if (error instanceof AxiosError && error.response) {
        setPreviewErrorMessages((prev) => ({
          ...prev,
          [id]: `Ошибка: ${error.response.data.detail || error.message}`
        }));
      } 
      else {
        setPreviewErrorMessages((prev) => ({
          ...prev,
          [id]: 'Произошла неизвестная ошибка при генерации превью.'
        }));
      }
    }
  };

  return (
    <div className="p-4 max-w-2xl mx-auto">
      <h2 className="text-xl font-bold mb-4">AI-промты для профиля #{profileId}</h2>

      <div className="space-y-2 mb-6">
        <input
          type="text"
          placeholder="Название"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full border p-2 rounded"
        />
        <textarea
          placeholder="Текст промта"
          value={promptText}
          onChange={(e) => setPromptText(e.target.value)}
          rows={4}
          className="w-full border p-2 rounded"
        />
        <button
          onClick={handleSave}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          {editingId ? 'Сохранить изменения' : 'Добавить промт'}
        </button>
      </div>

      <ul className="space-y-6">
        {prompts.map((prompt) => (
          <li
            key={prompt.id}
            className={`border p-4 rounded shadow-sm ${prompt.is_active ? 'border-green-500' : ''}`}
          >
            <div className="font-semibold flex items-center justify-between">
              {prompt.name}
              {prompt.is_active && <span className="text-green-600 text-sm ml-2">[активный]</span>}
            </div>
            <div className="text-sm text-gray-700 whitespace-pre-line mb-2">{prompt.prompt_text}</div>

            <textarea
              placeholder="Введите описание джобы для теста"
              value={previewInputs[prompt.id] || ''}
              onChange={(e) =>
                setPreviewInputs((prev) => ({ ...prev, [prompt.id]: e.target.value }))
              }
              rows={3}
              className="w-full border rounded p-2 text-sm"
            />
            <button
              onClick={() => handlePreview(prompt.id, previewInputs[prompt.id] || '')}
              className="mt-1 text-purple-600 hover:underline text-sm"
            >
              Сгенерировать по описанию
            </button>

            {previewResults[prompt.id] && (
              <div className="mt-2 p-2 bg-gray-100 text-sm rounded border">
                <strong>Предпросмотр:</strong>
                <p>{previewResults[prompt.id]}</p>
              </div>
            )}
            {previewErrorMessages[prompt.id] && (
              <p className="text-sm text-red-500 mt-1">
                {previewErrorMessages[prompt.id]}
              </p>
            )}

            <div className="mt-3 flex gap-3 flex-wrap">
              <button
                onClick={() => handleEdit(prompt)}
                className="text-blue-600 hover:underline text-sm"
              >
                Редактировать
              </button>
              <button
                onClick={() => handleDelete(prompt.id)}
                className="text-red-600 hover:underline text-sm"
              >
                Удалить
              </button>
              {!prompt.is_active && (
                <button
                  onClick={() => setActivePrompt(prompt.id)}
                  className="text-green-600 hover:underline text-sm"
                >
                  Сделать активным
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default AIPrompts;

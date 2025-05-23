import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';

type AIPrompt = {
  id: number;
  name: string;
  prompt_text: string;
  profile_id: number;
  is_active: boolean;
};

const AIPrompts: React.FC = () => {
  const { profileId } = useParams();
  const [prompts, setPrompts] = useState<AIPrompt[]>([]);
  const [name, setName] = useState('');
  const [promptText, setPromptText] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [previewInputs, setPreviewInputs] = useState<Record<number, string>>({});
  const [previewResults, setPreviewResults] = useState<Record<number, string>>({});

  const fetchPrompts = async () => {
    if (!profileId) return;
    const res = await axios.get(`/prompts/profile/${profileId}`);
    setPrompts(res.data);
  };

  useEffect(() => {
    fetchPrompts();
  }, [profileId]);

  const handleSave = async () => {
    if (!name || !promptText || !profileId) return;

    if (editingId) {
      await axios.put(`/prompts/${editingId}`, { name, prompt_text: promptText });
    } else {
      await axios.post(`/prompts/`, {
        name,
        prompt_text: promptText,
        profile_id: parseInt(profileId),
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
    setEditingId(prompt.id);
  };

  const handleDelete = async (id: number) => {
    await axios.delete(`/prompts/${id}`);
    fetchPrompts();
  };

  const setActivePrompt = async (id: number) => {
    await axios.post(`/prompts/${id}/set-active`);
    fetchPrompts();
  };

  const handlePreview = async (id: number, description: string) => {
    const res = await axios.post(`/prompts/${id}/preview`, { description });
    setPreviewResults((prev) => ({ ...prev, [id]: res.data.preview }));
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

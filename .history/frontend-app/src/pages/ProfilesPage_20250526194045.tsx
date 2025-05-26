import { useEffect, useState } from "react";
import api from '../lib/axios'; // Standardized Axios import
import Navbar from "../components/Navbar";

// 1. Define Profile TypeScript Type
type Profile = {
  id: string;
  name: string;
  profile_type: "personal" | "agency";
  autobid_enabled: boolean;
  user_id: string;
};

const ProfilePage = () => {
  // 2. Update State Types
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [name, setName] = useState("");
  const [profileType, setProfileType] = useState<"personal" | "agency">("personal"); // Renamed state, added type
  const [error, setError] = useState<string | null>(null); // Added error state

  // 5. Remove Unused token Variable (token is handled by interceptor in api instance)
  // const token = localStorage.getItem("token"); 

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    setError(null); // Clear previous errors
    try {
      // 3. Standardize Axios Usage & API Calls
      const res = await api.get<Profile[]>("/profiles/me"); // Use api instance, generic type for response
      setProfiles(res.data);
    } catch (err) {
      console.error("Ошибка загрузки профилей:", err);
      setError("Ошибка загрузки профилей. Пожалуйста, попробуйте позже.");
    }
  };

  const handleCreate = async () => {
    setError(null); // Clear previous errors
    if (!name.trim()) {
      setError("Название профиля не может быть пустым.");
      return;
    }
    try {
      // 3. Standardize Axios Usage & API Calls
      await api.post("/profiles", { name, profile_type: profileType }); // Use api instance and renamed state
      setName(""); // Clear input field
      setProfileType("personal"); // Reset select
      fetchProfiles(); // Refresh profiles list
      setError(null); // Clear error on success
    } catch (err) {
      console.error("Ошибка создания профиля:", err);
      setError("Ошибка создания профиля. Пожалуйста, попробуйте снова.");
    }
  };

  const handleDelete = async (id: string) => {
    setError(null); // Clear previous errors
    try {
      // 3. Standardize Axios Usage & API Calls
      await api.delete(`/profiles/${id}`); // Use api instance
      fetchProfiles(); // Refresh profiles list
      setError(null); // Clear error on success
    } catch (err) {
      console.error("Ошибка удаления профиля:", err);
      setError("Ошибка удаления профиля. Пожалуйста, попробуйте снова.");
    }
  };

  return (
    <>
      <Navbar />
      <div className="max-w-xl mx-auto mt-10 bg-white p-6 shadow rounded">
        <h2 className="text-xl font-bold mb-4">Ваши профили</h2>

        {/* 4. Update JSX: Display error message */}
        {error && <div className="text-red-500 mb-4 p-2 border border-red-300 rounded">{error}</div>}

        <ul className="mb-6">
          {/* 4. Update JSX: Explicitly type p and use p.profile_type */}
          {profiles.map((p: Profile) => (
            <li key={p.id} className="flex justify-between items-center mb-2 p-2 hover:bg-gray-50 rounded">
              <div>
                <strong>{p.name}</strong> ({p.profile_type})
                {p.autobid_enabled && <span className="ml-2 text-xs text-green-600 bg-green-100 px-2 py-0.5 rounded-full">Autobid ON</span>}
              </div>
              <button
                className="text-red-500 hover:text-red-700 font-medium text-sm"
                onClick={() => handleDelete(p.id)}
              >
                🗑 Удалить
              </button>
            </li>
          ))}
        </ul>

        <div className="border-t pt-4">
          <h3 className="text-md font-semibold mb-2">Добавить профиль</h3>
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              placeholder="Название"
              className="border px-3 py-2 rounded shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 flex-grow"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            {/* 4. Update JSX: Use profileType state */}
            <select
              value={profileType}
              onChange={(e) => setProfileType(e.target.value as "personal" | "agency")}
              className="border px-3 py-2 rounded shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="personal">Personal</option>
              <option value="agency">Agency</option>
            </select>
            <button
              onClick={handleCreate}
              className="bg-blue-600 text-white px-4 py-2 rounded shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
            >
              Создать
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default ProfilePage;

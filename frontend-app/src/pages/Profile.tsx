import { useEffect, useState } from "react";
import axios from "axios";
import Navbar from "../components/Navbar";

const ProfilePage = () => {
  const [profiles, setProfiles] = useState([]);
  const [name, setName] = useState("");
  const [type, setType] = useState("personal");

  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    try {
      const res = await axios.get("http://localhost:8000/profiles/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setProfiles(res.data);
    } catch (err) {
      console.error("Ошибка загрузки профилей");
    }
  };

  const handleCreate = async () => {
    try {
      await axios.post(
        "http://localhost:8000/profiles",
        { name, type },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setName("");
      fetchProfiles();
    } catch (err) {
      alert("Ошибка создания профиля");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await axios.delete(`http://localhost:8000/profiles/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchProfiles();
    } catch (err) {
      alert("Ошибка удаления профиля");
    }
  };

  return (
    <>
      <Navbar />
      <div className="max-w-xl mx-auto mt-10 bg-white p-6 shadow rounded">
        <h2 className="text-xl font-bold mb-4">Ваши профили</h2>

        <ul className="mb-6">
          {profiles.map((p: any) => (
            <li key={p.id} className="flex justify-between items-center mb-2">
              <div>
                <strong>{p.name}</strong> ({p.type})
              </div>
              <button
                className="text-red-500 hover:text-red-700"
                onClick={() => handleDelete(p.id)}
              >
                🗑 Удалить
              </button>
            </li>
          ))}
        </ul>

        <div className="border-t pt-4">
          <h3 className="text-md font-semibold mb-2">Добавить профиль</h3>
          <input
            type="text"
            placeholder="Название"
            className="border px-2 py-1 mr-2"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="border px-2 py-1 mr-2"
          >
            <option value="personal">Personal</option>
            <option value="agency">Agency</option>
          </select>
          <button
            onClick={handleCreate}
            className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
          >
            Создать
          </button>
        </div>
      </div>
    </>
  );
};

export default ProfilePage;

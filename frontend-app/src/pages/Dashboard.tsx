import { useEffect, useState } from "react";
import axios from "axios";
// import Navbar from "../components/Navbar"; // временно отключено

const Dashboard = () => {
  const [user, setUser] = useState<any | undefined>(undefined); // undefined = loading

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      setUser(null); // нет токена — неавторизован
      return;
    }

    axios
      .get(`${import.meta.env.VITE_API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      .then((res) => {
        console.log("✅ /auth/me response:", res.data);
        setUser(res.data);
      })
      .catch((err) => {
        console.error("❌ /auth/me error:", err);
        localStorage.removeItem("token");
        setUser(null);
      });
  }, []);

  const handleLogout = () => {
    const token = localStorage.getItem("token");
    axios.post(`${import.meta.env.VITE_API_BASE_URL}/auth/logout`, {}, {
      headers: { Authorization: `Bearer ${token}` },
    });
    localStorage.removeItem("token");
    window.location.href = "/signin";
  };

  if (user === undefined) {
    return (
      <div className="flex justify-center items-center h-screen text-gray-700">
        Загрузка...
      </div>
    );
  }

  if (user === null) {
    window.location.href = "/signin";
    return null;
  }

  return (
    <>
      {/* <Navbar /> */}
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-8 rounded shadow-md text-center w-full max-w-md">
          <h2 className="text-2xl font-bold mb-4">Добро пожаловать!</h2>
          <p className="mb-6">
            Вы вошли как <strong>{user.email}</strong>
          </p>
          <p className="mb-6">
            Роль: <strong>{user.role}</strong>
          </p>
          <button
            onClick={handleLogout}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
          >
            Выйти
          </button>
        </div>
      </div>
    </>
  );
};

export default Dashboard;

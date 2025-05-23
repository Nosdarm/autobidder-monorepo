import { useEffect, useState } from "react";
import axios from "axios";
import Navbar from "../components/Navbar";

const Dashboard = () => {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    axios
      .get("http://localhost:8000/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      .then((res) => setUser(res.data))
      .catch(() => setUser(null));
  }, []);

  if (!user) return <p>Загрузка или неавторизован...</p>;

  return (
    <>
      <Navbar />
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-8 rounded shadow-md text-center w-full max-w-md">
          <h2 className="text-2xl font-bold mb-4">
            Добро пожаловать, {user.email}!
          </h2>
          <p className="mb-4">Ваша роль: <strong>{user.role}</strong></p>
        </div>
      </div>
    </>
  );
};

export default Dashboard;

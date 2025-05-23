import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

const Navbar = () => {
  const [user, setUser] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    axios
      .get("http://localhost:8000/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => setUser(res.data))
      .catch(() => setUser(null));
  }, []);

  const handleLogout = () => {
    const token = localStorage.getItem("token");
    axios.post("http://localhost:8000/auth/logout", {}, {
      headers: { Authorization: `Bearer ${token}` },
    });
    localStorage.removeItem("token");
    navigate("/signin");
  };

  return (
    <nav className="bg-gray-800 text-white px-6 py-4 flex justify-between items-center">
      <div className="text-xl font-semibold">
        <Link to="/dashboard">Autobidder</Link>
      </div>
      <div className="flex items-center space-x-6">
        <Link to="/dashboard" className="hover:underline">
          Главная
        </Link>
        <Link to="/profile" className="hover:underline">
          Профили
        </Link>
        {user && (
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-300">{user.email}</span>
            <button
              onClick={handleLogout}
              className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded"
            >
              Выйти
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;

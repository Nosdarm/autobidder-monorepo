import { useEffect, useState } from "react";
import api from '../lib/axios'; // Updated axios import
import { useNavigate } from 'react-router-dom'; // Import useNavigate
import Navbar from "../components/Navbar"; // Uncommented Navbar

const Dashboard = () => {
  const [user, setUser] = useState<any | undefined>(undefined); // undefined = loading
  const [error, setError] = useState<string | null>(null); // Added error state
  const navigate = useNavigate(); // Initialize useNavigate

  useEffect(() => {
    const token = localStorage.getItem("token"); // Token check is still useful before API call

    if (!token) {
      setUser(null); 
      navigate("/signin"); // Navigate if no token
      return;
    }
    
    setError(null); // Clear previous errors
    // Assuming api instance in lib/axios.ts has an interceptor for the token
    api.get("/auth/me") 
      .then((res) => {
        console.log("✅ /auth/me response:", res.data);
        setUser(res.data);
      })
      .catch((err) => {
        console.error("❌ /auth/me error:", err);
        localStorage.removeItem("token");
        setUser(null);
        setError("Сессия истекла или недействительна. Пожалуйста, войдите снова.");
        navigate("/signin"); // Navigate on error
      });
  }, [navigate]);

  const handleLogout = async () => { // Made async
    // Token should be handled by interceptor in api instance
    try {
      await api.post("/auth/logout", {});
    } catch (err) {
      console.error("Logout API call failed:", err);
      // Proceed with local logout even if API fails
    }
    localStorage.removeItem("token");
    setUser(null); // Clear user state
    navigate("/signin"); // Use navigate
  };

  if (user === undefined) {
    return (
      <div className="flex justify-center items-center h-screen text-gray-700">
        Загрузка...
      </div>
    );
  }

  // This check might be redundant if useEffect navigates on null user,
  // but kept for safety if navigate hasn't completed.
  if (user === null && !error) { 
    // If no user and no error being displayed, it implies initial navigation hasn't run
    // or we are in a redirect loop. This check should ideally be handled by PrivateRoute.
    // For now, if user becomes null and there's no explicit error message being shown,
    // it likely means the useEffect hook already called navigate.
    // To avoid rendering briefly before navigation, we can return null or a loader.
    return null; 
  }

  return (
    <>
      <Navbar /> {/* Uncommented Navbar */}
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-8 rounded shadow-md text-center w-full max-w-md">
          {error && <div className="text-red-500 mb-4 p-2 border border-red-300 rounded">{error}</div>}
          <h2 className="text-2xl font-bold mb-4">Добро пожаловать!</h2>
          {user && ( // Only show user info if user is not null
            <>
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
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default Dashboard;

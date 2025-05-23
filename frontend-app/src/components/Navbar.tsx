import { useEffect, useState, useRef } from "react"; // Added useRef
import { Link, useNavigate } from "react-router-dom";
import api from '../lib/axios'; 

// 2. Define User Type More Specifically
type User = {
  id: number; // As per backend UserOut schema which seems to use int for user.id
  email: string;
  role?: string;
  is_verified?: boolean;
};

const Navbar = () => {
  const [user, setUser] = useState<User | null | undefined>(undefined); // undefined for initial loading state
  const navigate = useNavigate();
  const socketRef = useRef<WebSocket | null>(null); // For managing WebSocket instance

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setUser(null); // No token, so not authenticated
      return;
    }

    api.get("/auth/me") 
      .then((res) => setUser(res.data as User)) // Cast to User
      .catch(() => {
        setUser(null);
        localStorage.removeItem("token"); 
      });
  }, []);

  // 1. Add WebSocket Logic within useEffect
  useEffect(() => {
    if (user && user.id) {
      // 3. Handle VITE_API_URL for WebSocket
      let wsBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000');
      try {
        const urlObj = new URL(wsBaseUrl);
        // Ensure ws or wss protocol based on http or https
        const protocol = urlObj.protocol === 'https:' ? 'wss:' : 'ws:';
        wsBaseUrl = `${protocol}//${urlObj.host}`;
      } catch (e) { 
        // Fallback if VITE_API_URL is not a full URL (e.g. only /api/v1)
        // or if it's an invalid URL.
        const currentProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        wsBaseUrl = `${currentProtocol}//${window.location.host}`; 
        console.warn(
            "VITE_API_URL ('", import.meta.env.VITE_API_URL, 
            "') is not a full URL or is invalid. Defaulting WebSocket base to window location: ", 
            wsBaseUrl, e
        );
      }
      const wsUrl = `${wsBaseUrl}/ws/status/${user.id}`;
      
      console.log(`Attempting to connect WebSocket: ${wsUrl}`);
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log(`WebSocket connected for user ${user.id}`);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data as string);
          console.log("WebSocket message received:", data);
          if (data.type === "bid_update") {
            alert(
              `Bid ${data.bid_id} status: ${data.status} for job: ${data.job_id || 'N/A'}`
            );
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      socket.onclose = (event) => {
        console.log("WebSocket disconnected:", event.code, event.reason);
      };

      return () => {
        console.log("Cleaning up WebSocket connection for user", user.id);
        if (socketRef.current && 
            (socketRef.current.readyState === WebSocket.OPEN || 
             socketRef.current.readyState === WebSocket.CONNECTING)) {
          socketRef.current.close();
        }
        socketRef.current = null;
      };
    } else {
      // If no user or user.id, ensure any existing socket is closed
      if (socketRef.current && 
          (socketRef.current.readyState === WebSocket.OPEN || 
           socketRef.current.readyState === WebSocket.CONNECTING)) {
        console.log("User logged out or changed, closing WebSocket.");
        socketRef.current.close();
      }
      socketRef.current = null;
    }
  }, [user]); // Dependency on user state

  const handleLogout = async () => {
    try {
      await api.post("/auth/logout", {}); // Empty object for body if not needed
    } catch (error) {
      console.error("Logout failed:", error);
      // Even if logout API call fails, proceed to clear local token and redirect
    }
    localStorage.removeItem("token");
    setUser(null); // Clear user state
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

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from './lib/axios'; // Adjusted path for api import

interface Props {
  children: React.ReactNode;
}

const PrivateRoute = ({ children }: Props) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      setIsAuthenticated(false);
      navigate("/signin");
      return;
    }

    // Assuming api instance in lib/axios.ts has an interceptor for the token
    api.get("/auth/me")
      .then((res) => {
        // If /auth/me returns user data upon successful authentication
        if (res.data) { // Check if response data exists
          setIsAuthenticated(true);
        } else { // Should not happen if API is consistent, but good for robustness
          throw new Error("Authentication check failed, no user data returned.");
        }
      })
      .catch(() => {
        localStorage.removeItem("token");
        navigate("/signin");
        setIsAuthenticated(false);
      });
  }, [navigate]);

  if (isAuthenticated === null) return null; // можно добавить спиннер

  return <>{children}</>;
};

export default PrivateRoute;

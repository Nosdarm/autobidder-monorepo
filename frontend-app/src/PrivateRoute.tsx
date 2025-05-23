import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

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

    fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error();
      })
      .then(() => setIsAuthenticated(true))
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

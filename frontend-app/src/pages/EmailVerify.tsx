import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import axios from "axios";

const EmailVerify = () => {
  const [message, setMessage] = useState("Проверяем токен...");
  const [success, setSuccess] = useState(false);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setMessage("Токен не найден");
      return;
    }

    axios
      .get(`http://localhost:8000/auth/verify-email?token=${token}`)
      .then((res) => {
        setSuccess(true);
        setMessage(res.data.message);

        // Автоматический вход после подтверждения (опционально)
        if (res.data.token) {
          localStorage.setItem("token", res.data.token);
        }

        setTimeout(() => navigate("/dashboard"), 2000);
      })
      .catch((err) => {
        setSuccess(false);
        setMessage(
          err.response?.data?.detail || "Ошибка подтверждения токена"
        );
      });
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div
        className={`bg-white p-6 rounded shadow-md text-center w-full max-w-md ${
          success ? "text-green-600" : "text-red-600"
        }`}
      >
        <h2 className="text-xl font-semibold mb-4">Подтверждение Email</h2>
        <p>{message}</p>
      </div>
    </div>
  );
};

export default EmailVerify;

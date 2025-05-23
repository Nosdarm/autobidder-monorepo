import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import api from '../lib/axios'; // Updated axios import
import { AxiosError } from 'axios'; // For type checking

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

    // Backend endpoint is /auth/verify (not /auth/verify-email)
    api.get(`/auth/verify?token=${token}`) 
      .then((res) => {
        setSuccess(true);
        setMessage(res.data.message || "Email успешно подтвержден!"); // Use message from response or a default

        // Backend /auth/verify currently doesn't return a new token for auto-login.
        // If it did, this logic would be fine.
        // if (res.data.access_token) { 
        //   localStorage.setItem("token", res.data.access_token);
        // }

        setTimeout(() => navigate("/dashboard"), 3000); // Slightly longer timeout
      })
      .catch((err) => {
        console.error("Email verification error:", err); // Log the full error
        setSuccess(false);
        if (err instanceof AxiosError && err.response) {
          setMessage(err.response.data.detail || "Ошибка подтверждения токена. Возможно, ссылка недействительна или срок ее действия истек.");
        } else {
          setMessage("Произошла неизвестная ошибка при подтверждении email.");
        }
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

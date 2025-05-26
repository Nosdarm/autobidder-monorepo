import { useState } from "react";
import api from '../../lib/axios'; // Updated axios import
import { AxiosError } from 'axios'; // For type checking

const SignUp = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState(""); // Added error state
  const [loading, setLoading] = useState(false);

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    setError(""); // Clear previous errors

    if (password !== confirm) {
      alert("Пароли не совпадают");
      setLoading(false);
      return;
    }

    try {
      const res = await api.post("/auth/register", { // Use api and relative path
        email,
        password,
      });

      setMessage("Регистрация успешна. Проверьте вашу почту для верификации."); // Updated message
      setEmail("");
      setPassword("");
      setConfirm("");

      // Removed automatic opening of verify_link as it's better user experience
      // to inform them to check their email.
      // if (res.data.verify_link) { 
      //   window.open(res.data.verify_link, "_blank");
      // }
    } catch (err: any) {
      if (err instanceof AxiosError && err.response) {
        setError(err.response.data.detail || "Ошибка регистрации");
      } else {
        setError("Ошибка регистрации. Попробуйте снова.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">Регистрация</h2>
        <form onSubmit={handleSignUp} className="space-y-4">
          <input
            type="email"
            placeholder="Эл. почта"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            maxLength={100}
            className="w-full border px-4 py-2 rounded"
          />
          <input
            type="password"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            maxLength={100}
            className="w-full border px-4 py-2 rounded"
          />
          <input
            type="password"
            placeholder="Повторите пароль"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
            minLength={6}
            maxLength={100}
            className="w-full border px-4 py-2 rounded"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
          >
            {loading ? "Загрузка..." : "Зарегистрироваться"}
          </button>
        </form>
        {message && <p className="mt-4 text-center text-green-600">{message}</p>}
        {error && <p className="mt-4 text-center text-red-600">{error}</p>} 
      </div>
    </div>
  );
};

export default SignUp;

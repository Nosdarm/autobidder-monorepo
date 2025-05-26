import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
// import { Button } from '@/components/ui/button'; // Assuming shadcn/ui
// import { Input } from '@/components/ui/input';
// import { Label } from '@/components/ui/label';
// import { useToast } from '@/components/ui/use-toast'; // Assuming shadcn/ui toast
import { useAuth } from '@/contexts/AuthContext'; // Conceptual path

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth(); // Conceptual hook
  const navigate = useNavigate();
  // const { toast } = useToast(); // Conceptual shadcn/ui toast

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login({ email, password });
      // toast({ title: 'Success', description: 'Logged in successfully!' });
      alert('Logged in successfully! (Conceptual Toast)');
      navigate('/dashboard'); // Navigate to a protected route
    } catch (error: any) {
      // toast({ variant: "destructive", title: 'Error', description: error.message || 'Login failed. Please check your credentials.' });
      alert(`Login failed: ${error?.message || 'Please check your credentials.'} (Conceptual Toast)`);
      console.error("Login error", error);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '50px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2>Login</h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        <div>
          <label htmlFor="email" style={{ display: 'block', marginBottom: '5px' }}>Email (Conceptual Label)</label>
          <input 
            type="email" 
            id="email" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            required 
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
            placeholder="you@example.com"
          />
        </div>
        <div>
          <label htmlFor="password" style={{ display: 'block', marginBottom: '5px' }}>Password (Conceptual Label)</label>
          <input 
            type="password" 
            id="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            required 
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
            placeholder="Your password"
          />
        </div>
        <button type="submit" style={{ padding: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Login (Conceptual Button)
        </button>
      </form>
      <p style={{ marginTop: '15px', textAlign: 'center' }}>
        Don't have an account? <Link to="/register" style={{ color: '#007bff' }}>Register</Link>
      </p>
      <p style={{ marginTop: '10px', textAlign: 'center' }}>
        <Link to="/forgot-password" style={{ color: '#007bff' }}>Forgot Password?</Link>
      </p>
    </div>
  );
}

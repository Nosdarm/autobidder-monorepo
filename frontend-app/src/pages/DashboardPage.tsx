import React from 'react';
import { useAuth } from '@/components/contexts/AuthContext';

export default function DashboardPage() {
  const { user, logoutContext } = useAuth();

  return (
    <div style={{ padding: '20px' }}>
      <h2>Dashboard</h2>
      {user && <p>Welcome, {user.name || user.email}!</p>}
      <p>This is a protected page.</p>
      <button 
        onClick={logoutContext} 
        style={{ marginTop: '20px', padding: '10px', backgroundColor: 'tomato', color: 'white', border: 'none', borderRadius: '4px' }}
      >
        Logout (Conceptual Button)
      </button>
    </div>
  );
}

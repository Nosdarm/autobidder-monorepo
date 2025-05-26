import React from 'react';
import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>Welcome to the Autobidder Application</h1>
      <p>This is the public home page.</p>
      <nav style={{ marginTop: '20px' }}>
        <Link to="/login" style={{ marginRight: '10px', color: '#007bff' }}>Login</Link>
        <Link to="/register" style={{ color: '#007bff' }}>Register</Link>
        <br />
        <Link to="/dashboard" style={{ marginTop: '10px', display: 'inline-block', color: '#28a745' }}>Go to Dashboard (Protected)</Link>
      </nav>
    </div>
  );
}

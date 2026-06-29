import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/dashboard" element={<App />} />
        <Route path="/customers" element={<App />} />
        <Route path="/customer/:customer_id" element={<App />} />
        <Route path="/history" element={<App />} />
        <Route path="/analytics" element={<App />} />
        <Route path="/analysis" element={<App />} />
        <Route path="/analysis-results" element={<App />} />
        {/* Catch-all: redirect unknown paths to App (shows dashboard) */}
        <Route path="*" element={<App />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);

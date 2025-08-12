import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { ApiErrorBoundary } from './hooks/useApiClient';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ApiErrorBoundary>
      <App />
    </ApiErrorBoundary>
  </React.StrictMode>
);

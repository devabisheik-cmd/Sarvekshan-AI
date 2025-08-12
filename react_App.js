import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { store } from './store/store';
import { initializeRealTimeConnection } from './hooks/useWebSocket';

// Components
import Dashboard from './components/Dashboard/Dashboard';
import SurveyBuilder from './components/Survey/SurveyBuilder';
import SurveyForm from './components/Survey/SurveyForm';
import DataProcessing from './components/Processing/DataProcessing';
import QueryInterface from './components/Query/QueryInterface';
import Login from './components/Auth/Login';
import ProtectedRoute from './components/Auth/ProtectedRoute';

// Theme configuration
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  React.useEffect(() => {
    // Initialize WebSocket connection for real-time updates
    initializeRealTimeConnection();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <Provider store={store}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Router>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />
              <Route path="/survey/create" element={
                <ProtectedRoute>
                  <SurveyBuilder />
                </ProtectedRoute>
              } />
              <Route path="/survey/:id" element={
                <ProtectedRoute>
                  <SurveyForm />
                </ProtectedRoute>
              } />
              <Route path="/processing" element={
                <ProtectedRoute>
                  <DataProcessing />
                </ProtectedRoute>
              } />
              <Route path="/query" element={
                <ProtectedRoute>
                  <QueryInterface />
                </ProtectedRoute>
              } />
            </Routes>
          </Router>
        </ThemeProvider>
      </Provider>
    </QueryClientProvider>
  );
}

export default App;

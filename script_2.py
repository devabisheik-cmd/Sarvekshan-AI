# Create core React application files

# Main React App.js
react_app_js = '''import React from 'react';
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
'''

# React index.js
react_index_js = '''import React from 'react';
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
'''

# Redux store configuration
redux_store_js = '''import { configureStore } from '@reduxjs/toolkit';
import authSlice from './slices/authSlice';
import surveySlice from './slices/surveySlice';
import processingSlice from './slices/processingSlice';
import querySlice from './slices/querySlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    survey: surveySlice,
    processing: processingSlice,
    query: querySlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
'''

# Auth slice
auth_slice_js = '''import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface User {
  id: string;
  username: string;
  role: 'enumerator' | 'analyst' | 'admin';
  permissions: string[];
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const initialState: AuthState = {
  user: null,
  accessToken: localStorage.getItem('accessToken'),
  refreshToken: localStorage.getItem('refreshToken'),
  isAuthenticated: false,
  isLoading: false,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.isLoading = true;
    },
    loginSuccess: (state, action: PayloadAction<{user: User; accessToken: string; refreshToken: string}>) => {
      state.user = action.payload.user;
      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken;
      state.isAuthenticated = true;
      state.isLoading = false;
      
      // Store tokens in localStorage
      localStorage.setItem('accessToken', action.payload.accessToken);
      localStorage.setItem('refreshToken', action.payload.refreshToken);
    },
    loginFailure: (state) => {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.isLoading = false;
    },
    logout: (state) => {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.isLoading = false;
      
      // Clear tokens from localStorage
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    },
    updateAccessToken: (state, action: PayloadAction<string>) => {
      state.accessToken = action.payload;
      localStorage.setItem('accessToken', action.payload);
    },
  },
});

export const { loginStart, loginSuccess, loginFailure, logout, updateAccessToken } = authSlice.actions;
export default authSlice.reducer;
'''

# HTML template
html_template = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Sarvekshan-AI - Intelligent Platform for Automated Survey Data Management" />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <title>Sarvekshan-AI</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
'''

# PWA manifest
pwa_manifest = '''{
  "short_name": "Sarvekshan-AI",
  "name": "Sarvekshan-AI Survey Platform",
  "icons": [
    {
      "src": "favicon.ico",
      "sizes": "64x64 32x32 24x24 16x16",
      "type": "image/x-icon"
    }
  ],
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#ffffff"
}'''

# CSS styles
css_styles = '''body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

/* Sarvekshan-AI specific styles */
.sarvekshan-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.survey-form {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 24px;
  margin: 16px 0;
}

.processing-dashboard {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.query-interface {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 24px;
}

/* Real-time indicators */
.online-indicator {
  width: 8px;
  height: 8px;
  background-color: #4caf50;
  border-radius: 50%;
  display: inline-block;
  margin-right: 8px;
}

.offline-indicator {
  width: 8px;
  height: 8px;
  background-color: #f44336;
  border-radius: 50%;
  display: inline-block;
  margin-right: 8px;
}
'''

# Save React files
react_files = [
    ("react_App.js", react_app_js),
    ("react_index.js", react_index_js),
    ("redux_store.js", redux_store_js),
    ("auth_slice.js", auth_slice_js),
    ("public_index.html", html_template),
    ("public_manifest.json", pwa_manifest),
    ("src_index.css", css_styles)
]

print("🔨 CREATING REACT APPLICATION FILES")
print("=" * 45)

for filename, content in react_files:
    with open(f"{filename}", "w") as f:
        f.write(content)
    print(f"✅ Created: {filename}")

print(f"\n📦 REACT APPLICATION FILES COMPLETE")
print(f"🎯 Frontend React components ready")
print(f"🔄 Redux state management configured")
print(f"📱 Progressive Web App (PWA) enabled")
/**
 * Main App component.
 * See .ai/architecture.md: React structure.
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

// Pages
import Login from './pages/login/Login';
import Register from './pages/register/Register';
import Dashboard from './pages/dashboard/Dashboard';
import TeamsList from './pages/teams/TeamsList';
import TeamDetail from './pages/teams/TeamDetail';
import ProjectsList from './pages/projects/ProjectsList';
import ProjectDetail from './pages/projects/ProjectDetail';
import TasksList from './pages/tasks/TasksList';
import TaskDetail from './pages/tasks/TaskDetail';
import TaskCreate from './pages/tasks/TaskCreate';
import WorkloadDashboard from './pages/analytics/WorkloadDashboard';
import RiskDashboard from './pages/analytics/RiskDashboard';
import RecommendationsList from './pages/recommendations/RecommendationsList';
import RecommendationDetail from './pages/recommendations/RecommendationDetail';
import NotificationsPage from './pages/notifications/NotificationsPage';
import ChatPage from './pages/chat/ChatPage';

/**
 * Wrap a page in the shared AppLayout (navbar + NotificationBell).
 * All authenticated routes go through this so the bell is always visible.
 */
function WithLayout({ children }) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Authenticated — all wrapped in AppLayout for shared navbar + bell */}
      <Route path="/" element={<WithLayout><Dashboard /></WithLayout>} />

      <Route path="/teams" element={<WithLayout><TeamsList /></WithLayout>} />
      <Route path="/teams/:id" element={<WithLayout><TeamDetail /></WithLayout>} />

      <Route path="/projects" element={<WithLayout><ProjectsList /></WithLayout>} />
      <Route path="/projects/:id" element={<WithLayout><ProjectDetail /></WithLayout>} />
      <Route path="/projects/:projectId/tasks/create" element={<WithLayout><TaskCreate /></WithLayout>} />

      <Route path="/tasks" element={<WithLayout><TasksList /></WithLayout>} />
      <Route path="/tasks/:id" element={<WithLayout><TaskDetail /></WithLayout>} />

      <Route path="/analytics/workload" element={<WithLayout><WorkloadDashboard /></WithLayout>} />
      <Route path="/analytics/risk/:projectId" element={<WithLayout><RiskDashboard /></WithLayout>} />

      <Route path="/recommendations" element={<WithLayout><RecommendationsList /></WithLayout>} />
      <Route path="/recommendations/:id" element={<WithLayout><RecommendationDetail /></WithLayout>} />

      <Route path="/notifications" element={<WithLayout><NotificationsPage /></WithLayout>} />

      {/* Chat has its own full-screen layout — still needs ProtectedRoute but no AppLayout
          so the sidebar + composer don't fight with the outer nav chrome */}
      <Route path="/chat" element={
        <ProtectedRoute><ChatPage /></ProtectedRoute>
      } />

      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;

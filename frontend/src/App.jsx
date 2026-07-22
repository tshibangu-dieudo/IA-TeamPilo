/**
 * Main App component.
 * See .ai/architecture.md: React structure.
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import Login from './pages/login/Login';
import Register from './pages/register/Register';
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

// Placeholder pages - will be implemented in later sprints
const Dashboard = () => <div>Dashboard - Coming Soon</div>;


function AppRoutes() {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      } />
      <Route path="/teams" element={
        <ProtectedRoute>
          <TeamsList />
        </ProtectedRoute>
      } />
      <Route path="/teams/:id" element={
        <ProtectedRoute>
          <TeamDetail />
        </ProtectedRoute>
      } />
      <Route path="/projects" element={
        <ProtectedRoute>
          <ProjectsList />
        </ProtectedRoute>
      } />
      <Route path="/projects/:id" element={
        <ProtectedRoute>
          <ProjectDetail />
        </ProtectedRoute>
      } />
      <Route path="/projects/:projectId/tasks/create" element={
        <ProtectedRoute>
          <TaskCreate />
        </ProtectedRoute>
      } />
      <Route path="/tasks" element={
        <ProtectedRoute>
          <TasksList />
        </ProtectedRoute>
      } />
      <Route path="/tasks/:id" element={
        <ProtectedRoute>
          <TaskDetail />
        </ProtectedRoute>
      } />
      <Route path="/analytics/workload" element={
        <ProtectedRoute>
          <WorkloadDashboard />
        </ProtectedRoute>
      } />
      <Route path="/analytics/risk/:projectId" element={
        <ProtectedRoute>
          <RiskDashboard />
        </ProtectedRoute>
      } />
      <Route path="/recommendations" element={
        <ProtectedRoute>
          <RecommendationsList />
        </ProtectedRoute>
      } />
      <Route path="/recommendations/:id" element={
        <ProtectedRoute>
          <RecommendationDetail />
        </ProtectedRoute>
      } />
      <Route path="/notifications" element={
        <ProtectedRoute>
          <NotificationsPage />
        </ProtectedRoute>
      } />
      <Route path="/chat" element={
        <ProtectedRoute>
          <ChatPage />
        </ProtectedRoute>
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

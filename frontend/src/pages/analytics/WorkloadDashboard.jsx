/**
 * Workload Dashboard page component.
 * See .ai/architecture.md: src/pages/ - one folder per screen group.
 * See .ai/coding-rules.md: Tailwind utility classes only.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../../auth/AuthContext';
import { analyticsAPI } from '../../api/analytics';

export default function WorkloadDashboard() {
  const { user } = useAuth();
  const [workload, setWorkload] = useState(null);
  const [teamWorkload, setTeamWorkload] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [view, setView] = useState('individual'); // individual, team

  useEffect(() => {
    if (user) {
      loadWorkload();
    }
  }, [user]);

  const loadWorkload = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getWorkload(user.id);
      setWorkload(response.data);
      
      // Load team workload if user is PM or Executive
      if (user.role === 'project_manager' || user.role === 'executive_manager') {
        // Assuming user has a team_id - in production, this would come from user profile
        // For now, we'll skip team view if team_id is not available
      }
    } catch (err) {
      setError('Failed to load workload data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'underloaded': return 'bg-blue-100 text-blue-800';
      case 'balanced': return 'bg-green-100 text-green-800';
      case 'overloaded': return 'bg-orange-100 text-orange-800';
      case 'critically_overloaded': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getProgressBarColor = (percentage) => {
    if (percentage <= 60) return 'bg-blue-500';
    if (percentage <= 99) return 'bg-green-500';
    if (percentage <= 120) return 'bg-orange-500';
    return 'bg-red-500';
  };

  if (loading) return <div className="text-center py-8">Loading workload data...</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Workload Dashboard</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setView('individual')}
            className={`px-4 py-2 rounded-md ${
              view === 'individual'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            My Workload
          </button>
          {(user.role === 'project_manager' || user.role === 'executive_manager') && (
            <button
              onClick={() => setView('team')}
              className={`px-4 py-2 rounded-md ${
                view === 'team'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Team Workload
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {view === 'individual' && workload && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Your Current Workload</h2>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Workload Percentage</span>
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(workload.status)}`}>
                  {workload.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className={`h-4 rounded-full transition-all duration-300 ${getProgressBarColor(workload.workload_percentage)}`}
                  style={{ width: `${Math.min(workload.workload_percentage, 150)}%` }}
                />
              </div>
              <p className="text-right text-sm text-gray-600 mt-1">
                {workload.workload_percentage.toFixed(1)}%
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Computed At</h3>
                <p className="text-lg text-gray-900">
                  {new Date(workload.computed_at).toLocaleString()}
                </p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Status</h3>
                <p className="text-lg text-gray-900 capitalize">
                  {workload.status.replace('_', ' ')}
                </p>
              </div>
            </div>

            {workload.status === 'overloaded' || workload.status === 'critically_overloaded' ? (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <p className="text-sm text-orange-800">
                  <strong>Attention:</strong> Your workload is above recommended capacity. Consider
                  requesting task reassignment or adjusting deadlines.
                </p>
              </div>
            ) : workload.status === 'underloaded' ? (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  <strong>Note:</strong> You have available capacity. Consider taking on additional
                  tasks or helping overloaded team members.
                </p>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {view === 'team' && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Team Workload</h2>
          <p className="text-gray-500">Team workload view requires team configuration.</p>
        </div>
      )}
    </div>
  );
}

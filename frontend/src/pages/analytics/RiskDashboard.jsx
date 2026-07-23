/**
 * Risk Dashboard page component.
 * See .ai/architecture.md: src/pages/ - one folder per screen group.
 * See .ai/coding-rules.md: Tailwind utility classes only.
 */
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { analyticsAPI } from '../../api/analytics';

export default function RiskDashboard() {
  const { projectId } = useParams();
  const [riskScore, setRiskScore] = useState(null);
  const [riskHistory, setRiskHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    if (projectId) {
      loadRiskScore();
    }
  }, [projectId]);

  const loadRiskScore = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getRiskScore(projectId);
      setRiskScore(response.data);
    } catch (err) {
      setError('Failed to load risk score data');
    } finally {
      setLoading(false);
    }
    // Load history separately so a history failure doesn't mask the main score
    try {
      const historyResponse = await analyticsAPI.getRiskHistory(projectId);
      const histData = historyResponse.data;
      setRiskHistory(Array.isArray(histData) ? histData : (histData.results ?? []));
    } catch {
      // History is optional; non-fatal
    }
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'moderate': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getProgressBarColor = (score) => {
    if (score <= 29) return 'bg-green-500';
    if (score <= 59) return 'bg-yellow-500';
    if (score <= 79) return 'bg-orange-500';
    return 'bg-red-500';
  };

  if (loading) return <div className="text-center py-8">Loading risk score...</div>;

  if (!riskScore) return <div className="text-center py-8">Risk score not found</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Project Risk Dashboard</h1>
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
        >
          {showHistory ? 'Hide History' : 'Show History'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Current Risk Score</h2>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Risk Level</h3>
              <span className={`px-3 py-1 text-sm rounded-full ${getLevelColor(riskScore.level)}`}>
                {riskScore.level.toUpperCase()}
              </span>
            </div>
            <div className="text-right">
              <h3 className="text-sm font-medium text-gray-500 mb-1">Score</h3>
              <p className="text-4xl font-bold text-gray-900">{riskScore.score.toFixed(1)}%</p>
            </div>
          </div>

          <div>
            <div className="w-full bg-gray-200 rounded-full h-6">
              <div
                className={`h-6 rounded-full transition-all duration-300 ${getProgressBarColor(riskScore.score)}`}
                style={{ width: `${riskScore.score}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0%</span>
              <span>25%</span>
              <span>50%</span>
              <span>75%</span>
              <span>100%</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Project</h3>
              <p className="text-lg text-gray-900">{riskScore.project_name}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Computed At</h3>
              <p className="text-lg text-gray-900">
                {new Date(riskScore.computed_at).toLocaleString()}
              </p>
            </div>
          </div>

          {riskScore.explanation_text && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Explanation</h3>
              <p className="text-sm text-gray-600">{riskScore.explanation_text}</p>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Risk Components</h2>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">Overload Factor (35%)</span>
              <span className="text-sm text-gray-600">{riskScore.overload_factor.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{ width: `${Math.min(riskScore.overload_factor, 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">Blocked Task Factor (30%)</span>
              <span className="text-sm text-gray-600">{riskScore.blocked_task_factor.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-red-500 h-2 rounded-full"
                style={{ width: `${Math.min(riskScore.blocked_task_factor, 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">Deadline Proximity Factor (20%)</span>
              <span className="text-sm text-gray-600">{riskScore.deadline_proximity_factor.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-yellow-500 h-2 rounded-full"
                style={{ width: `${Math.min(riskScore.deadline_proximity_factor, 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">Historical Velocity Factor (15%)</span>
              <span className="text-sm text-gray-600">{riskScore.historical_velocity_factor.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full"
                style={{ width: `${Math.min(riskScore.historical_velocity_factor, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {showHistory && (
        riskHistory.length > 0 ? (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Risk Score History</h2>
          <div className="space-y-2">
            {riskHistory.map((entry) => (
              <div
                key={entry.id}
                className="flex justify-between items-center p-3 bg-gray-50 rounded"
              >
                <div className="flex items-center gap-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${getLevelColor(entry.level)}`}>
                    {entry.level.toUpperCase()}
                  </span>
                  <span className="text-gray-900">{entry.score.toFixed(1)}%</span>
                </div>
                <div className="text-sm text-gray-500">
                  {new Date(entry.computed_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
        ) : (
          <div className="bg-white shadow rounded-lg p-6 text-center">
            <p className="text-gray-500">No risk score history available yet.</p>
          </div>
        )
      )}

      {riskScore.level === 'critical' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-6">
          <p className="text-sm text-red-800">
            <strong>Critical Risk:</strong> Immediate action required. Review project status,
            address blocked tasks, and consider resource reallocation.
          </p>
        </div>
      )}

      {riskScore.level === 'high' && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mt-6">
          <p className="text-sm text-orange-800">
            <strong>High Risk:</strong> Project is at elevated risk. Monitor closely and take
            preventive measures to avoid escalation.
          </p>
        </div>
      )}
    </div>
  );
}

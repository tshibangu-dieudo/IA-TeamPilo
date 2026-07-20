import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { recommendationsAPI } from '../../api/recommendations';
import { projectsAPI } from '../../api/projects';

export default function RecommendationsList() {
  const [recommendations, setRecommendations] = useState([]);
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [activeTab, setActiveTab] = useState('pending'); // 'pending' | 'history'
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [actioningId, setActioningId] = useState(null); // track which card is being accepted/dismissed
  const [successMessages, setSuccessMessages] = useState({}); // track inline status updates per card
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadProjects();
    loadRecommendations();
  }, [selectedProjectId, activeTab]);

  const loadProjects = async () => {
    try {
      const response = await projectsAPI.getMyProjects();
      setProjects(response.data);
    } catch (err) {
      console.error('Failed to load projects', err);
    }
  };

  const loadRecommendations = async () => {
    setLoading(true);
    try {
      let response;
      if (selectedProjectId) {
        response = await recommendationsAPI.listByProject(
          selectedProjectId, 
          activeTab === 'pending' ? 'pending' : ''
        );
      } else {
        response = await recommendationsAPI.list(
          activeTab === 'pending' ? 'pending' : ''
        );
      }
      
      // If history tab, filter out pending recommendations
      let data = response.data;
      if (activeTab === 'history') {
        data = data.filter(r => r.status !== 'pending');
      }
      
      setRecommendations(data);
    } catch (err) {
      setError('Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedProjectId) {
      setError('Please select a project to run AI diagnostics.');
      return;
    }
    setGenerating(true);
    setError('');
    try {
      await recommendationsAPI.generate(selectedProjectId);
      await loadRecommendations();
    } catch (err) {
      setError('Failed to run diagnostics or no new recommendations found.');
    } finally {
      setGenerating(false);
    }
  };

  const handleAccept = async (id, suggestedName) => {
    setActioningId(id);
    setError('');
    try {
      await recommendationsAPI.accept(id);
      setSuccessMessages(prev => ({ ...prev, [id]: `Reassigned to ${suggestedName} ✓` }));
      // Remove from list after a short delay for visual transition
      setTimeout(() => {
        setRecommendations(prev => prev.filter(r => r.id !== id));
      }, 1500);
    } catch (err) {
      setError('Failed to apply reassignment.');
    } finally {
      setActioningId(null);
    }
  };

  const handleDismiss = async (id) => {
    setActioningId(id);
    setError('');
    try {
      await recommendationsAPI.dismiss(id);
      setSuccessMessages(prev => ({ ...prev, [id]: 'Recommendation dismissed' }));
      setTimeout(() => {
        setRecommendations(prev => prev.filter(r => r.id !== id));
      }, 1500);
    } catch (err) {
      setError('Failed to dismiss recommendation.');
    } finally {
      setActioningId(null);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical':
        return 'border-red-500 bg-red-50 text-red-700';
      case 'high':
        return 'border-orange-500 bg-orange-50 text-orange-700';
      case 'medium':
        return 'border-blue-500 bg-blue-50 text-blue-700';
      default:
        return 'border-gray-300 bg-gray-50 text-gray-700';
    }
  };

  const getTypeLabel = (type) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-indigo-900 via-slate-900 to-indigo-950 rounded-2xl p-6 md:p-8 text-white shadow-xl mb-8">
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">AI Recommendation Inbox</h1>
        <p className="mt-2 text-indigo-200 max-w-2xl text-sm md:text-base">
          Continuously analyzing workloads, task blockers, and deadline proximity. Select projects and trigger diagnostics to redistribute responsibilities.
        </p>
        
        {/* Actions Controls */}
        <div className="mt-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          <div className="w-full sm:w-64">
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">All Scoped Projects</option>
              {projects.map((proj) => (
                <option key={proj.id} value={proj.id}>{proj.name}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating || !selectedProjectId}
            className={`w-full sm:w-auto px-5 py-2 font-medium rounded-lg text-white shadow transition-colors flex items-center justify-center gap-2 ${
              !selectedProjectId 
                ? 'bg-gray-600 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800'
            }`}
          >
            {generating ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Running Diagnostics...
              </>
            ) : (
              'Run AI Diagnostics'
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Tabs Menu */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('pending')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'pending'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Pending Action ({activeTab === 'pending' ? recommendations.length : '?'})
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'history'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Recommendation History
          </button>
        </nav>
      </div>

      {/* Grid List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2].map(n => (
            <div key={n} className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="flex gap-4">
                <div className="h-10 bg-gray-200 rounded w-24"></div>
                <div className="h-10 bg-gray-200 rounded w-24"></div>
              </div>
            </div>
          ))}
        </div>
      ) : recommendations.length === 0 ? (
        <div className="text-center py-16 bg-white border border-gray-100 rounded-2xl shadow-sm">
          <svg className="mx-auto h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-2 text-lg font-semibold text-gray-900">All Clear!</h3>
          <p className="mt-1 text-sm text-gray-500">
            {activeTab === 'pending' 
              ? 'No pending recommendations found. Your team workloads are balanced and tasks are on schedule.'
              : 'No recommendation decision logs found.'}
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {recommendations.map((reco) => {
            const isAccepted = reco.status === 'accepted';
            const isDismissed = reco.status === 'dismissed';
            const suggestedName = reco.suggested_assignee ? (reco.suggested_assignee.full_name || reco.suggested_assignee.username) : '';
            const currentName = reco.current_assignee ? (reco.current_assignee.full_name || reco.current_assignee.username) : 'Unassigned';
            
            return (
              <div
                key={reco.id}
                className={`bg-white rounded-xl shadow-sm hover:shadow-md border-l-4 p-6 transition-all duration-200 relative overflow-hidden ${getPriorityColor(reco.priority)}`}
              >
                {/* Source and Confidence badges */}
                <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-800 border border-slate-200">
                      {getTypeLabel(reco.recommendation_type)}
                    </span>
                    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${
                      reco.generated_by === 'granite'
                        ? 'bg-purple-50 text-purple-700 border-purple-200'
                        : 'bg-gray-50 text-gray-600 border-gray-200'
                    }`}>
                      {reco.generated_by === 'granite' ? 'AI (IBM Granite)' : 'Safety Fallback'}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-xs font-bold rounded ${
                      reco.confidence_level === 'HIGH' ? 'bg-green-100 text-green-800' :
                      reco.confidence_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {reco.confidence_score}% Confidence
                    </span>
                    <span className="text-xs text-gray-400">
                      {new Date(reco.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <h3 
                  className="text-lg font-bold text-gray-900 cursor-pointer hover:text-indigo-600 transition-colors"
                  onClick={() => navigate(`/recommendations/${reco.id}`)}
                >
                  {reco.title}
                </h3>
                <p className="text-sm text-gray-600 mt-1 mb-4">{reco.description}</p>

                {/* Reassignment Flow Detail */}
                {reco.task && (
                  <div className="bg-slate-50 border border-slate-100 rounded-lg p-4 mb-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div className="flex-1">
                      <span className="text-xs font-semibold uppercase text-gray-400 block mb-1">Task at Hand</span>
                      <span className="font-semibold text-gray-800 text-sm">{reco.task.title}</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <span className="text-xs text-gray-400 block">Current Assignee</span>
                        <span className="text-sm font-semibold text-gray-700">{currentName}</span>
                      </div>
                      <div className="text-gray-400 font-bold px-2">→</div>
                      <div>
                        <span className="text-xs text-gray-400 block">Suggested Candidate</span>
                        <span className="text-sm font-semibold text-indigo-700">{suggestedName}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Explanation text box */}
                <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4 mb-4">
                  <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider mb-1">AI Recommendation Justification</h4>
                  <p className="text-sm text-indigo-950 italic leading-relaxed">
                    "{reco.explanation}"
                  </p>
                </div>

                {/* Actions with inline statuses */}
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-100">
                  <button
                    onClick={() => navigate(`/recommendations/${reco.id}`)}
                    className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                  >
                    View Details & Metrics
                  </button>

                  <div className="flex items-center gap-3">
                    {successMessages[reco.id] ? (
                      <span className={`text-sm font-bold px-3 py-1.5 rounded-lg ${
                        isAccepted || successMessages[reco.id].includes('✓')
                          ? 'bg-green-50 text-green-700 border border-green-200'
                          : 'bg-gray-50 text-gray-600 border border-gray-200'
                      }`}>
                        {successMessages[reco.id]}
                      </span>
                    ) : activeTab === 'pending' ? (
                      <>
                        <button
                          onClick={() => handleDismiss(reco.id)}
                          disabled={actioningId === reco.id}
                          className="px-3.5 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-50 rounded-lg border border-gray-200 transition-colors"
                        >
                          Dismiss
                        </button>
                        <button
                          onClick={() => handleAccept(reco.id, suggestedName)}
                          disabled={actioningId === reco.id}
                          className="px-4 py-1.5 text-sm font-medium bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors shadow-sm"
                        >
                          Accept & Reassign
                        </button>
                      </>
                    ) : (
                      <span className={`text-xs uppercase font-bold px-2.5 py-1 rounded ${
                        isAccepted ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {reco.status}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

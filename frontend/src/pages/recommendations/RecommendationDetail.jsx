import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { recommendationsAPI } from '../../api/recommendations';

export default function RecommendationDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actioning, setActioning] = useState(false);
  const [actionStatus, setActionStatus] = useState('');

  useEffect(() => {
    loadRecommendationDetail();
  }, [id]);

  const loadRecommendationDetail = async () => {
    try {
      const response = await recommendationsAPI.get(id);
      setRecommendation(response.data);
    } catch (err) {
      setError('Failed to load recommendation details');
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async () => {
    if (!recommendation) return;
    setActioning(true);
    setActionStatus('Accepting and reassigning...');
    try {
      await recommendationsAPI.accept(id);
      setActionStatus('Reassigned successfully ✓');
      setTimeout(() => {
        navigate('/recommendations');
      }, 1500);
    } catch (err) {
      setError('Failed to accept recommendation');
      setActioning(false);
      setActionStatus('');
    }
  };

  const handleDismiss = async () => {
    if (!recommendation) return;
    setActioning(true);
    setActionStatus('Dismissing recommendation...');
    try {
      await recommendationsAPI.dismiss(id);
      setActionStatus('Recommendation dismissed');
      setTimeout(() => {
        navigate('/recommendations');
      }, 1500);
    } catch (err) {
      setError('Failed to dismiss recommendation');
      setActioning(false);
      setActionStatus('');
    }
  };

  const getPriorityBadgeColor = (priority) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTypeLabel = (type) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading details...</div>;

  if (error || !recommendation) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <button onClick={() => navigate('/recommendations')} className="text-indigo-600 hover:text-indigo-800 mb-6 inline-block">
          ← Back to Inbox
        </button>
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
          {error || 'Recommendation not found'}
        </div>
      </div>
    );
  }

  const suggestedName = recommendation.suggested_assignee 
    ? (recommendation.suggested_assignee.full_name || recommendation.suggested_assignee.username) 
    : 'None';
  const currentName = recommendation.current_assignee 
    ? (recommendation.current_assignee.full_name || recommendation.current_assignee.username) 
    : 'Unassigned';

  const isPending = recommendation.status === 'pending';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Navigation */}
      <button
        onClick={() => navigate('/recommendations')}
        className="text-indigo-600 hover:text-indigo-800 mb-6 flex items-center gap-1.5 font-medium transition-colors"
      >
        <span>←</span> Back to Recommendations Inbox
      </button>

      {/* Main card */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-xl overflow-hidden">
        {/* Card Header banner */}
        <div className="bg-slate-900 px-6 py-8 text-white relative">
          <div className="flex flex-wrap gap-2 items-center mb-3">
            <span className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded bg-slate-800 border border-slate-700 text-indigo-300">
              {getTypeLabel(recommendation.recommendation_type)}
            </span>
            <span className={`px-2.5 py-0.5 text-xs font-semibold rounded border ${getPriorityBadgeColor(recommendation.priority)}`}>
              {recommendation.priority.toUpperCase()} PRIORITY
            </span>
          </div>
          
          <h1 className="text-2xl md:text-3xl font-extrabold">{recommendation.title}</h1>
          <p className="mt-2 text-slate-400 text-sm">{recommendation.description}</p>
        </div>

        {/* Detailed Metrics Panel */}
        <div className="p-6 md:p-8 space-y-8">
          {/* Diagnostic Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
              <span className="text-xs font-semibold text-gray-400 block mb-1">AI Confidence Score</span>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-extrabold text-indigo-900">{recommendation.confidence_score}%</span>
                <span className={`text-xs font-bold ${
                  recommendation.confidence_level === 'HIGH' ? 'text-green-600' :
                  recommendation.confidence_level === 'MEDIUM' ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  ({recommendation.confidence_level})
                </span>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
              <span className="text-xs font-semibold text-gray-400 block mb-1">Engine Source</span>
              <span className="text-lg font-bold text-gray-800 block mt-1">
                {recommendation.generated_by === 'granite' ? 'IBM Granite AI' : 'Deterministic Template'}
              </span>
            </div>

            <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
              <span className="text-xs font-semibold text-gray-400 block mb-1">Decision Status</span>
              <span className="text-lg font-bold text-gray-800 capitalize block mt-1">
                {recommendation.status}
              </span>
            </div>
          </div>

          {/* Reassignment details */}
          {recommendation.task && (
            <div className="border border-gray-100 rounded-xl overflow-hidden">
              <div className="bg-slate-50 px-4 py-3 border-b border-gray-100">
                <h3 className="font-bold text-gray-800 text-sm">Suggested Reassignment Plan</h3>
              </div>
              <div className="p-4 sm:p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Task Details */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Affected Task</h4>
                  <div>
                    <span className="text-base font-bold text-gray-800 block">{recommendation.task.title}</span>
                    <span className="text-xs text-gray-500 block mt-1">ID: {recommendation.task.id}</span>
                  </div>
                </div>

                {/* Flow View */}
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Workload Transfer</h4>
                  <div className="flex items-center gap-4">
                    <div className="flex-1 bg-red-50/50 border border-red-100 rounded-lg p-3">
                      <span className="text-xs text-gray-400 block">From (Assignee)</span>
                      <span className="text-sm font-semibold text-gray-800">{currentName}</span>
                    </div>
                    <div className="text-xl text-gray-400 font-bold">→</div>
                    <div className="flex-1 bg-green-50/50 border border-green-100 rounded-lg p-3">
                      <span className="text-xs text-gray-400 block">To (Suggested)</span>
                      <span className="text-sm font-semibold text-indigo-800">{suggestedName}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Explanation Text block */}
          <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-6 relative overflow-hidden">
            <h3 className="text-xs font-bold text-indigo-900 uppercase tracking-wider mb-2">Recommendation Justification</h3>
            <blockquote className="text-base text-indigo-950 italic font-medium leading-relaxed">
              "{recommendation.explanation}"
            </blockquote>
          </div>

          {/* Decided Audit metadata */}
          {recommendation.status !== 'pending' && (
            <div className="bg-gray-50 border border-gray-100 rounded-xl p-4 text-sm text-gray-500 space-y-1">
              {recommendation.accepted_by && (
                <p>Reviewed and decided by: <span className="font-semibold">{recommendation.accepted_by}</span></p>
              )}
              {recommendation.accepted_at && (
                <p>Accepted at: {new Date(recommendation.accepted_at).toLocaleString()}</p>
              )}
              {recommendation.dismissed_at && (
                <p>Dismissed at: {new Date(recommendation.dismissed_at).toLocaleString()}</p>
              )}
            </div>
          )}

          {/* Accept / Dismiss controls */}
          {isPending && (
            <div className="flex items-center justify-end gap-4 border-t border-gray-100 pt-6 mt-8">
              {actionStatus ? (
                <div className="text-sm font-bold text-indigo-700 bg-indigo-50 px-4 py-2 rounded-lg border border-indigo-200 animate-pulse">
                  {actionStatus}
                </div>
              ) : (
                <>
                  <button
                    onClick={handleDismiss}
                    disabled={actioning}
                    className="px-6 py-2.5 font-medium border border-gray-200 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors shadow-sm"
                  >
                    Dismiss Recommendation
                  </button>
                  <button
                    onClick={handleAccept}
                    disabled={actioning}
                    className="px-6 py-2.5 font-semibold bg-green-600 hover:bg-green-700 active:bg-green-800 text-white rounded-lg transition-colors shadow-md"
                  >
                    Accept & Apply Reassignment
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

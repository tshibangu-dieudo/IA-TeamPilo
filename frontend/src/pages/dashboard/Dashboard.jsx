/**
 * Dashboard — role-aware landing page at /.
 * See docs/15_UI_UX.md §3 (PM), §6 (Executive).
 * Replaces the Sprint 0 "Dashboard - Coming Soon" placeholder.
 *
 * Roles:
 *   pm / admin   → PMDashboard
 *   executive    → ExecutiveDashboard
 *   member       → MemberDashboard
 *
 * Rules: Tailwind only, no TypeScript.
 * All data fetched from GET /api/dashboard/summary/ (single call).
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { dashboardAPI } from '../../api/dashboard';

// ------------------------------------------------------------------ helpers

const RISK_COLORS = {
  low:      'bg-green-100 text-green-800 border-green-200',
  moderate: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  high:     'bg-orange-100 text-orange-800 border-orange-200',
  critical: 'bg-red-100 text-red-800 border-red-200',
};

const RISK_BAR_COLORS = {
  low: 'bg-green-500', moderate: 'bg-yellow-500',
  high: 'bg-orange-500', critical: 'bg-red-500',
};

const WORKLOAD_STATUS_COLORS = {
  underloaded: 'bg-blue-100 text-blue-800',
  balanced: 'bg-green-100 text-green-800',
  overloaded: 'bg-orange-100 text-orange-800',
  critically_overloaded: 'bg-red-100 text-red-800',
};

const WORKLOAD_BAR_COLORS = {
  underloaded: 'bg-blue-500', balanced: 'bg-green-500',
  overloaded: 'bg-orange-500', critically_overloaded: 'bg-red-500',
};

const TASK_STATUS_COLORS = {
  todo: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  blocked: 'bg-red-100 text-red-700',
  waiting_on_dependency: 'bg-yellow-100 text-yellow-700',
  done: 'bg-green-100 text-green-700',
};

function RiskBadge({ level }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-bold border ${RISK_COLORS[level] ?? 'bg-gray-100 text-gray-700'}`}>
      {(level ?? 'unknown').toUpperCase()}
    </span>
  );
}

function WorkloadBar({ percentage, statusKey }) {
  const capped = Math.min(percentage, 150);
  const width = (capped / 150) * 100;
  return (
    <div className="w-full bg-gray-200 rounded-full h-2.5">
      <div
        className={`h-2.5 rounded-full transition-all ${WORKLOAD_BAR_COLORS[statusKey] ?? 'bg-gray-400'}`}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}

function StatCard({ label, value, sub, color = 'indigo' }) {
  const colors = {
    indigo: 'bg-indigo-50 text-indigo-700',
    green: 'bg-green-50 text-green-700',
    orange: 'bg-orange-50 text-orange-700',
    red: 'bg-red-50 text-red-700',
    gray: 'bg-gray-50 text-gray-700',
  };
  return (
    <div className={`rounded-xl p-4 ${colors[color]}`}>
      <p className="text-sm font-medium opacity-80">{label}</p>
      <p className="text-3xl font-extrabold mt-1">{value}</p>
      {sub && <p className="text-xs mt-1 opacity-70">{sub}</p>}
    </div>
  );
}

// ------------------------------------------------------------------ PM Dashboard

function PMDashboard({ data }) {
  const { projects_summary = [], my_workload, pending_recommendations_count = 0,
          top_recommendations = [], unread_notifications_count = 0 } = data;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="My Projects" value={projects_summary.length} color="indigo" />
        <StatCard
          label="Pending Recommendations"
          value={pending_recommendations_count}
          color={pending_recommendations_count > 0 ? 'orange' : 'green'}
          sub={pending_recommendations_count > 0 ? 'Needs your review' : 'All clear'}
        />
        <StatCard
          label="Unread Notifications"
          value={unread_notifications_count}
          color={unread_notifications_count > 0 ? 'red' : 'gray'}
        />
        {my_workload ? (
          <StatCard
            label="My Workload"
            value={`${my_workload.workload_percentage.toFixed(0)}%`}
            sub={my_workload.status.replace(/_/g, ' ')}
            color={
              my_workload.status === 'critically_overloaded' ? 'red'
              : my_workload.status === 'overloaded' ? 'orange'
              : my_workload.status === 'balanced' ? 'green' : 'indigo'
            }
          />
        ) : (
          <StatCard label="My Workload" value="—" sub="No snapshot yet" color="gray" />
        )}
      </div>

      {/* Projects grid — sorted by risk descending */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">My Projects</h2>
          <Link to="/projects" className="text-sm text-indigo-600 hover:underline">View all →</Link>
        </div>
        {projects_summary.length === 0 ? (
          <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center">
            <p className="text-gray-500">No projects yet.</p>
            <Link to="/projects" className="mt-2 inline-block text-sm text-indigo-600 hover:underline">
              Create your first project
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects_summary.map((p) => (
              <Link key={p.id} to={`/projects/${p.id}`}
                className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow block">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-gray-900 truncate pr-2">{p.name}</h3>
                  {p.risk ? <RiskBadge level={p.risk.level} /> : (
                    <span className="text-xs text-gray-400">No risk data</span>
                  )}
                </div>
                {p.risk && (
                  <div className="mb-3">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Risk Score</span>
                      <span>{p.risk.score.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${RISK_BAR_COLORS[p.risk.level] ?? 'bg-gray-400'}`}
                        style={{ width: `${p.risk.score}%` }}
                      />
                    </div>
                  </div>
                )}
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>Due {new Date(p.end_date).toLocaleDateString()}</span>
                  {p.pending_recommendations_count > 0 && (
                    <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full font-medium">
                      {p.pending_recommendations_count} recs pending
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Top recommendations preview */}
      {top_recommendations.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Pending Recommendations</h2>
            <Link to="/recommendations" className="text-sm text-indigo-600 hover:underline">
              View all ({pending_recommendations_count}) →
            </Link>
          </div>
          <div className="space-y-3">
            {top_recommendations.map((r) => (
              <Link key={r.id} to={`/recommendations/${r.id}`}
                className="flex items-center justify-between bg-white border border-gray-200 rounded-xl px-5 py-4 hover:shadow-sm transition-shadow block">
                <div className="flex-1 min-w-0 pr-4">
                  <p className="text-sm font-medium text-gray-900 truncate">{r.title}</p>
                  {r.current_assignee && r.suggested_assignee && (
                    <p className="text-xs text-gray-500 mt-0.5">
                      {r.current_assignee} → {r.suggested_assignee}
                    </p>
                  )}
                </div>
                <span className={`flex-shrink-0 text-xs font-bold px-2.5 py-1 rounded-full ${
                  r.confidence_score >= 80 ? 'bg-green-100 text-green-800'
                  : r.confidence_score >= 60 ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
                }`}>
                  {r.confidence_score}%
                </span>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// ------------------------------------------------------------------ Executive Dashboard

function ExecutiveDashboard({ data }) {
  const { portfolio = [], unread_notifications_count = 0 } = data;
  const critical = portfolio.filter(p => p.risk?.level === 'critical').length;
  const high = portfolio.filter(p => p.risk?.level === 'high').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Projects" value={portfolio.length} color="indigo" />
        <StatCard label="Critical Risk" value={critical} color={critical > 0 ? 'red' : 'gray'} />
        <StatCard label="High Risk" value={high} color={high > 0 ? 'orange' : 'gray'} />
        <StatCard label="Unread Alerts" value={unread_notifications_count}
          color={unread_notifications_count > 0 ? 'orange' : 'gray'} />
      </div>

      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Portfolio — Ranked by Risk
        </h2>
        {portfolio.length === 0 ? (
          <p className="text-gray-500">No projects in the organisation yet.</p>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-5 py-3 font-medium text-gray-600">Project</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-600">Team</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-600">Status</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-600">Risk</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-600">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {portfolio.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-5 py-3 font-medium text-gray-900">
                      <Link to={`/projects/${p.id}`} className="hover:text-indigo-600">
                        {p.name}
                      </Link>
                    </td>
                    <td className="px-5 py-3 text-gray-500">{p.team_name ?? '—'}</td>
                    <td className="px-5 py-3">
                      <span className="capitalize text-gray-600">{p.status}</span>
                    </td>
                    <td className="px-5 py-3">
                      {p.risk ? <RiskBadge level={p.risk.level} /> : <span className="text-gray-400">—</span>}
                    </td>
                    <td className="px-5 py-3">
                      {p.risk ? (
                        <div className="flex items-center gap-2">
                          <div className="w-24 bg-gray-100 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${RISK_BAR_COLORS[p.risk.level] ?? 'bg-gray-400'}`}
                              style={{ width: `${p.risk.score}%` }}
                            />
                          </div>
                          <span className="text-gray-700">{p.risk.score.toFixed(1)}%</span>
                        </div>
                      ) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

// ------------------------------------------------------------------ Member Dashboard

function MemberDashboard({ data }) {
  const { my_workload, my_tasks_by_status = {}, my_upcoming_tasks = [],
          unread_notifications_count = 0 } = data;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Workload card */}
      <section className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">My Workload</h2>
        {my_workload ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-3xl font-extrabold text-gray-900">
                {my_workload.workload_percentage.toFixed(0)}%
              </span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                WORKLOAD_STATUS_COLORS[my_workload.status] ?? 'bg-gray-100 text-gray-700'
              }`}>
                {my_workload.status.replace(/_/g, ' ')}
              </span>
            </div>
            <WorkloadBar
              percentage={my_workload.workload_percentage}
              statusKey={my_workload.status}
            />
            {(my_workload.status === 'overloaded' || my_workload.status === 'critically_overloaded') && (
              <p className="text-sm text-orange-700 bg-orange-50 border border-orange-200 rounded-lg px-4 py-2">
                Your workload is above recommended capacity. Consider reporting a blocker or requesting task reassignment.
              </p>
            )}
          </div>
        ) : (
          <p className="text-gray-500">No workload snapshot yet — data will appear once tasks are assigned.</p>
        )}
      </section>

      {/* Task status summary */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">My Tasks Overview</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { key: 'todo', label: 'To Do', color: 'gray' },
            { key: 'in_progress', label: 'In Progress', color: 'indigo' },
            { key: 'blocked', label: 'Blocked', color: 'red' },
            { key: 'waiting_on_dependency', label: 'Waiting', color: 'orange' },
          ].map(({ key, label, color }) => (
            <StatCard
              key={key}
              label={label}
              value={my_tasks_by_status[key] ?? 0}
              color={my_tasks_by_status[key] > 0 ? color : 'gray'}
            />
          ))}
        </div>
      </section>

      {/* Upcoming tasks list */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">My Upcoming Tasks</h2>
          <Link to="/tasks" className="text-sm text-indigo-600 hover:underline">View all →</Link>
        </div>
        {my_upcoming_tasks.length === 0 ? (
          <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center">
            <p className="text-gray-500">No open tasks assigned to you.</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <ul className="divide-y divide-gray-100">
              {my_upcoming_tasks.map((t) => (
                <li key={t.id}>
                  <Link to={`/tasks/${t.id}`}
                    className="flex items-center justify-between px-5 py-3 hover:bg-gray-50 transition-colors">
                    <div className="flex-1 min-w-0 pr-4">
                      <p className="text-sm font-medium text-gray-900 truncate">{t.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{t.project_name}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        TASK_STATUS_COLORS[t.status] ?? 'bg-gray-100 text-gray-700'
                      }`}>
                        {t.status.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(t.deadline).toLocaleDateString()}
                      </span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}

// ------------------------------------------------------------------ Admin Dashboard

function AdminDashboard({ data }) {
  // Admin gets PM payload — show org-level counts + all projects
  return <PMDashboard data={data} />;
}

// ------------------------------------------------------------------ Root Dashboard component

export default function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    dashboardAPI.getSummary()
      .then((res) => { setSummary(res.data); })
      .catch((err) => { setError('Failed to load dashboard data.'); })
      .finally(() => { setLoading(false); });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="inline-block w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-gray-500">Loading your dashboard…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <p className="text-red-600 font-medium">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!summary) return null;

  const role = user?.role ?? 'member';

  return (
    <>
      {/* Welcome header */}
      <div className="bg-gradient-to-r from-indigo-900 to-slate-900 text-white px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl md:text-3xl font-extrabold">
            Welcome back, {user?.username ?? 'User'}
          </h1>
          <p className="mt-1 text-indigo-200 text-sm">
            {role === 'pm' && "Here's your project overview — sorted by risk, highest first."}
            {role === 'executive' && 'Portfolio-wide risk overview across all active projects.'}
            {role === 'member' && 'Your workload and upcoming tasks at a glance.'}
            {role === 'admin' && 'System overview and project management.'}
          </p>
        </div>
      </div>

      {/* Role-specific content */}
      {(role === 'pm' || role === 'admin') && <PMDashboard data={summary} />}
      {role === 'executive' && <ExecutiveDashboard data={summary} />}
      {role === 'member' && <MemberDashboard data={summary} />}
    </>
  );
}

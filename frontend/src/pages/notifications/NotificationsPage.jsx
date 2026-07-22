/**
 * NotificationsPage — full notification list at /notifications.
 * See Sprint 7 Req 15 and docs/15_UI_UX.md.
 *
 * Features:
 * - Lists all user notifications, most recent first.
 * - "Mark all as read" button.
 * - Click individual unread notification to mark it read.
 * - Visual distinction between read and unread.
 * - Tailwind utility classes only — no custom CSS.
 */
import { useNotifications } from '../../hooks/useNotifications';

const TYPE_LABELS = {
  overload_alert: 'Overload Alert',
  risk_alert: 'Risk: Critical',
  recommendation: 'Recommendation',
  task_blocked: 'Task Blocked',
  task_reassigned: 'Task Assigned',
};

const TYPE_BADGE_COLORS = {
  overload_alert: 'bg-orange-100 text-orange-800',
  risk_alert: 'bg-red-100 text-red-800',
  recommendation: 'bg-indigo-100 text-indigo-800',
  task_blocked: 'bg-yellow-100 text-yellow-800',
  task_reassigned: 'bg-green-100 text-green-800',
};

function formatDate(isoString) {
  if (!isoString) return '';
  return new Date(isoString).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function NotificationsPage() {
  const {
    notifications,
    unreadCount,
    loading,
    error,
    markAsRead,
    markAllAsRead,
  } = useNotifications();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Loading notifications…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-red-500">Failed to load notifications. Please refresh the page.</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
          {unreadCount > 0 && (
            <p className="mt-1 text-sm text-gray-500">{unreadCount} unread</p>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={markAllAsRead}
            className="px-4 py-2 text-sm font-medium text-indigo-700 bg-indigo-50 rounded-lg hover:bg-indigo-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            Mark all as read
          </button>
        )}
      </div>

      {/* Empty state */}
      {notifications.length === 0 && (
        <div className="text-center py-16">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="mx-auto h-12 w-12 text-gray-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 00-5-5.917V4a1 1 0 10-2 0v1.083A6 6 0 006 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          <p className="mt-4 text-gray-500">No notifications yet.</p>
        </div>
      )}

      {/* Notification list */}
      {notifications.length > 0 && (
        <ul className="space-y-2">
          {notifications.map((notif) => (
            <li
              key={notif.id}
              onClick={() => {
                if (!notif.is_read) markAsRead(notif.id);
              }}
              className={[
                'rounded-lg border p-4 cursor-pointer transition-colors',
                notif.is_read
                  ? 'bg-white border-gray-200 hover:bg-gray-50'
                  : 'bg-indigo-50 border-indigo-200 hover:bg-indigo-100',
              ].join(' ')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if ((e.key === 'Enter' || e.key === ' ') && !notif.is_read) {
                  markAsRead(notif.id);
                }
              }}
              aria-label={`${notif.title}${notif.is_read ? ' (read)' : ' (unread)'}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    {/* Unread dot */}
                    {!notif.is_read && (
                      <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0" aria-hidden="true" />
                    )}
                    {/* Type badge */}
                    <span
                      className={[
                        'inline-block px-2 py-0.5 rounded-full text-xs font-medium',
                        TYPE_BADGE_COLORS[notif.notification_type] ?? 'bg-gray-100 text-gray-700',
                      ].join(' ')}
                    >
                      {TYPE_LABELS[notif.notification_type] ?? notif.notification_type}
                    </span>
                  </div>
                  <p className={[
                    'text-sm font-semibold',
                    notif.is_read ? 'text-gray-700' : 'text-gray-900',
                  ].join(' ')}>
                    {notif.title}
                  </p>
                  <p className="mt-1 text-sm text-gray-600 leading-relaxed">
                    {notif.message}
                  </p>

                  {/* Linked entities */}
                  {(notif.project || notif.task) && (
                    <p className="mt-2 text-xs text-gray-400">
                      {notif.project && <span>Project: {notif.project.name}</span>}
                      {notif.project && notif.task && <span className="mx-1">·</span>}
                      {notif.task && <span>Task: {notif.task.title}</span>}
                    </p>
                  )}
                </div>

                {/* Timestamp */}
                <time
                  dateTime={notif.created_at}
                  className="flex-shrink-0 text-xs text-gray-400 whitespace-nowrap"
                >
                  {formatDate(notif.created_at)}
                </time>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

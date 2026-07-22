/**
 * NotificationBell — top-navigation bell icon with unread badge and dropdown preview.
 * See docs/15_UI_UX.md and Sprint 7 Req 14.
 *
 * Rules:
 * - Tailwind utility classes only — no custom CSS files (.ai/coding-rules.md).
 * - Polling via useNotifications hook (30s interval).
 * - Badge caps at 99+.
 * - Dropdown shows 5 most recent unread notifications.
 * - "View all" links to /notifications.
 */
import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useNotifications } from '../../hooks/useNotifications';

/** Map notification_type to a human-readable label. */
const TYPE_LABELS = {
  overload_alert: 'Overload Alert',
  risk_alert: 'Risk Alert',
  recommendation: 'Recommendation',
  task_blocked: 'Task Blocked',
  task_reassigned: 'Task Assigned',
};

/** Format a UTC ISO timestamp as a short relative time string. */
function relativeTime(isoString) {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function NotificationBell() {
  const { notifications, unreadCount, markAsRead } = useNotifications();
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  const preview = notifications.filter((n) => !n.is_read).slice(0, 5);
  const badgeLabel = unreadCount > 99 ? '99+' : String(unreadCount);

  function handleNotificationClick(id) {
    markAsRead(id);
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell button */}
      <button
        onClick={() => setOpen((prev) => !prev)}
        aria-label={`Notifications${unreadCount > 0 ? `, ${unreadCount} unread` : ''}`}
        className="relative p-2 rounded-full text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      >
        {/* Bell icon (inline SVG — no external dependency) */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 00-5-5.917V4a1 1 0 10-2 0v1.083A6 6 0 006 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>

        {/* Unread count badge */}
        {unreadCount > 0 && (
          <span
            className="absolute top-0.5 right-0.5 flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-xs font-bold leading-none"
            aria-hidden="true"
          >
            {badgeLabel}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 z-50">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-800">Notifications</h3>
            {unreadCount > 0 && (
              <span className="text-xs text-gray-500">{unreadCount} unread</span>
            )}
          </div>

          {preview.length === 0 ? (
            <p className="px-4 py-6 text-sm text-gray-500 text-center">
              No unread notifications.
            </p>
          ) : (
            <ul className="divide-y divide-gray-100 max-h-72 overflow-y-auto">
              {preview.map((notif) => (
                <li key={notif.id}>
                  <button
                    onClick={() => handleNotificationClick(notif.id)}
                    className="w-full text-left px-4 py-3 hover:bg-gray-50 focus:outline-none focus:bg-gray-50"
                  >
                    <div className="flex items-start gap-2">
                      <span className="mt-0.5 inline-block w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {notif.title}
                        </p>
                        <p className="text-xs text-gray-500">
                          {TYPE_LABELS[notif.notification_type] ?? notif.notification_type}
                          {' · '}
                          {relativeTime(notif.created_at)}
                        </p>
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}

          <div className="px-4 py-3 border-t border-gray-100 text-center">
            <Link
              to="/notifications"
              onClick={() => setOpen(false)}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
            >
              View all notifications
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

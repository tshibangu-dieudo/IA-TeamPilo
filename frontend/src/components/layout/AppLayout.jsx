/**
 * AppLayout — shared layout wrapper for all authenticated pages.
 * Provides top navigation bar with:
 *   - App brand / home link
 *   - Role-aware navigation links
 *   - NotificationBell (persistent across all pages)
 *   - User menu with logout
 *
 * Rules: Tailwind only, no custom CSS, no TypeScript.
 * See docs/15_UI_UX.md §3 (header with bell icon).
 */
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import NotificationBell from '../notifications/NotificationBell';

const NAV_LINKS = {
  pm: [
    { to: '/', label: 'Dashboard' },
    { to: '/projects', label: 'Projects' },
    { to: '/tasks', label: 'Tasks' },
    { to: '/recommendations', label: 'Recommendations' },
    { to: '/analytics/workload', label: 'Workload' },
    { to: '/chat', label: 'AI Chat' },
  ],
  member: [
    { to: '/', label: 'Dashboard' },
    { to: '/tasks', label: 'My Tasks' },
    { to: '/analytics/workload', label: 'Workload' },
  ],
  executive: [
    { to: '/', label: 'Dashboard' },
    { to: '/projects', label: 'Projects' },
    { to: '/recommendations', label: 'Recommendations' },
    { to: '/chat', label: 'AI Chat' },
  ],
  admin: [
    { to: '/', label: 'Dashboard' },
    { to: '/teams', label: 'Teams' },
    { to: '/projects', label: 'Projects' },
    { to: '/tasks', label: 'Tasks' },
    { to: '/recommendations', label: 'Recommendations' },
    { to: '/chat', label: 'AI Chat' },
  ],
};

export default function AppLayout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const role = user?.role ?? 'member';
  const links = NAV_LINKS[role] ?? NAV_LINKS.member;

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* ---- Top navigation bar ---- */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Brand */}
            <Link to="/" className="flex items-center gap-2 flex-shrink-0">
              <span className="text-xl font-extrabold text-indigo-700 tracking-tight">
                TeamPilot
              </span>
              <span className="hidden sm:inline-block text-xs font-medium text-indigo-400 bg-indigo-50 px-2 py-0.5 rounded-full">
                AI
              </span>
            </Link>

            {/* Nav links — hidden on small screens, shown md+ */}
            <nav className="hidden md:flex items-center gap-1" aria-label="Main navigation">
              {links.map((link) => {
                const active = location.pathname === link.to ||
                  (link.to !== '/' && location.pathname.startsWith(link.to));
                return (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={[
                      'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      active
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
                    ].join(' ')}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>

            {/* Right side: bell + user */}
            <div className="flex items-center gap-3">
              {/* NotificationBell — visible on every authenticated page */}
              <NotificationBell />

              {/* User info + logout */}
              {user && (
                <div className="flex items-center gap-2">
                  <span className="hidden sm:block text-sm font-medium text-gray-700">
                    {user.username}
                  </span>
                  <span className="hidden sm:inline-block text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full capitalize">
                    {role}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="ml-1 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    aria-label="Sign out"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Mobile nav — horizontal scroll */}
          <nav className="md:hidden flex gap-1 pb-2 overflow-x-auto" aria-label="Mobile navigation">
            {links.map((link) => {
              const active = location.pathname === link.to ||
                (link.to !== '/' && location.pathname.startsWith(link.to));
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={[
                    'flex-shrink-0 px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors',
                    active
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
                  ].join(' ')}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* ---- Page content ---- */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}

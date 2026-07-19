/**
 * Task Detail page component.
 * See .ai/architecture.md: src/pages/ - one folder per screen group.
 * See .ai/coding-rules.md: Tailwind utility classes only.
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { tasksAPI } from '../../api/tasks';

export default function TaskDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [history, setHistory] = useState([]);
  const [dependencies, setDependencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditForm, setShowEditForm] = useState(false);
  const [editTask, setEditTask] = useState({
    title: '',
    description: '',
    priority: '',
    deadline: ''
  });
  const [showDependencyForm, setShowDependencyForm] = useState(false);
  const [newDependencyId, setNewDependencyId] = useState('');

  useEffect(() => {
    loadTask();
    loadHistory();
    loadDependencies();
  }, [id]);

  const loadTask = async () => {
    try {
      const response = await tasksAPI.get(id);
      setTask(response.data);
      setEditTask({
        title: response.data.title,
        description: response.data.description,
        priority: response.data.priority,
        deadline: response.data.deadline
      });
    } catch (err) {
      setError('Failed to load task details');
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await tasksAPI.getHistory(id);
      setHistory(response.data);
    } catch (err) {
      console.error('Failed to load task history');
    }
  };

  const loadDependencies = async () => {
    try {
      const response = await tasksAPI.getDependencies(id);
      setDependencies(response.data);
    } catch (err) {
      console.error('Failed to load dependencies');
    }
  };

  const handleUpdateTask = async (e) => {
    e.preventDefault();
    try {
      await tasksAPI.update(id, editTask);
      setShowEditForm(false);
      loadTask();
    } catch (err) {
      setError('Failed to update task');
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await tasksAPI.updateStatus(id, { status: newStatus });
      loadTask();
      loadHistory();
    } catch (err) {
      setError('Failed to update task status');
    }
  };

  const handleAddDependency = async (e) => {
    e.preventDefault();
    try {
      await tasksAPI.addDependency(id, { depends_on_task_id: newDependencyId });
      setShowDependencyForm(false);
      setNewDependencyId('');
      loadDependencies();
    } catch (err) {
      setError('Failed to add dependency');
    }
  };

  const handleRemoveDependency = async (depId) => {
    try {
      await tasksAPI.removeDependency(id, depId);
      loadDependencies();
    } catch (err) {
      setError('Failed to remove dependency');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'todo': return 'bg-gray-100 text-gray-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'blocked': return 'bg-red-100 text-red-800';
      case 'waiting_on_dependency': return 'bg-yellow-100 text-yellow-800';
      case 'done': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) return <div className="text-center py-8">Loading task details...</div>;

  if (!task) return <div className="text-center py-8">Task not found</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <button
          onClick={() => navigate('/tasks')}
          className="text-indigo-600 hover:text-indigo-800 mb-4 inline-block"
        >
          ← Back to Tasks
        </button>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{task.title}</h1>
            <p className="text-gray-600 mt-2">{task.description || 'No description'}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowEditForm(!showEditForm)}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              {showEditForm ? 'Cancel' : 'Edit'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {showEditForm && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Edit Task</h2>
          <form onSubmit={handleUpdateTask}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
              <input
                type="text"
                required
                value={editTask.title}
                onChange={(e) => setEditTask({ ...editTask, title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                value={editTask.description}
                onChange={(e) => setEditTask({ ...editTask, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                rows="3"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
                <select
                  value={editTask.priority}
                  onChange={(e) => setEditTask({ ...editTask, priority: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Deadline</label>
                <input
                  type="date"
                  required
                  value={editTask.deadline}
                  onChange={(e) => setEditTask({ ...editTask, deadline: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
              >
                Update Task
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Task Information</h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Status</h3>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(task.status)}`}>
                  {task.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
                <select
                  value={task.status}
                  onChange={(e) => handleStatusChange(e.target.value)}
                  className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="todo">To Do</option>
                  <option value="in_progress">In Progress</option>
                  <option value="blocked">Blocked</option>
                  <option value="waiting_on_dependency">Waiting on Dependency</option>
                  <option value="done">Done</option>
                </select>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Project</h3>
              <p className="text-lg text-gray-900">{task.project_name}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Assignee</h3>
              <p className="text-lg text-gray-900">{task.assignee_username || 'Unassigned'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Priority</h3>
              <p className="text-lg text-gray-900 capitalize">{task.priority}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Estimated Effort</h3>
              <p className="text-lg text-gray-900">{task.estimated_effort_hours} hours</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Deadline</h3>
              <p className="text-lg text-gray-900">{new Date(task.deadline).toLocaleDateString()}</p>
            </div>
            {task.blocked_reason && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Blocked Reason</h3>
                <p className="text-lg text-gray-900">{task.blocked_reason}</p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Dependencies</h2>
          <button
            onClick={() => setShowDependencyForm(!showDependencyForm)}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 mb-4"
          >
            {showDependencyForm ? 'Cancel' : 'Add Dependency'}
          </button>

          {showDependencyForm && (
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <form onSubmit={handleAddDependency}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Task ID</label>
                  <input
                    type="text"
                    required
                    value={newDependencyId}
                    onChange={(e) => setNewDependencyId(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="Enter task ID"
                  />
                </div>
                <button
                  type="submit"
                  className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                >
                  Add Dependency
                </button>
              </form>
            </div>
          )}

          {dependencies.length === 0 ? (
            <p className="text-gray-500">No dependencies</p>
          ) : (
            <div className="space-y-2">
              {dependencies.map((dep) => (
                <div
                  key={dep.id}
                  className="flex justify-between items-center p-3 bg-gray-50 rounded"
                >
                  <span className="text-gray-900">{dep.depends_on_task_title}</span>
                  <button
                    onClick={() => handleRemoveDependency(dep.depends_on_task)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6 mt-6">
        <h2 className="text-xl font-semibold mb-4">Status History</h2>
        {history.length === 0 ? (
          <p className="text-gray-500">No history</p>
        ) : (
          <div className="space-y-2">
            {history.map((entry) => (
              <div
                key={entry.id}
                className="flex justify-between items-center p-3 bg-gray-50 rounded"
              >
                <div>
                  <span className="text-gray-900">
                    {entry.previous_status ? entry.previous_status.replace('_', ' ') : 'None'}
                  </span>
                  <span className="mx-2 text-gray-500">→</span>
                  <span className="text-gray-900">
                    {entry.new_status.replace('_', ' ')}
                  </span>
                </div>
                <div className="text-sm text-gray-500">
                  {entry.changed_by_username} - {new Date(entry.changed_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

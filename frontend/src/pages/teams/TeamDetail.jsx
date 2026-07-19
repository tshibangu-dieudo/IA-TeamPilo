/**
 * Team Detail page component.
 * See .ai/architecture.md: src/pages/ - one folder per screen group.
 * See .ai/coding-rules.md: Tailwind utility classes only.
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { teamsAPI } from '../../api/teams';

export default function TeamDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddMember, setShowAddMember] = useState(false);
  const [newMember, setNewMember] = useState({ user_id: '', role: 'member' });

  useEffect(() => {
    loadTeam();
  }, [id]);

  const loadTeam = async () => {
    try {
      const response = await teamsAPI.get(id);
      setTeam(response.data);
    } catch (err) {
      setError('Failed to load team details');
    } finally {
      setLoading(false);
    }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    try {
      await teamsAPI.createMembership({
        team: id,
        user: newMember.user_id,
        role: newMember.role
      });
      setShowAddMember(false);
      setNewMember({ user_id: '', role: 'member' });
      loadTeam();
    } catch (err) {
      setError('Failed to add member');
    }
  };

  const handleRemoveMember = async (membershipId) => {
    if (!confirm('Are you sure you want to remove this member?')) return;
    
    try {
      await teamsAPI.deleteMembership(membershipId);
      loadTeam();
    } catch (err) {
      setError('Failed to remove member');
    }
  };

  const handleUpdateRole = async (membershipId, newRole) => {
    try {
      await teamsAPI.updateMembership(membershipId, { role: newRole });
      loadTeam();
    } catch (err) {
      setError('Failed to update role');
    }
  };

  if (loading) return <div className="text-center py-8">Loading team details...</div>;

  if (!team) return <div className="text-center py-8">Team not found</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <button
          onClick={() => navigate('/teams')}
          className="text-indigo-600 hover:text-indigo-800 mb-4 inline-block"
        >
          ← Back to Teams
        </button>
        <h1 className="text-3xl font-bold text-gray-900">{team.name}</h1>
        <p className="text-gray-600 mt-2">{team.description || 'No description'}</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Team Members ({team.member_count})</h2>
          <button
            onClick={() => setShowAddMember(!showAddMember)}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
          >
            {showAddMember ? 'Cancel' : 'Add Member'}
          </button>
        </div>

        {showAddMember && (
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <h3 className="font-medium mb-3">Add New Member</h3>
            <form onSubmit={handleAddMember}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">User ID</label>
                  <input
                    type="text"
                    required
                    value={newMember.user_id}
                    onChange={(e) => setNewMember({ ...newMember, user_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="Enter user ID"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
                  <select
                    value={newMember.role}
                    onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="member">Member</option>
                    <option value="lead">Lead</option>
                  </select>
                </div>
              </div>
              <button
                type="submit"
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
              >
                Add Member
              </button>
            </form>
          </div>
        )}

        {team.memberships.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No members yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Joined
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {team.memberships.map((membership) => (
                  <tr key={membership.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {membership.user_username}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{membership.user_email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <select
                        value={membership.role}
                        onChange={(e) => handleUpdateRole(membership.id, e.target.value)}
                        className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      >
                        <option value="member">Member</option>
                        <option value="lead">Lead</option>
                      </select>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">
                        {new Date(membership.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => handleRemoveMember(membership.id)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

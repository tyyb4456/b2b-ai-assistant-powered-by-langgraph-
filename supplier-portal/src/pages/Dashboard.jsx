import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ResponseModal from '../components/modals/ResponseModal';

// Mock API calls - replace with real API
const API_BASE = 'http://localhost:8000/api/v1/supplier';

function SupplierDashboard() {
  const navigate = useNavigate();
  const [pendingRequests, setPendingRequests] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedRequestId, setSelectedRequestId] = useState(null);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('supplier_token');
    if (!token) {
      navigate('/login');
      return;
    }

    // Load user data
    const userData = JSON.parse(localStorage.getItem('supplier_user') || '{}');
    setUser(userData);

    // Fetch dashboard data
    fetchDashboardData();

    // Poll for new requests every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, [navigate]);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('supplier_token');
      
      // Fetch pending requests
      const reqResponse = await fetch(`${API_BASE}/requests/pending`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const reqData = await reqResponse.json();
      setPendingRequests(reqData.data?.pending_requests || []);

      // Fetch unread notifications
      const notifResponse = await fetch(`${API_BASE}/notifications?unread_only=true`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const notifData = await notifResponse.json();
      setNotifications(notifData.data?.notifications || []);

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('supplier_token');
    localStorage.removeItem('supplier_user');
    navigate('/login');
  };

  const handleNotificationClick = (notification) => {
    if (notification.request_id) {
      setSelectedRequestId(notification.request_id);
      setModalOpen(true);
    }
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedRequestId(null);
  };

  const handleModalSuccess = () => {
    // Refresh dashboard data after successful response
    fetchDashboardData();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">S</span>
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">Supplier Portal</h1>
                <p className="text-xs text-gray-500">{user?.full_name}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Notification Bell */}
              <button className="relative p-2 text-gray-600 hover:text-gray-900">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                {notifications.length > 0 && (
                  <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                )}
              </button>

              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatsCard
            title="Pending Requests"
            value={pendingRequests.length}
            icon="📋"
            color="yellow"
          />
          <StatsCard
            title="Unread Notifications"
            value={notifications.length}
            icon="🔔"
            color="blue"
          />
          <StatsCard
            title="Response Rate"
            value="95%"
            icon="✅"
            color="green"
          />
        </div>

        {/* Pending Requests Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Pending Requests
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {pendingRequests.length} request{pendingRequests.length !== 1 ? 's' : ''} awaiting your response
            </p>
          </div>

          <div className="divide-y divide-gray-200">
            {pendingRequests.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <p className="text-gray-500">No pending requests at the moment</p>
              </div>
            ) : (
              pendingRequests.map((request) => (
                <RequestCard
                  key={request.request_id}
                  request={request}
                  onClick={() => navigate(`/requests/${request.request_id}`)}
                />
              ))
            )}
          </div>
        </div>

        {/* Recent Notifications */}
        {notifications.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Recent Notifications
              </h2>
            </div>

            <div className="divide-y divide-gray-200">
              {notifications.slice(0, 5).map((notif) => (
                <NotificationCard 
                  key={notif.notification_id} 
                  notification={notif}
                  onClick={() => handleNotificationClick(notif)}
                />
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Response Modal */}
      <ResponseModal
        requestId={selectedRequestId}
        isOpen={modalOpen}
        onClose={handleModalClose}
        onSuccess={handleModalSuccess}
      />
    </div>
  );
}

// ============================================
// COMPONENTS
// ============================================

function StatsCard({ title, value, icon, color }) {
  const colorClasses = {
    yellow: 'bg-yellow-50 border-yellow-200',
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
  };

  return (
    <div className={`rounded-lg border p-6 ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <div className="text-4xl">{icon}</div>
      </div>
    </div>
  );
}

function RequestCard({ request, onClick }) {
  const priorityColors = {
    low: 'bg-gray-100 text-gray-700',
    medium: 'bg-blue-100 text-blue-700',
    high: 'bg-orange-100 text-orange-700',
    urgent: 'bg-red-100 text-red-700',
  };

  const typeIcons = {
    negotiation: '💬',
    clarification: '❓',
    quote_confirmation: '📄',
  };

  return (
    <div
      onClick={onClick}
      className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl">{typeIcons[request.request_type] || '📋'}</span>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                {request.request_subject}
              </h3>
              <p className="text-xs text-gray-500 mt-1">
                Round {request.conversation_round} • {new Date(request.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <span className={`px-3 py-1 rounded-full text-xs font-medium ${priorityColors[request.priority]}`}>
          {request.priority}
        </span>
      </div>

      {request.expires_at && (
        <div className="mt-3 text-xs text-gray-500">
          ⏰ Expires: {new Date(request.expires_at).toLocaleString()}
        </div>
      )}
    </div>
  );
}

function NotificationCard({ notification, onClick }) {
  return (
    <div 
      onClick={onClick}
      className={`px-6 py-4 ${onClick ? 'hover:bg-blue-50 cursor-pointer transition-colors' : ''}`}
    >
      <div className="flex items-start gap-3">
        <div className="shrink-0 text-2xl">🔔</div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-gray-900">
            {notification.title}
          </h4>
          <p className="text-sm text-gray-600 mt-1">
            {notification.message}
          </p>
          <p className="text-xs text-gray-400 mt-2">
            {new Date(notification.sent_at).toLocaleString()}
          </p>
          {notification.request_id && onClick && (
            <p className="text-xs text-blue-600 font-medium mt-2 flex items-center gap-1">
              📝 Click to respond in modal
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default SupplierDashboard;

import { useNavigate } from 'react-router-dom';
import { useConversations } from '../api/hooks';
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { StatusBadge } from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import { 
  MessageSquare, 
  FileText, 
  DollarSign, 
  TrendingUp,
  Plus,
  ArrowRight,
  Clock,
} from 'lucide-react';
import { formatRelativeTime, formatCurrency, truncate } from '../utils/formatters';
import { INTENT_CONFIG } from '../utils/constants';

export default function Dashboard() {
  const navigate = useNavigate();
  const { data: conversations, isLoading, error } = useConversations({ limit: 10 });

  // Calculate stats
  const stats = {
    totalConversations: conversations?.length || 0,
    quotesGenerated: conversations?.filter(c => c.status === 'quote_generated')?.length || 0,
    inProgress: conversations?.filter(c => c.status === 'in_progress' || c.status === 'paused')?.length || 0,
    negotiations: conversations?.filter(c => c.intent === 'negotiate')?.length || 0,
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Dashboard</h1>
          <p className="text-neutral-600 mt-1">Overview of your procurement activities</p>
        </div>
        <Button
          leftIcon={<Plus size={18} />}
          onClick={() => navigate('/new')}
        >
          New Conversation
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Conversations"
          value={stats.totalConversations}
          icon={<MessageSquare className="text-primary-600" size={24} />}
          color="primary"
        />
        <StatCard
          title="Quotes Generated"
          value={stats.quotesGenerated}
          icon={<FileText className="text-success-600" size={24} />}
          color="success"
        />
        <StatCard
          title="In Progress"
          value={stats.inProgress}
          icon={<Clock className="text-warning-600" size={24} />}
          color="warning"
        />
        <StatCard
          title="Negotiations"
          value={stats.negotiations}
          icon={<TrendingUp className="text-secondary-600" size={24} />}
          color="secondary"
        />
      </div>

      {/* Recent Conversations */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Conversations</CardTitle>
              <CardDescription>Your latest procurement requests</CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              rightIcon={<ArrowRight size={16} />}
              onClick={() => navigate('/history')}
            >
              View All
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {isLoading && (
            <div className="py-12">
              <Spinner text="Loading conversations..." />
            </div>
          )}

          {error && (
            <div className="py-8 text-center">
              <p className="text-error-600">Failed to load conversations</p>
              <p className="text-sm text-neutral-500 mt-1">{error.message}</p>
            </div>
          )}

          {!isLoading && !error && conversations?.length === 0 && (
            <div className="py-12 text-center">
              <MessageSquare className="mx-auto text-neutral-400 mb-4" size={48} />
              <p className="text-neutral-600 mb-4">No conversations yet</p>
              <Button onClick={() => navigate('/new')}>
                Start Your First Conversation
              </Button>
            </div>
          )}

          {!isLoading && !error && conversations && conversations.length > 0 && (
            <div className="space-y-3">
              {conversations.map((conversation) => (
                <ConversationCard
                  key={conversation.thread_id}
                  conversation={conversation}
                  onClick={() => navigate(`/conversation/${conversation.thread_id}`)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Stat Card Component
function StatCard({ title, value, icon, color }) {
  const colorClasses = {
    primary: 'bg-primary-50',
    success: 'bg-success-50',
    warning: 'bg-warning-50',
    secondary: 'bg-secondary-50',
  };

  return (
    <Card className="relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-neutral-600 font-medium">{title}</p>
          <p className="text-3xl font-bold text-neutral-900 mt-2">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
}

// Conversation Card Component
function ConversationCard({ conversation, onClick }) {
  const intentConfig = INTENT_CONFIG[conversation.intent] || { label: conversation.intent, icon: '📝' };

  return (
    <div
      onClick={onClick}
      className="p-4 border border-neutral-200 rounded-lg hover:border-primary-300 hover:bg-primary-50/30 transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">{intentConfig.icon}</span>
            <span className="text-sm font-medium text-neutral-700">{intentConfig.label}</span>
            <StatusBadge status={conversation.status} />
          </div>
          <p className="text-neutral-900 font-medium mb-1">
            {truncate(conversation.preview, 80)}
          </p>
          <p className="text-sm text-neutral-500">
            {formatRelativeTime(conversation.created_at)}
          </p>
        </div>
        <ArrowRight 
          size={20} 
          className="text-neutral-400 group-hover:text-primary-600 transition-colors shrink-0 mt-1" 
        />
      </div>
    </div>
  );
}
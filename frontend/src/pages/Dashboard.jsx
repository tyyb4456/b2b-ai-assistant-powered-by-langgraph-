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

  const stats = {
    totalConversations: conversations?.length || 0,
    quotesGenerated: conversations?.filter(c => c.status === 'quote_generated')?.length || 0,
    inProgress: conversations?.filter(c => c.status === 'in_progress' || c.status === 'paused')?.length || 0,
    negotiations: conversations?.filter(c => c.intent === 'negotiate')?.length || 0,
  };

  return (
    <div className="space-y-10">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-neutral-900 tracking-tight">Dashboard</h1>
          <p className="text-neutral-600 mt-1 text-sm">Overview of your procurement activities</p>
        </div>

        <Button
          leftIcon={<Plus size={18} />}
          onClick={() => navigate('/conversation')}
          className="shadow-sm hover:shadow-md transition-all"
        >
          New Conversation
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Conversations" value={stats.totalConversations} icon={MessageSquare} />
        <StatCard title="Quotes Generated" value={stats.quotesGenerated} icon={FileText} />
        <StatCard title="In Progress" value={stats.inProgress} icon={Clock} />
        <StatCard title="Negotiations" value={stats.negotiations} icon={TrendingUp} />
      </div>

      {/* Recent Conversations */}
      <Card className="rounded-2xl border border-neutral-200 shadow-sm hover:shadow-md transition-all">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="font-semibold text-neutral-900">Recent Conversations</CardTitle>
              <CardDescription className="text-neutral-500">
                Your latest procurement requests
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              rightIcon={<ArrowRight size={16} />}
              onClick={() => navigate('/history')}
              className="text-neutral-600 hover:text-neutral-900"
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
              <p className="text-neutral-700 font-medium">Failed to load conversations</p>
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

function StatCard({ title, value, icon: Icon }) {
  return (
    <Card className="rounded-2xl border border-neutral-200 shadow-sm hover:shadow-md transition-all">
      <div className="flex items-start justify-between p-5">
        <div>
          <p className="text-sm text-neutral-600 font-medium">{title}</p>
          <p className="text-3xl font-semibold text-neutral-900 mt-2">{value}</p>
        </div>
        <div className="p-2 rounded-xl border border-neutral-300 bg-neutral-50">
          <Icon className="text-neutral-700" size={22} />
        </div>
      </div>
    </Card>
  );
}

function ConversationCard({ conversation, onClick }) {
  const intentConfig = INTENT_CONFIG[conversation.intent] || {
    label: conversation.intent,
    icon: '📝'
  };

  return (
    <div
      onClick={onClick}
      className="p-4 border border-neutral-200 rounded-xl hover:border-neutral-400 hover:bg-neutral-50 transition-all cursor-pointer group shadow-sm hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-base">{intentConfig.icon}</span>
            <span className="text-sm font-medium text-neutral-700">{intentConfig.label}</span>
            <StatusBadge status={conversation.status} />
          </div>

          <p className="text-neutral-900 font-medium mb-1">
            {truncate(conversation.preview, 90)}
          </p>

          <p className="text-sm text-neutral-500">
            {formatRelativeTime(conversation.created_at)}
          </p>
        </div>

        <ArrowRight
          size={18}
          className="text-neutral-400 group-hover:text-neutral-700 transition-colors shrink-0 mt-1"
        />
      </div>
    </div>
  );
}

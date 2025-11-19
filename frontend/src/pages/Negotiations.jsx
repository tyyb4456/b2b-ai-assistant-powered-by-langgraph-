import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConversations } from '../api/hooks';
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { StatusBadge } from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import { 
  Handshake,
  ArrowRight,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  MessageSquare,
} from 'lucide-react';
import { formatRelativeTime, truncate } from '../utils/formatters';

export default function Negotiations() {
  const navigate = useNavigate();
  const { data: allConversations, isLoading, error } = useConversations({ limit: 100 });

  // Filter only negotiation conversations
  const negotiations = useMemo(() => {
    if (!allConversations) return [];
    return allConversations.filter(conv => conv.intent === 'negotiate');
  }, [allConversations]);

  // Group by status
  const groupedNegotiations = useMemo(() => {
    return {
      active: negotiations.filter(n => n.status === 'paused' || n.status === 'message_sent'),
      completed: negotiations.filter(n => n.status === 'completed' || n.status === 'quote_generated'),
      failed: negotiations.filter(n => n.status === 'failed'),
    };
  }, [negotiations]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-neutral-900">Negotiations</h1>
        <p className="text-neutral-600 mt-1">Track and manage your ongoing negotiations</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title="Total"
          value={negotiations.length}
          icon={<Handshake size={24} className="text-primary-600" />}
        />
        <StatCard
          title="Active"
          value={groupedNegotiations.active.length}
          icon={<Clock size={24} className="text-warning-600" />}
        />
        <StatCard
          title="Completed"
          value={groupedNegotiations.completed.length}
          icon={<CheckCircle size={24} className="text-success-600" />}
        />
        <StatCard
          title="Failed"
          value={groupedNegotiations.failed.length}
          icon={<XCircle size={24} className="text-error-600" />}
        />
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="py-12">
          <Spinner text="Loading negotiations..." />
        </div>
      )}

      {/* Error */}
      {error && (
        <Card>
          <CardContent>
            <div className="text-center py-8">
              <p className="text-error-600">Failed to load negotiations</p>
              <p className="text-sm text-neutral-500 mt-1">{error.message}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !error && negotiations.length === 0 && (
        <Card>
          <CardContent>
            <div className="text-center py-12">
              <Handshake className="mx-auto text-neutral-400 mb-4" size={48} />
              <p className="text-neutral-600 mb-2">No negotiations yet</p>
              <p className="text-sm text-neutral-500 mb-4">
                Start negotiating with suppliers to get better deals
              </p>
              <Button onClick={() => navigate('/new')}>
                Start a Negotiation
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Negotiations */}
      {!isLoading && !error && groupedNegotiations.active.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Negotiations</CardTitle>
            <CardDescription>
              {groupedNegotiations.active.length} negotiation(s) in progress
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {groupedNegotiations.active.map(negotiation => (
                <NegotiationCard
                  key={negotiation.thread_id}
                  negotiation={negotiation}
                  onClick={() => navigate(`/conversation/${negotiation.thread_id}`)}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Completed Negotiations */}
      {!isLoading && !error && groupedNegotiations.completed.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Completed Negotiations</CardTitle>
            <CardDescription>
              {groupedNegotiations.completed.length} successful negotiation(s)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {groupedNegotiations.completed.map(negotiation => (
                <NegotiationCard
                  key={negotiation.thread_id}
                  negotiation={negotiation}
                  onClick={() => navigate(`/conversation/${negotiation.thread_id}`)}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Stat Card
function StatCard({ title, value, icon }) {
  return (
    <Card>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-neutral-600 font-medium">{title}</p>
            <p className="text-3xl font-bold text-neutral-900 mt-2">{value}</p>
          </div>
          <div className="p-3 rounded-lg bg-neutral-100">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Negotiation Card
function NegotiationCard({ negotiation, onClick }) {
  return (
    <div
      onClick={onClick}
      className="p-4 border border-neutral-200 rounded-lg hover:border-primary-300 hover:bg-primary-50/30 transition-all cursor-pointer group"
    >
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-lg bg-secondary-100 flex items-center justify-center text-2xl shrink-0">
          🤝
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <StatusBadge status={negotiation.status} />
            {negotiation.status === 'paused' && (
              <span className="text-xs text-warning-600 font-medium">
                Waiting for supplier response
              </span>
            )}
          </div>
          <p className="text-neutral-900 font-medium mb-1">
            {truncate(negotiation.preview, 100)}
          </p>
          <p className="text-sm text-neutral-500">
            {formatRelativeTime(negotiation.created_at)}
          </p>
        </div>

        <ArrowRight 
          size={20} 
          className="text-neutral-400 group-hover:text-primary-600 transition-colors shrink-0 mt-2" 
        />
      </div>
    </div>
  );
}
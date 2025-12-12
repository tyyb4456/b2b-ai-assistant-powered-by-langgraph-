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
  Clock,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { formatRelativeTime, truncate } from '../utils/formatters';

export default function Negotiations() {
  const navigate = useNavigate();
  const { data: allConversations, isLoading, error } = useConversations({ limit: 100 });

  const negotiations = useMemo(() => {
    if (!allConversations) return [];
    return allConversations.filter(conv => conv.intent === 'negotiate');
  }, [allConversations]);

  const groupedNegotiations = useMemo(() => {
    return {
      active: negotiations.filter(n => n.status === 'paused' || n.status === 'message_sent'),
      completed: negotiations.filter(n => n.status === 'completed' || n.status === 'quote_generated'),
      failed: negotiations.filter(n => n.status === 'failed'),
    };
  }, [negotiations]);

  return (
    <div className="space-y-10">

      {/* Header */}
      <header className="space-y-1">
        <h1 className="text-3xl font-semibold text-neutral-900 tracking-tight">Negotiations</h1>
        <p className="text-neutral-600 text-sm">Review and manage supplier negotiations effortlessly</p>
      </header>

      {/* Stats */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title="Total"
          value={negotiations.length}
          icon={<Handshake size={22} />}
        />
        <StatCard
          title="Active"
          value={groupedNegotiations.active.length}
          icon={<Clock size={22} />}
        />
        <StatCard
          title="Completed"
          value={groupedNegotiations.completed.length}
          icon={<CheckCircle size={22} />}
        />
        <StatCard
          title="Failed"
          value={groupedNegotiations.failed.length}
          icon={<XCircle size={22} />}
        />
      </section>

      {/* Loading */}
      {isLoading && (
        <div className="py-16">
          <Spinner text="Loading negotiations..." />
        </div>
      )}

      {/* Error */}
      {error && (
        <Card>
          <CardContent>
            <div className="text-center py-8">
              <p className="text-error-600 font-medium">Failed to load negotiations</p>
              <p className="text-sm text-neutral-500 mt-1">{error.message}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !error && negotiations.length === 0 && (
        <Card>
          <CardContent>
            <div className="text-center py-16 space-y-4">
              <div className="w-14 h-14 mx-auto rounded-xl bg-neutral-100 flex items-center justify-center text-neutral-500">
                <Handshake size={32} />
              </div>
              <p className="text-neutral-700 font-medium">No negotiations yet</p>
              <p className="text-sm text-neutral-500">
                Start negotiating with suppliers to secure better deals.
              </p>
              <Button onClick={() => navigate('/conversation')} className="mt-2">
                Start Negotiation
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active */}
      {groupedNegotiations.active.length > 0 && (
        <NegotiationSection
          title="Active Negotiations"
          subtitle={`${groupedNegotiations.active.length} ongoing`}
          list={groupedNegotiations.active}
          navigate={navigate}
        />
      )}

      {/* Completed */}
      {groupedNegotiations.completed.length > 0 && (
        <NegotiationSection
          title="Completed Negotiations"
          subtitle={`${groupedNegotiations.completed.length} completed`}
          list={groupedNegotiations.completed}
          navigate={navigate}
        />
      )}
    </div>
  );
}


/** Reusable Section Wrapper */
function NegotiationSection({ title, subtitle, list, navigate }) {
  return (
    <Card className="shadow-sm border border-neutral-200/70">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{subtitle}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {list.map(item => (
            <NegotiationCard
              key={item.thread_id}
              negotiation={item}
              onClick={() => navigate(`/conversation/${item.thread_id}`)}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/** Stat Card */
function StatCard({ title, value, icon }) {
  return (
    <Card className="shadow-sm border border-neutral-200">
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-neutral-600 text-sm">{title}</p>
            <p className="text-3xl font-semibold text-neutral-900 mt-1">{value}</p>
          </div>
          <div className="p-3 rounded-xl bg-neutral-100 text-neutral-600">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/** Negotiation Card */
function NegotiationCard({ negotiation, onClick }) {
  return (
    <div
      onClick={onClick}
      className="
        p-4 rounded-xl border border-neutral-200 hover:border-neutral-400 
        hover:bg-neutral-50 transition-all cursor-pointer group flex items-start gap-4
      "
    >
      <div className="w-12 h-12 rounded-xl bg-neutral-100 flex items-center justify-center text-neutral-600">
        🤝
      </div>

      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <StatusBadge status={negotiation.status} />
        </div>

        <p className="text-neutral-900 font-medium mb-1">
          {truncate(negotiation.preview, 90)}
        </p>

        <p className="text-sm text-neutral-500">{formatRelativeTime(negotiation.created_at)}</p>
      </div>

      <ArrowRight
        size={18}
        className="text-neutral-400 group-hover:text-neutral-700 transition-colors mt-2"
      />
    </div>
  );
}

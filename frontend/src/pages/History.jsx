import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConversations } from '../api/hooks';
import Card, { CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { StatusBadge } from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import {
  Search,
  ArrowRight,
  Calendar,
  MessageSquare,
} from 'lucide-react';
import { formatDateTime, truncate } from '../utils/formatters';
import { INTENT_CONFIG, STATUS_CONFIG } from '../utils/constants';

export default function History() {
  const navigate = useNavigate();
  const { data: conversations, isLoading, error } = useConversations({ limit: 100 });

  const [searchQuery, setSearchQuery] = useState('');
  const [filterIntent, setFilterIntent] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  // Filter and search conversations
  const filteredConversations = useMemo(() => {
    if (!conversations) return [];

    return conversations.filter(conv => {
      const matchesSearch = searchQuery === '' ||
        conv.preview?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.thread_id.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesIntent = filterIntent === 'all' || conv.intent === filterIntent;
      const matchesStatus = filterStatus === 'all' || conv.status === filterStatus;

      return matchesSearch && matchesIntent && matchesStatus;
    });
  }, [conversations, searchQuery, filterIntent, filterStatus]);

  const availableIntents = useMemo(() => {
    if (!conversations) return [];
    return [...new Set(conversations.map(c => c.intent).filter(Boolean))];
  }, [conversations]);

  const availableStatuses = useMemo(() => {
    if (!conversations) return [];
    return [...new Set(conversations.map(c => c.status).filter(Boolean))];
  }, [conversations]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Conversation History</h1>
          <p className="text-neutral-600 mt-1">View and manage all your conversations</p>
        </div>
      </div>

      {/* Search & Filters */}
      <Card>
        <CardContent>
          <div className="flex flex-col md:flex-row md:items-center gap-4">
            <Input
              placeholder="Search conversations..."
              leftIcon={<Search size={18} />}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1"
            />

            <select
              value={filterIntent}
              onChange={(e) => setFilterIntent(e.target.value)}
              className="input-base w-full md:w-48"
            >
              <option value="all">All Intents</option>
              {availableIntents.map(intent => (
                <option key={intent} value={intent}>
                  {INTENT_CONFIG[intent]?.label || intent}
                </option>
              ))}
            </select>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input-base w-full md:w-48"
            >
              <option value="all">All Statuses</option>
              {availableStatuses.map(status => (
                <option key={status} value={status}>
                  {STATUS_CONFIG[status]?.label || status}
                </option>
              ))}
            </select>
          </div>

          {!isLoading && conversations && (
            <p className="text-sm text-neutral-600 mt-4">
              Showing {filteredConversations.length} of {conversations.length} conversations
            </p>
          )}
        </CardContent>
      </Card>

      {/* Content */}
      <div className="space-y-4">
        {isLoading && (
          <div className="py-12 flex justify-center">
            <Spinner text="Loading conversations..." />
          </div>
        )}

        {error && (
          <Card>
            <CardContent>
              <div className="text-center py-8">
                <p className="text-error-600">Failed to load conversations</p>
                <p className="text-sm text-neutral-500 mt-1">{error.message}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {!isLoading && !error && filteredConversations.length === 0 && (
          <Card>
            <CardContent>
              <div className="text-center py-12">
                <MessageSquare className="mx-auto text-neutral-400 mb-4" size={48} />
                <p className="text-neutral-600 mb-2">No conversations found</p>
                {(searchQuery || filterIntent !== 'all' || filterStatus !== 'all') ? (
                  <p className="text-sm text-neutral-500">Try adjusting your filters</p>
                ) : (
                  <Button onClick={() => navigate('/new')} className="mt-8">
                    Start a Conversation
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {!isLoading && !error && filteredConversations.length > 0 && (
          <div className="grid gap-3 md:grid-cols-1 lg:grid-cols-2">
            {filteredConversations.map(conv => (
              <ConversationRow
                key={conv.thread_id}
                conversation={conv}
                onClick={() => navigate(`/conversation/${conv.thread_id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Conversation Row Component
function ConversationRow({ conversation, onClick }) {
  const navigate = useNavigate();
  const intentConfig = INTENT_CONFIG[conversation.intent] || { label: conversation.intent, icon: '📝' };

  return (
    <Card hoverable>
      <CardContent>
        <div
          onClick={onClick}
          className="flex items-center gap-4 cursor-pointer hover:bg-gray-50 p-2 rounded transition"
        >
          {/* Icon */}
          <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center text-2xl shrink-0">
            {intentConfig.icon}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-medium text-neutral-700">{intentConfig.label}</span>
              <StatusBadge status={conversation.status} />
            </div>
            <p className="text-neutral-900 font-medium mb-1">
              {truncate(conversation.preview, 100)}
            </p>
            <div className="flex items-center gap-4 text-xs text-neutral-500">
              <span className="flex items-center gap-1">
                <Calendar size={12} />
                {formatDateTime(conversation.created_at)}
              </span>
              <span className="font-mono">{conversation.thread_id.split('_').pop()}</span>
            </div>
          </div>

          {/* Arrow */}
          <ArrowRight
            size={20}
            className="text-neutral-400 shrink-0"
          />
        </div>
      </CardContent>
    </Card>
  );
}

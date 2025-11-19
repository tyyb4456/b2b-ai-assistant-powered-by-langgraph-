import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import * as api from '../../api/endpoints';
import Card, { CardHeader, CardTitle, CardContent } from '../ui/Card';
import Button from '../ui/Button';
import { Textarea } from '../ui/Input';
import { 
  Send, 
  Loader2, 
  CheckCircle, 
  Package,
  Building2,
  FileText,
  MessageSquare,
  Zap,
} from 'lucide-react';

export default function StreamingConversation({ initialInput = '', recipientEmail = '' }) {
  const navigate = useNavigate();
  const [userInput, setUserInput] = useState(initialInput);
  const [isStreaming, setIsStreaming] = useState(false);
  const [events, setEvents] = useState([]);
  const [threadId, setThreadId] = useState(null);
  const [currentNode, setCurrentNode] = useState('');
  const cleanupRef = useRef(null);

  const handleStart = () => {
    if (!userInput.trim()) return;

    setIsStreaming(true);
    setEvents([]);
    setCurrentNode('Starting...');

    const cleanup = api.startConversationStream(
      {
        userInput,
        recipientEmail: recipientEmail || null,
        channel: 'web',
      },
      // onEvent
      (event) => {
        console.log('SSE Event:', event);
        setEvents(prev => [...prev, event]);

        if (event.type === 'connected') {
          setThreadId(event.data.thread_id);
          setCurrentNode('Connected');
        } else if (event.type === 'node_progress') {
          setCurrentNode(event.data.node);
        } else if (event.type === 'workflow_complete') {
          setCurrentNode('Completed');
          setThreadId(event.data.thread_id);
        }
      },
      // onComplete
      (data) => {
        setIsStreaming(false);
        setCurrentNode('Completed');
        
        // Navigate to detail page after a short delay
        setTimeout(() => {
          if (data.thread_id) {
            navigate(`/conversation/${data.thread_id}`);
          }
        }, 1500);
      },
      // onError
      (error) => {
        console.error('Stream error:', error);
        setIsStreaming(false);
        setCurrentNode('Error');
        setEvents(prev => [...prev, { type: 'error', data: error }]);
      }
    );

    cleanupRef.current = cleanup;
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (cleanupRef.current) {
        cleanupRef.current();
      }
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Input Form */}
      {!isStreaming && events.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap size={20} className="text-primary-600" />
              Real-Time Processing
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Textarea
                placeholder="Enter your procurement request..."
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                rows={4}
              />
              <Button
                onClick={handleStart}
                leftIcon={<Send size={18} />}
                fullWidth
                disabled={!userInput.trim()}
              >
                Start with Real-Time Updates
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Live Progress */}
      {isStreaming && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 size={20} className="animate-spin text-primary-600" />
              Processing Your Request
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Current Node */}
              <div className="p-4 bg-primary-50 border border-primary-200 rounded-lg">
                <p className="text-sm font-medium text-primary-900">
                  Current Step: {currentNode}
                </p>
              </div>

              {/* Event Timeline */}
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {events.map((event, index) => (
                  <EventCard key={index} event={event} />
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Completion */}
      {!isStreaming && events.length > 0 && (
        <Card>
          <CardContent>
            <div className="text-center py-8">
              <CheckCircle size={48} className="mx-auto text-success-600 mb-4" />
              <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                Processing Complete!
              </h3>
              <p className="text-neutral-600 mb-4">
                Redirecting to conversation details...
              </p>
              {threadId && (
                <Button onClick={() => navigate(`/conversation/${threadId}`)}>
                  View Details
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Event Card Component
function EventCard({ event }) {
  const getEventIcon = (type) => {
    switch (type) {
      case 'connected':
        return <CheckCircle size={16} className="text-success-600" />;
      case 'message':
        return <MessageSquare size={16} className="text-primary-600" />;
      case 'parameters_extracted':
        return <Package size={16} className="text-secondary-600" />;
      case 'suppliers_found':
        return <Building2 size={16} className="text-warning-600" />;
      case 'quote_generated':
        return <FileText size={16} className="text-success-600" />;
      case 'node_progress':
        return <Loader2 size={16} className="animate-spin text-primary-600" />;
      case 'error':
        return <span className="text-error-600">❌</span>;
      default:
        return <span>ℹ️</span>;
    }
  };

  const getEventTitle = (type) => {
    switch (type) {
      case 'connected':
        return 'Connected';
      case 'message':
        return 'Message';
      case 'parameters_extracted':
        return 'Parameters Extracted';
      case 'suppliers_found':
        return 'Suppliers Found';
      case 'quote_generated':
        return 'Quote Generated';
      case 'node_progress':
        return `Progress: ${event.data.node}`;
      case 'workflow_complete':
        return 'Workflow Complete';
      case 'error':
        return 'Error';
      default:
        return type;
    }
  };

  return (
    <div className="flex items-start gap-3 p-3 bg-neutral-50 rounded-lg border border-neutral-200">
      <div className="mt-0.5">{getEventIcon(event.type)}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-neutral-900">
          {getEventTitle(event.type)}
        </p>
        {event.data.message && (
          <p className="text-sm text-neutral-600 mt-1">
            {event.data.message}
          </p>
        )}
        {event.data.count && (
          <p className="text-sm text-neutral-600 mt-1">
            Found {event.data.count} suppliers
          </p>
        )}
        {event.data.quote_id && (
          <p className="text-xs text-neutral-500 mt-1 font-mono">
            {event.data.quote_id}
          </p>
        )}
      </div>
    </div>
  );
}
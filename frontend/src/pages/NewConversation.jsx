import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStartConversation } from '../api/hooks';
import * as api from '../api/endpoints';
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input, { Textarea } from '../components/ui/Input';
import { 
  Send, 
  Sparkles, 
  Mail, 
  ArrowLeft, 
  Zap,
  Loader2,
  CheckCircle,
  Package,
  Building2,
  FileText,
  MessageSquare,
  Clock,
  Target,
} from 'lucide-react';
import { QUICK_TEMPLATES } from '../utils/constants';

export default function NewConversation() {
  const navigate = useNavigate();
  const startConversation = useStartConversation();

  const [formData, setFormData] = useState({
    userInput: '',
    recipientEmail: '',
  });

  const [errors, setErrors] = useState({});
  const [useStreaming, setUseStreaming] = useState(true);

  // ✅ Consolidated streaming state
  const [streamState, setStreamState] = useState({
    isStreaming: false,
    events: [],
    currentNode: '',
    threadId: null,
  });

  const cleanupRef = useRef(null);
  const eventsEndRef = useRef(null);

  // Auto-scroll to latest event
  useEffect(() => {
    if (streamState.events.length > 0) {
      eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [streamState.events.length]);

  // Validate form
  const validate = () => {
    const newErrors = {};

    if (!formData.userInput.trim()) {
      newErrors.userInput = 'Please enter your message';
    }

    if (formData.recipientEmail && !isValidEmail(formData.recipientEmail)) {
      newErrors.recipientEmail = 'Please enter a valid email address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle regular submit (non-streaming)
  const handleRegularSubmit = async () => {
    if (!validate()) return;

    try {
      const result = await startConversation.mutateAsync({
        userInput: formData.userInput,
        recipientEmail: formData.recipientEmail || null,
        channel: 'web',
      });

      navigate(`/conversation/${result.thread_id}`);
    } catch (error) {
      console.error('Failed to start conversation:', error);
    }
  };

  // ✅ FIXED: Removed useCallback to avoid stale closures
  const handleStreamingSubmit = () => {
    if (!validate()) return;

    console.log('[Frontend] 🚀 Starting streaming conversation');
    
    // Reset state
    setStreamState({
      isStreaming: true,
      events: [],
      currentNode: 'Initializing...',
      threadId: null,
    });

    const cleanup = api.startConversationStream(
      {
        userInput: formData.userInput,
        recipientEmail: formData.recipientEmail || null,
        channel: 'web',
      },
      // ✅ UPDATED: onEvent callback for simplified format
      (event) => {
        console.log('[Frontend] ✅ Event received:', event);
        
        // 🔥 FIX: event.data now contains everything including type
        const eventType = event.type || event.data?.type || 'message';
        const eventData = event.data;
        
        setStreamState(prev => {
          const newEvents = [...prev.events, { type: eventType, data: eventData }];
          let newNode = prev.currentNode;
          let newThreadId = prev.threadId;

          // Update current node based on event type
          switch (eventType) {
            case 'connected':
              newNode = '✅ Connected';
              newThreadId = eventData.thread_id || newThreadId;
              break;
            case 'node_progress':
              newNode = `⚙️ ${formatNodeName(eventData.node || 'Processing')}`;
              break;
            case 'intent_classified':
              newNode = `🎯 Intent: ${eventData.intent || 'Unknown'}`;
              break;
            case 'parameters_extracted':
              newNode = '📋 Parameters Extracted';
              break;
            case 'suppliers_found':
              newNode = `🏢 Found ${eventData.count || 0} Suppliers`;
              break;
            case 'quote_generated':
              newNode = '📄 Quote Generated';
              break;
            case 'message':
              newNode = `💬 ${formatNodeName(eventData.node || 'Message')}`;
              break;
            case 'workflow_complete':
              newNode = '✅ Completed';
              newThreadId = eventData.thread_id || newThreadId;
              break;
            case 'error':
              newNode = '❌ Error';
              break;
          }

          console.log('[Frontend] 📊 State update - Events:', newEvents.length, 'Node:', newNode);

          return {
            ...prev,
            events: newEvents,
            currentNode: newNode,
            threadId: newThreadId,
          };
        });
      },
      // onComplete - no changes needed
      (data) => {
        console.log('[Frontend] ✅ Stream completed', data);
        
        setStreamState(prev => ({
          ...prev,
          isStreaming: false,
          currentNode: '✅ Processing Complete',
        }));
        
        setTimeout(() => {
          setStreamState(prev => {
            const finalThreadId = data.thread_id || prev.threadId;
            if (finalThreadId) {
              console.log('[Frontend] 🚀 Navigating to:', finalThreadId);
              navigate(`/conversation/${finalThreadId}`);
            }
            return prev;
          });
        }, 1500);
      },
      // onError - no changes needed
      (error) => {
        console.error('[Frontend] ❌ Error:', error);
        
        setStreamState(prev => ({
          ...prev,
          isStreaming: false,
          currentNode: '❌ Error occurred',
          events: [...prev.events, { 
            type: 'error', 
            data: { error: error.message } 
          }],
        }));
      }
    );

    cleanupRef.current = cleanup;
  };

  // // Cleanup on unmount
  // useEffect(() => {
  //   return () => {
  //     if (cleanupRef.current) {
  //       console.log('[Frontend] 🧹 Cleanup');
  //       cleanupRef.current();
  //     }
  //   };
  // }, []);

  // Apply template
  const applyTemplate = (template) => {
    setFormData(prev => ({
      ...prev,
      userInput: template,
    }));
    setErrors(prev => ({ ...prev, userInput: undefined }));
  };

  // Format node names
  const formatNodeName = (nodeName) => {
    return nodeName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        leftIcon={<ArrowLeft size={16} />}
        onClick={() => navigate('/')}
      >
        Back to Dashboard
      </Button>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-neutral-900">New Conversation</h1>
        <p className="text-neutral-600 mt-1">
          Start a new procurement conversation with our AI assistant
        </p>
      </div>

      {/* Streaming Toggle */}
      {!streamState.isStreaming && streamState.events.length === 0 && (
        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Zap size={20} className={useStreaming ? 'text-primary-600' : 'text-neutral-400'} />
                <div>
                  <p className="font-medium text-neutral-900">Real-Time Processing</p>
                  <p className="text-sm text-neutral-600">
                    See live progress as your request is processed
                  </p>
                </div>
              </div>
              <button
                onClick={() => setUseStreaming(!useStreaming)}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${useStreaming ? 'bg-primary-600' : 'bg-neutral-300'}
                `}
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${useStreaming ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Form */}
        <div className="lg:col-span-2">
          {/* Input Form */}
          {!streamState.isStreaming && streamState.events.length === 0 && (
            <Card>
              <CardHeader>
                <CardTitle>What do you need?</CardTitle>
                <CardDescription>
                  Describe your procurement request in detail
                </CardDescription>
              </CardHeader>

              <CardContent>
                <div className="space-y-6">
                  <Textarea
                    label="Your Message"
                    placeholder="I need a quote for 5,000 meters of organic cotton canvas..."
                    value={formData.userInput}
                    onChange={(e) => {
                      setFormData({ ...formData, userInput: e.target.value });
                      setErrors({ ...errors, userInput: undefined });
                    }}
                    error={errors.userInput}
                    rows={6}
                  />

                  <Input
                    label="Recipient Email (Optional)"
                    type="email"
                    placeholder="buyer@company.com"
                    leftIcon={<Mail size={18} />}
                    value={formData.recipientEmail}
                    onChange={(e) => {
                      setFormData({ ...formData, recipientEmail: e.target.value });
                      setErrors({ ...errors, recipientEmail: undefined });
                    }}
                    error={errors.recipientEmail}
                    helperText="We'll send the quote to this email address"
                  />

                  <div className="flex items-center gap-3">
                    <Button
                      onClick={useStreaming ? handleStreamingSubmit : handleRegularSubmit}
                      loading={startConversation.isPending}
                      leftIcon={useStreaming ? <Zap size={18} /> : <Send size={18} />}
                      fullWidth
                    >
                      {useStreaming ? 'Start with Live Updates' : 'Start Conversation'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => navigate('/')}
                      disabled={startConversation.isPending}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Streaming Progress */}
          {streamState.isStreaming && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Loader2 size={20} className="animate-spin text-primary-600" />
                  Processing Your Request
                </CardTitle>
                <CardDescription>
                  Watch your request being processed in real-time
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Current Step */}
                  <div className="p-4 bg-linear-to-r from-primary-50 to-secondary-50 border border-primary-200 rounded-lg shadow-sm">
                    <div className="flex items-center gap-3">
                      <Loader2 size={20} className="animate-spin text-primary-600" />
                      <div>
                        <p className="text-xs font-medium text-primary-700 uppercase tracking-wide">
                          Current Step
                        </p>
                        <p className="text-lg font-bold text-primary-900 mt-1">
                          {streamState.currentNode}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Event Timeline */}
                  <div className="space-y-2 max-h-96 overflow-y-auto bg-neutral-50 rounded-lg p-4 border border-neutral-200">
                    {streamState.events.length === 0 ? (
                      <div className="text-center py-8 text-neutral-500">
                        <Loader2 size={32} className="animate-spin mx-auto mb-3 text-neutral-400" />
                        <p className="text-sm">Waiting for events...</p>
                      </div>
                    ) : (
                      <>
                        {streamState.events.map((event, index) => (
                          <StreamEventCard 
                            key={`event-${index}`}
                            event={event} 
                            index={index} 
                          />
                        ))}
                        <div ref={eventsEndRef} />
                      </>
                    )}
                  </div>

                  {/* Event counter */}
                  <div className="flex justify-between text-xs text-neutral-500">
                    <span>{streamState.events.length} event{streamState.events.length !== 1 ? 's' : ''} received</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Completion Screen */}
          {!streamState.isStreaming && streamState.events.length > 0 && (
            <Card>
              <CardContent>
                <div className="text-center py-12">
                  <CheckCircle size={64} className="mx-auto text-success-600 mb-4" />
                  <h3 className="text-2xl font-bold text-neutral-900 mb-2">
                    Processing Complete!
                  </h3>
                  <p className="text-neutral-600 mb-6">
                    Your request has been processed successfully
                  </p>
                  <p className="text-sm text-neutral-500 mb-4">
                    Processed {streamState.events.length} events
                  </p>
                  {streamState.threadId && (
                    <div className="space-y-3">
                      <p className="text-sm text-neutral-500 font-mono">
                        Thread ID: {streamState.threadId}
                      </p>
                      <Button 
                        onClick={() => navigate(`/conversation/${streamState.threadId}`)}
                        leftIcon={<FileText size={18} />}
                      >
                        View Conversation Details
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Templates Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles size={18} className="text-primary-600" />
                Quick Templates
              </CardTitle>
              <CardDescription>
                Click to use a template
              </CardDescription>
            </CardHeader>

            <CardContent>
              <div className="space-y-2">
                {QUICK_TEMPLATES.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => applyTemplate(template.template)}
                    disabled={streamState.isStreaming}
                    className="w-full text-left p-3 rounded-lg border border-neutral-200 hover:border-primary-300 hover:bg-primary-50/30 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <p className="text-sm font-medium text-neutral-900 mb-1">
                      {template.title}
                    </p>
                    <p className="text-xs text-neutral-500 line-clamp-2">
                      {template.template}
                    </p>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function StreamEventCard({ event, index }) {
  // 🔥 FIX: Extract type and data correctly
  const eventType = event.type;
  const eventData = event.data || {};
  
  const getEventIcon = (type) => {
    switch (type) {
      case 'connected':
        return <CheckCircle size={20} className="text-success-600" />;
      case 'message':
        return <MessageSquare size={20} className="text-primary-600" />;
      case 'intent_classified':
        return <Target size={20} className="text-secondary-600" />;
      case 'parameters_extracted':
        return <Package size={20} className="text-secondary-600" />;
      case 'suppliers_found':
        return <Building2 size={20} className="text-warning-600" />;
      case 'quote_generated':
        return <FileText size={20} className="text-success-600" />;
      case 'node_progress':
        return <Clock size={20} className="text-primary-600" />;
      case 'workflow_complete':
        return <CheckCircle size={20} className="text-success-600" />;
      case 'error':
        return <span className="text-error-600 text-xl">❌</span>;
      default:
        return <span className="text-lg">ℹ️</span>;
    }
  };

  const getEventTitle = (type, data) => {
    switch (type) {
      case 'connected':
        return 'Connection Established';
      case 'message':
        return 'Message Received';
      case 'intent_classified':
        return `Intent: ${data.intent || 'Unknown'}`;
      case 'parameters_extracted':
        return 'Parameters Extracted';
      case 'suppliers_found':
        return `Found ${data.count || 0} Suppliers`;
      case 'quote_generated':
        return 'Quote Generated';
      case 'node_progress':
        return formatNodeName(data.node || 'Processing');
      case 'workflow_complete':
        return 'Workflow Complete ✅';
      case 'error':
        return 'Error Occurred';
      default:
        return type;
    }
  };

  const formatNodeName = (nodeName) => {
    return nodeName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="flex items-start gap-3 p-4 bg-white rounded-lg border border-neutral-200 shadow-sm animate-slideIn">
      <div className="shrink-0 mt-0.5">
        {getEventIcon(eventType)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between mb-1">
          <p className="text-sm font-semibold text-neutral-900">
            {getEventTitle(eventType, eventData)}
          </p>
          <span className="text-xs text-neutral-400 ml-2">#{index + 1}</span>
        </div>
        
        {eventData.content && (
          <p className="text-sm text-neutral-600 mb-2 line-clamp-3">
            {eventData.content}
          </p>
        )}
        
        {eventType === 'intent_classified' && eventData.confidence && (
          <p className="text-xs text-primary-600 font-medium">
            Confidence: {(eventData.confidence * 100).toFixed(0)}%
          </p>
        )}
        
        {eventType === 'parameters_extracted' && eventData.parameters && (
          <div className="mt-2 p-2 bg-neutral-50 rounded border border-neutral-200">
            <p className="text-xs text-neutral-600 font-medium mb-1">Extracted:</p>
            <div className="flex flex-wrap gap-2">
              {eventData.parameters.fabric_type && (
                <span className="px-2 py-0.5 bg-secondary-100 text-secondary-700 text-xs rounded-full">
                  {eventData.parameters.fabric_type}
                </span>
              )}
              {eventData.parameters.quantity && (
                <span className="px-2 py-0.5 bg-secondary-100 text-secondary-700 text-xs rounded-full">
                  {eventData.parameters.quantity} {eventData.parameters.unit}
                </span>
              )}
            </div>
          </div>
        )}
        
        {eventType === 'suppliers_found' && eventData.suppliers && (
          <div className="mt-2">
            <p className="text-xs text-neutral-600 mb-1">Top suppliers:</p>
            <div className="flex flex-wrap gap-1">
              {eventData.suppliers.slice(0, 3).map((supplier, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-warning-100 text-warning-700 text-xs rounded-full">
                  {supplier.name}
                </span>
              ))}
            </div>
          </div>
        )}
        
        {eventData.quote_id && (
          <p className="text-xs text-neutral-500 font-mono mt-1">
            Quote: {eventData.quote_id}
          </p>
        )}
        
        {eventData.estimated_savings && (
          <p className="text-xs text-success-600 font-medium mt-1">
            💰 Potential Savings: {eventData.estimated_savings}%
          </p>
        )}
        
        {eventType === 'error' && eventData.error && (
          <p className="text-sm text-error-600 mt-1">
            {eventData.error}
          </p>
        )}
      </div>
    </div>
  );
}

function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}
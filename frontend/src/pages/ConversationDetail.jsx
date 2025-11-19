import { useParams, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useConversationComprehensive, useContinueConversation, useResumeConversation } from '../api/hooks';
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { StatusBadge } from '../components/ui/Badge';
import Spinner from '../components/ui/Spinner';
import { Textarea } from '../components/ui/Input';
import {
  ArrowLeft,
  Download,
  MessageSquare,
  Calendar,
  Package,
  DollarSign,
  Clock,
  Building2,
  Award,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { formatDateTime, formatCurrency, formatLeadTime, formatNumber, truncate } from '../utils/formatters';
import { INTENT_CONFIG } from '../utils/constants';

export default function ConversationDetail() {
  const { threadId } = useParams();
  const navigate = useNavigate();
  
  // Use COMPREHENSIVE endpoint
  const { data: conversation, isLoading, error, refetch } = useConversationComprehensive(threadId);
  const continueConversation = useContinueConversation();
  const resumeConversation = useResumeConversation();

  const [showContinueForm, setShowContinueForm] = useState(false);
  const [showResumeForm, setShowResumeForm] = useState(false);
  const [continueInput, setContinueInput] = useState('');
  const [resumeInput, setResumeInput] = useState('');

  // Handle continue conversation
  const handleContinue = async () => {
    if (!continueInput.trim()) return;

    try {
      await continueConversation.mutateAsync({
        threadId,
        userInput: continueInput,
      });
      setContinueInput('');
      setShowContinueForm(false);
      refetch();
    } catch (error) {
      console.error('Failed to continue:', error);
    }
  };

  // Handle resume conversation
  const handleResume = async () => {
    if (!resumeInput.trim()) return;

    try {
      await resumeConversation.mutateAsync({
        threadId,
        supplierResponse: resumeInput,
      });
      setResumeInput('');
      setShowResumeForm(false);
      refetch();
    } catch (error) {
      console.error('Failed to resume:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="py-12">
        <Spinner size="lg" text="Loading conversation details..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto py-12">
        <Card>
          <CardContent>
            <div className="text-center py-8">
              <AlertCircle size={48} className="mx-auto text-error-600 mb-4" />
              <p className="text-error-600 text-lg font-medium mb-2">Failed to load conversation</p>
              <p className="text-neutral-600 mb-4">{error.message}</p>
              <div className="flex gap-3 justify-center">
                <Button onClick={() => navigate('/')}>Back to Dashboard</Button>
                <Button variant="outline" onClick={() => refetch()}>Try Again</Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Safe access to properties with defaults
  const status = conversation?.status || 'unknown';
  const intent = conversation?.intent || 'unknown';
  const isPaused = conversation?.is_paused || false;
  const intentConfig = INTENT_CONFIG[intent] || { label: intent, icon: '📝' };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Back Button */}
      <Button
        variant="ghost"
        size="sm"
        leftIcon={<ArrowLeft size={16} />}
        onClick={() => navigate('/')}
      >
        Back to Dashboard
      </Button>

      {/* Header Card */}
      <Card>
        <CardContent>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{intentConfig.icon}</span>
                <h1 className="text-2xl font-bold text-neutral-900">{intentConfig.label}</h1>
                <StatusBadge status={status} />
              </div>
              <p className="text-neutral-600 mb-4">
                Thread ID: <span className="font-mono text-sm">{conversation?.thread_id || threadId}</span>
              </p>
              <div className="flex items-center gap-6 text-sm text-neutral-600">
                <div className="flex items-center gap-2">
                  <Calendar size={16} />
                  <span>{formatDateTime(conversation?.created_at)}</span>
                </div>
                {isPaused && (
                  <div className="flex items-center gap-2 text-warning-600">
                    <Clock size={16} />
                    <span>Waiting for response</span>
                  </div>
                )}
                {conversation?.intent_confidence && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs">Confidence:</span>
                    <span className="font-medium">{(conversation.intent_confidence * 100).toFixed(0)}%</span>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<RefreshCw size={16} />}
                onClick={() => refetch()}
              >
                Refresh
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {conversation?.error && (
        <Card>
          <CardContent>
            <div className="p-4 bg-error-50 border border-error-200 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="text-error-600 shrink-0" size={20} />
                <div>
                  <p className="font-medium text-error-900">Workflow Error</p>
                  <p className="text-sm text-error-700 mt-1">{conversation.error}</p>
                  {conversation.error_type && (
                    <p className="text-xs text-error-600 mt-1">Type: {conversation.error_type}</p>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Extracted Parameters */}
      {conversation?.extracted_parameters && (
        <Card>
          <CardHeader>
            <CardTitle>Request Details</CardTitle>
            <CardDescription>Extracted from your message</CardDescription>
          </CardHeader>
          <CardContent>
            <ParametersDisplay parameters={conversation.extracted_parameters} />
          </CardContent>
        </Card>
      )}

      {/* Supplier Search Results */}
      {conversation?.supplier_search && (
        <Card>
          <CardHeader>
            <CardTitle>Supplier Search Results</CardTitle>
            <CardDescription>
              Found {conversation.supplier_search.total_suppliers_found || 0} suppliers, 
              showing top {conversation.supplier_search.top_recommendations?.length || 0}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {conversation.supplier_search.market_insights && (
              <div className="mb-4 p-4 bg-primary-50 border border-primary-200 rounded-lg">
                <p className="text-sm text-primary-900">{conversation.supplier_search.market_insights}</p>
              </div>
            )}
            {conversation.supplier_search.top_recommendations && (
              <div className="space-y-4">
                {conversation.supplier_search.top_recommendations.map((supplier, index) => (
                  <SupplierCard key={supplier.supplier_id || index} supplier={supplier} rank={index + 1} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Quote Details */}
      {conversation?.quote && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Quote Details</CardTitle>
                <CardDescription>Quote ID: {conversation.quote.quote_id}</CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Download size={16} />}
              >
                Download PDF
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <QuoteDisplay quote={conversation.quote} />
          </CardContent>
        </Card>
      )}

      {/* Negotiation State */}
      {conversation?.negotiation && (
        <Card>
          <CardHeader>
            <CardTitle>Negotiation Progress</CardTitle>
            <CardDescription>
              Round {conversation.negotiation.negotiation_rounds || 1} - 
              Status: {conversation.negotiation.negotiation_status || 'Unknown'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <NegotiationDisplay negotiation={conversation.negotiation} />
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
          <CardDescription>Continue or manage this conversation</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Continue Form */}
            {!isPaused && (
              <>
                {!showContinueForm ? (
                  <Button
                    variant="outline"
                    fullWidth
                    leftIcon={<MessageSquare size={18} />}
                    onClick={() => setShowContinueForm(true)}
                  >
                    Continue Conversation
                  </Button>
                ) : (
                  <div className="space-y-3">
                    <Textarea
                      placeholder="Enter your follow-up message..."
                      value={continueInput}
                      onChange={(e) => setContinueInput(e.target.value)}
                      rows={4}
                    />
                    <div className="flex gap-2">
                      <Button
                        onClick={handleContinue}
                        loading={continueConversation.isPending}
                        fullWidth
                      >
                        Send
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowContinueForm(false);
                          setContinueInput('');
                        }}
                        disabled={continueConversation.isPending}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Resume Form */}
            {isPaused && (
              <>
                {!showResumeForm ? (
                  <Button
                    variant="primary"
                    fullWidth
                    leftIcon={<MessageSquare size={18} />}
                    onClick={() => setShowResumeForm(true)}
                  >
                    Resume with Supplier Response
                  </Button>
                ) : (
                  <div className="space-y-3">
                    <Textarea
                      placeholder="Paste the supplier's response here..."
                      value={resumeInput}
                      onChange={(e) => setResumeInput(e.target.value)}
                      rows={6}
                    />
                    <div className="flex gap-2">
                      <Button
                        onClick={handleResume}
                        loading={resumeConversation.isPending}
                        fullWidth
                      >
                        Resume Negotiation
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowResumeForm(false);
                          setResumeInput('');
                        }}
                        disabled={resumeConversation.isPending}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Parameters Display Component
function ParametersDisplay({ parameters }) {
  if (!parameters) return null;
  
  const fabric = parameters.fabric_details || {};
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {fabric.type && (
        <InfoItem icon={<Package />} label="Fabric Type" value={fabric.type} />
      )}
      {fabric.quantity && (
        <InfoItem 
          icon={<Package />} 
          label="Quantity" 
          value={`${formatNumber(fabric.quantity)} ${fabric.unit || ''}`} 
        />
      )}
      {parameters.urgency_level && (
        <InfoItem 
          icon={<Clock />} 
          label="Urgency" 
          value={parameters.urgency_level} 
        />
      )}
      {fabric.certifications && fabric.certifications.length > 0 && (
        <div className="col-span-full">
          <p className="text-sm font-medium text-neutral-700 mb-2">Certifications</p>
          <div className="flex flex-wrap gap-2">
            {fabric.certifications.map((cert, idx) => (
              <span key={idx} className="px-3 py-1 bg-success-100 text-success-700 text-sm rounded-full">
                {cert}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Quote Display Component
function QuoteDisplay({ quote }) {
  if (!quote) return null;

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      {quote.supplier_options && quote.supplier_options.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <InfoItem 
            icon={<Building2 />} 
            label="Options" 
            value={quote.total_options_count || quote.supplier_options.length} 
          />
          {quote.estimated_savings && (
            <InfoItem 
              icon={<DollarSign />} 
              label="Est. Savings" 
              value={`${quote.estimated_savings}%`}
              highlight
            />
          )}
        </div>
      )}

      {/* Supplier Options */}
      {quote.supplier_options && quote.supplier_options.length > 0 && (
        <div className="space-y-4">
          <h4 className="font-semibold text-neutral-900">Supplier Options</h4>
          {quote.supplier_options.map((supplier, index) => (
            <SupplierOptionCard key={index} supplier={supplier} rank={index + 1} />
          ))}
        </div>
      )}

      {/* Strategic Analysis */}
      {quote.strategic_analysis && (
        <div className="p-4 bg-neutral-50 border border-neutral-200 rounded-lg">
          <h4 className="font-semibold text-neutral-900 mb-2">Strategic Analysis</h4>
          {quote.strategic_analysis.market_assessment && (
            <p className="text-sm text-neutral-700 mb-2">{quote.strategic_analysis.market_assessment}</p>
          )}
          {quote.strategic_analysis.recommended_supplier && (
            <p className="text-sm text-primary-700 font-medium">
              Recommended: {quote.strategic_analysis.recommended_supplier}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// Supplier Card Component
function SupplierCard({ supplier, rank }) {
  return (
    <div className="p-4 border border-neutral-200 rounded-lg hover:border-primary-300 transition-all">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-700 font-bold flex items-center justify-center shrink-0">
          #{rank}
        </div>
        <div className="flex-1">
          <div className="flex items-start justify-between mb-2">
            <div>
              <h4 className="font-semibold text-neutral-900">{supplier.name}</h4>
              <p className="text-sm text-neutral-600">{supplier.location}</p>
            </div>
            {supplier.reputation_score && (
              <div className="flex items-center gap-1">
                <Award size={16} className="text-warning-500" />
                <span className="text-sm font-medium">{supplier.reputation_score.toFixed(1)}</span>
              </div>
            )}
          </div>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div>
              <p className="text-neutral-500">Price</p>
              <p className="font-medium">{formatCurrency(supplier.price_per_unit)}</p>
            </div>
            <div>
              <p className="text-neutral-500">Lead Time</p>
              <p className="font-medium">{supplier.lead_time_days} days</p>
            </div>
            <div>
              <p className="text-neutral-500">Score</p>
              <p className="font-medium text-primary-700">{supplier.overall_score?.toFixed(1) || 'N/A'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Supplier Option Card (for quotes)
function SupplierOptionCard({ supplier, rank }) {
  return (
    <div className="p-4 border border-neutral-200 rounded-lg">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-700 font-bold flex items-center justify-center shrink-0">
          #{rank}
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-neutral-900">{supplier.supplier_name}</h4>
          <p className="text-sm text-neutral-600 mb-3">{supplier.supplier_location}</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <p className="text-neutral-500">Unit Price</p>
              <p className="font-medium">{formatCurrency(supplier.unit_price)}</p>
            </div>
            <div>
              <p className="text-neutral-500">Material Cost</p>
              <p className="font-medium">{formatCurrency(supplier.material_cost)}</p>
            </div>
            <div>
              <p className="text-neutral-500">Lead Time</p>
              <p className="font-medium">{supplier.lead_time_days} days</p>
            </div>
            <div>
              <p className="text-neutral-500">Total</p>
              <p className="font-medium text-primary-700">{formatCurrency(supplier.total_landed_cost)}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Negotiation Display
function NegotiationDisplay({ negotiation }) {
  if (!negotiation) return null;

  return (
    <div className="space-y-4">
      {negotiation.drafted_message && (
        <div className="p-4 bg-neutral-50 rounded-lg">
          <p className="text-sm font-medium text-neutral-700 mb-2">Last Message:</p>
          <p className="text-sm text-neutral-600">{truncate(negotiation.drafted_message.message_body || '', 200)}</p>
        </div>
      )}
    </div>
  );
}

// Info Item Component
function InfoItem({ icon, label, value, highlight = false }) {
  return (
    <div className={`p-4 rounded-lg border ${highlight ? 'border-primary-300 bg-primary-50' : 'border-neutral-200 bg-neutral-50'}`}>
      <div className="flex items-center gap-2 mb-2 text-neutral-600">
        {icon && <div className="w-4 h-4">{icon}</div>}
        <p className="text-sm font-medium">{label}</p>
      </div>
      <p className={`text-lg font-semibold ${highlight ? 'text-primary-700' : 'text-neutral-900'}`}>
        {value}
      </p>
    </div>
  );
}
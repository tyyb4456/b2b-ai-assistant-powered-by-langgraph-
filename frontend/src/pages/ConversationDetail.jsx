import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useConversationComprehensive, useConversationMessages, useConversationStatus, useSelectSupplier } from '../api/hooks';
import * as api from '../api/endpoints';
import StreamingConversation from '../components/features/StreamingConversation';
import Card, { CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { Textarea } from '../components/ui/Input';
import { 
  ArrowLeft, 
  Send, 
  Zap, 
  MessageSquare,
  FileText,
  Package,
  Clock,
  CheckCircle,
  XCircle,
  Pause,
  Play,
  TrendingUp,
  AlertTriangle,
  AlertCircle,
  BookOpen,
  BarChart3,
  Briefcase,
} from 'lucide-react';
import { STATUS_CONFIG } from '../utils/constants';

export default function ConversationDetail() {
  const { threadId } = useParams();
  const navigate = useNavigate();

  // Fetch conversation data
  const { data: conversation, isLoading, refetch } = useConversationComprehensive(threadId);
  const { data: messagesData, refetch: refetchMessages } = useConversationMessages(threadId);
  const { data: statusData } = useConversationStatus(threadId, { 
    refetchInterval: 5000 // Poll every 5 seconds
  });

  // Form states
  const [continueInput, setContinueInput] = useState('');
  const [resumeInput, setResumeInput] = useState('');
  const [activeTab, setActiveTab] = useState('overview'); // overview | messages | continue | resume
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  
  // Supplier selection
  const selectSupplierMutation = useSelectSupplier() || { mutate: () => {}, isPending: false };

  // 🔥 FIXED: Streaming setup with proper thread_id handling
  const streaming = StreamingConversation({
    onComplete: (completedThreadId, events) => {
      console.log('[ConversationDetail] ✅ Streaming completed', completedThreadId || threadId, events.length);
      
      // Refetch conversation data
      refetch();
      refetchMessages();
      
      // Reset forms
      setContinueInput('');
      setResumeInput('');
      
      // Switch back to overview after a delay
      setTimeout(() => {
        setActiveTab('overview');
      }, 2000);
    },
    onError: (error) => {
      console.error('[ConversationDetail] ❌ Streaming error:', error);
    },
    showEvents: true,
  });

  // Handle Continue Conversation (with streaming)
  const handleContinue = () => {
    if (!continueInput.trim()) return;

    console.log('[ConversationDetail] 🚀 Starting continue stream for thread:', threadId);
    
    streaming.startStreaming((onEvent, onComplete, onError) => {
      return api.continueConversationStream(
        threadId,
        continueInput,
        onEvent,
        // 🔥 FIXED: Wrap onComplete to pass threadId since continue/resume don't return it
        (data) => {
          console.log('[ConversationDetail] Continue completed:', data);
          // Pass the threadId from URL since backend doesn't return it for continue/resume
          onComplete({ ...data, thread_id: threadId });
        },
        onError
      );
    });
  };

  // Handle Resume Conversation (with streaming)
  const handleResume = () => {
    if (!resumeInput.trim()) return;

    console.log('[ConversationDetail] 🚀 Starting resume stream for thread:', threadId);
    
    streaming.startStreaming((onEvent, onComplete, onError) => {
      return api.resumeConversationStream(
        threadId,
        resumeInput,
        onEvent,
        // 🔥 FIXED: Wrap onComplete to pass threadId
        (data) => {
          console.log('[ConversationDetail] Resume completed:', data);
          onComplete({ ...data, thread_id: threadId });
        },
        onError
      );
    });
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-neutral-600">Loading conversation...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <Card>
          <CardContent>
            <div className="text-center py-12">
              <XCircle size={48} className="mx-auto text-error-600 mb-4" />
              <h3 className="text-xl font-semibold text-neutral-900 mb-2">
                Conversation Not Found
              </h3>
              <p className="text-neutral-600 mb-6">
                The conversation you're looking for doesn't exist or has been deleted.
              </p>
              <Button onClick={() => navigate('/')}>
                Back to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isPaused = conversation.is_paused;
  const status = conversation.status;
  const intent = conversation.intent;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<ArrowLeft size={16} />}
            onClick={() => navigate('/')}
          >
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Conversation Details</h1>
            <p className="text-sm text-neutral-600 font-mono mt-1">
              Thread: {threadId}
            </p>
          </div>
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-3">
          {isPaused && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-warning-50 border border-warning-200 rounded-lg">
              <Pause size={16} className="text-warning-600" />
              <span className="text-sm font-medium text-warning-900">Paused</span>
            </div>
          )}
          <StatusBadge status={status} />
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-neutral-200">
        <TabButton
          active={activeTab === 'overview'}
          onClick={() => setActiveTab('overview')}
          icon={<FileText size={16} />}
        >
          Overview
        </TabButton>
        <TabButton
          active={activeTab === 'messages'}
          onClick={() => setActiveTab('messages')}
          icon={<MessageSquare size={16} />}
        >
          Messages
        </TabButton>
        <TabButton
          active={activeTab === 'continue'}
          onClick={() => setActiveTab('continue')}
          icon={<Send size={16} />}
          disabled={isPaused || streaming.streamState.isStreaming}
        >
          Continue
        </TabButton>
        {isPaused && (
          <TabButton
            active={activeTab === 'resume'}
            onClick={() => setActiveTab('resume')}
            icon={<Play size={16} />}
            disabled={streaming.streamState.isStreaming}
          >
            Resume
          </TabButton>
        )}
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && !streaming.streamState.isStreaming && (
          <OverviewTab 
            conversation={conversation} 
            selectedSupplier={selectedSupplier}
            setSelectedSupplier={setSelectedSupplier}
            selectSupplierMutation={selectSupplierMutation}
            threadId={threadId}
          />
        )}


        {activeTab === 'messages' && !streaming.streamState.isStreaming && (
          <MessagesTab messages={messagesData?.messages || []} />
        )}

        {activeTab === 'continue' && !streaming.streamState.isStreaming && (
          <ContinueTab
            input={continueInput}
            setInput={setContinueInput}
            onSubmit={handleContinue}
            disabled={isPaused}
          />
        )}

        {activeTab === 'resume' && !streaming.streamState.isStreaming && (
          <ResumeTab
            input={resumeInput}
            setInput={setResumeInput}
            onSubmit={handleResume}
          />
        )}

        {/* 🔥 FIXED: Show streaming progress when active */}
        {streaming.streamState.isStreaming && (
          <div className="space-y-4">
            {streaming.renderProgress()}
            <Button
              variant="outline"
              onClick={streaming.stopStreaming}
              fullWidth
            >
              Stop Processing
            </Button>
          </div>
        )}

        {/* Completion Message */}
        {!streaming.streamState.isStreaming && 
         streaming.streamState.events.length > 0 && 
         !streaming.streamState.error && (
          <Card>
            <CardContent>
              <div className="text-center py-8">
                <CheckCircle size={48} className="mx-auto text-success-600 mb-4" />
                <h3 className="text-xl font-semibold text-neutral-900 mb-2">
                  {activeTab === 'continue' ? 'Conversation Continued!' : 'Conversation Resumed!'}
                </h3>
                <p className="text-neutral-600 mb-4">
                  Your request has been processed successfully
                </p>
                <Button onClick={() => setActiveTab('overview')}>
                  View Updated Conversation
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

// ============================================
// TAB COMPONENTS
// ============================================

function OverviewTab({ conversation, selectedSupplier, setSelectedSupplier, selectSupplierMutation, threadId }) {
  const [resumingWorkflow, setResumingWorkflow] = React.useState(false);
  
  // Check if supplier response is available
  const hasSupplierResponse = conversation.is_paused && 
    conversation.negotiation && 
    conversation.negotiation.current_round_status === 'awaiting_supplier_response_review';

  const handleResumeWorkflow = async () => {
    try {
      setResumingWorkflow(true);
      // Get request ID from negotiation data (you may need to adjust based on your data structure)
      const requestId = conversation.negotiation?.current_request_id;
      if (!requestId) {
        alert('Could not find supplier request ID');
        return;
      }
      
      const response = await fetch(`${window.location.origin.replace(/:\d+/, ':8000')}/api/v1/supplier/requests/${requestId}/resume-workflow`, {
        method: 'POST'
      });
      
      if (response.ok) {
        alert('✅ Workflow resumed successfully');
        window.location.reload();
      } else {
        alert('❌ Failed to resume workflow');
      }
    } catch (error) {
      console.error('Error resuming workflow:', error);
      alert('Error: ' + error.message);
    } finally {
      setResumingWorkflow(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* SUPPLIER RESPONSE RECEIVED BANNER */}
      {hasSupplierResponse && (
        <Card>
          <CardContent>
            <div className="bg-success-50 border-l-4 border-success-500 p-4 rounded">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-success-900 mb-2">
                    ✅ Supplier Response Received
                  </h3>
                  <p className="text-sm text-success-700 mb-3">
                    The supplier has submitted their response. Review it and click below to resume the workflow and continue negotiation.
                  </p>
                  <Button
                    onClick={handleResumeWorkflow}
                    disabled={resumingWorkflow}
                    className="bg-success-600 hover:bg-success-700 text-white"
                  >
                    {resumingWorkflow ? 'Resuming...' : 'Resume Workflow Now'}
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* BASIC INFORMATION */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText size={20} />
            Basic Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <InfoRow label="Thread ID" value={conversation.thread_id} />
            <InfoRow label="Intent" value={conversation.intent || 'Unknown'} />
            {conversation.intent_confidence && (
              <InfoRow label="Intent Confidence" value={`${(conversation.intent_confidence * 100).toFixed(0)}%`} />
            )}
            <InfoRow label="Status" value={conversation.status} />
            <InfoRow label="Paused" value={conversation.is_paused ? 'Yes' : 'No'} />
            {conversation.requires_human_review && (
              <InfoRow label="Requires Review" value="Yes" />
            )}
            <InfoRow label="Created" value={new Date(conversation.created_at).toLocaleString()} />
            <InfoRow label="Updated" value={new Date(conversation.updated_at).toLocaleString()} />
            {conversation.next_step && (
              <InfoRow label="Next Step" value={conversation.next_step} />
            )}
          </div>
        </CardContent>
      </Card>

      {/* EXTRACTED PARAMETERS */}
      {conversation.extracted_parameters && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package size={20} />
              Extracted Parameters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {conversation.extracted_parameters.fabric_details && (
                <>
                  <InfoRow label="Fabric Type" value={conversation.extracted_parameters.fabric_details.type} />
                  <InfoRow label="Quantity" value={`${conversation.extracted_parameters.fabric_details.quantity} ${conversation.extracted_parameters.fabric_details.unit}`} />
                </>
              )}
              {conversation.extracted_parameters.urgency_level && (
                <InfoRow label="Urgency" value={conversation.extracted_parameters.urgency_level} />
              )}
              {conversation.extracted_parameters.request_type && (
                <InfoRow label="Request Type" value={conversation.extracted_parameters.request_type} />
              )}
              {conversation.extracted_parameters.confidence && (
                <InfoRow label="Confidence" value={`${(conversation.extracted_parameters.confidence * 100).toFixed(0)}%`} />
              )}
              {conversation.extracted_parameters.supplier_preference && (
                <InfoRow label="Supplier Preference" value={conversation.extracted_parameters.supplier_preference} />
              )}
              {conversation.extracted_parameters.payment_terms && (
                <InfoRow label="Payment Terms" value={conversation.extracted_parameters.payment_terms} />
              )}
              {conversation.extracted_parameters.needs_clarification && (
                <div className="p-3 bg-warning-50 border border-warning-200 rounded-lg">
                  <p className="text-xs font-semibold text-warning-900 mb-1">⚠️ Clarification Needed</p>
                  {conversation.extracted_parameters.clarification_questions?.length > 0 && (
                    <ul className="text-xs text-warning-800 space-y-1">
                      {conversation.extracted_parameters.clarification_questions.map((q, i) => (
                        <li key={i}>• {q}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* SUPPLIER SEARCH */}
      {conversation.supplier_search && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp size={20} />
              Supplier Search Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <InfoRow label="Total Found" value={conversation.supplier_search.total_suppliers_found} />
              <InfoRow label="Filtered" value={conversation.supplier_search.filtered_suppliers} />
              {conversation.supplier_search.search_strategy && (
                <InfoRow label="Strategy" value={conversation.supplier_search.search_strategy} />
              )}
              {conversation.supplier_search.confidence && (
                <InfoRow label="Confidence" value={`${(conversation.supplier_search.confidence * 100).toFixed(0)}%`} />
              )}
              {conversation.supplier_search.market_insights && (
                <div className="p-3 bg-primary-50 border border-primary-200 rounded-lg">
                  <p className="text-xs font-semibold text-primary-900">📊 Market Insights</p>
                  <p className="text-xs text-primary-800 mt-1">{conversation.supplier_search.market_insights}</p>
                </div>
              )}
              {conversation.supplier_search.top_recommendations?.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-neutral-700">Top Recommendations:</p>
                  {conversation.supplier_search.top_recommendations.map((supplier, idx) => (
                    <div key={idx} className={`p-3 rounded border transition ${selectedSupplier?.supplier_id === supplier.supplier_id ? 'bg-primary-100 border-primary-400' : 'bg-neutral-50 border-neutral-200 hover:border-primary-300'}`}>
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-neutral-900">{supplier.name}</p>
                          <div className="text-xs text-neutral-600 space-y-1 mt-1">
                            <p>📍 {supplier.location}</p>
                            {supplier.price_per_unit && <p>💰 ${supplier.price_per_unit}/unit</p>}
                            {supplier.lead_time_days && <p>⏱️ {supplier.lead_time_days} days</p>}
                            <p>⭐ Score: {supplier.overall_score.toFixed(1)}/100</p>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => {
                            setSelectedSupplier(supplier);
                            selectSupplierMutation.mutate({
                              threadId,
                              supplierData: supplier
                            });
                          }}
                          disabled={selectSupplierMutation.isPending}
                          className={selectedSupplier?.supplier_id === supplier.supplier_id ? 'bg-primary-600 text-white' : ''}
                        >
                          {selectSupplierMutation.isPending && selectedSupplier?.supplier_id === supplier.supplier_id ? 'Selecting...' : selectedSupplier?.supplier_id === supplier.supplier_id ? '✓ Selected' : 'Select'}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* QUOTE DETAILS */}
      {conversation.quote && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 size={20} />
              Quote Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-primary-50 rounded-lg border border-primary-200">
                <p className="text-xs text-primary-700 font-medium">Quote ID</p>
                <p className="text-sm font-mono text-primary-900 mt-1">{conversation.quote.quote_id}</p>
              </div>
              <div className="p-3 bg-success-50 rounded-lg border border-success-200">
                <p className="text-xs text-success-700 font-medium">Total Options</p>
                <p className="text-sm font-bold text-success-900 mt-1">{conversation.quote.total_options_count}</p>
              </div>
            </div>
            {conversation.quote.estimated_savings && (
              <div className="p-3 bg-success-50 border border-success-200 rounded-lg">
                <p className="text-xs font-semibold text-success-900">💰 Potential Savings</p>
                <p className="text-xl font-bold text-success-700 mt-1">{conversation.quote.estimated_savings}%</p>
              </div>
            )}
            {conversation.quote.validity_days && (
              <InfoRow label="Quote Valid For" value={`${conversation.quote.validity_days} days`} />
            )}
            {conversation.quote.strategic_analysis && (
              <div className="p-3 bg-secondary-50 border border-secondary-200 rounded-lg space-y-2">
                <p className="text-xs font-semibold text-secondary-900">📋 Strategic Analysis</p>
                {conversation.quote.strategic_analysis.market_assessment && (
                  <p className="text-xs text-secondary-800">{conversation.quote.strategic_analysis.market_assessment}</p>
                )}
                {conversation.quote.strategic_analysis.negotiation_opportunities?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-secondary-900 mb-1">Negotiation Opportunities:</p>
                    <ul className="text-xs text-secondary-800 space-y-1">
                      {conversation.quote.strategic_analysis.negotiation_opportunities.map((opp, i) => (
                        <li key={i}>• {opp}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* NEGOTIATION */}
      {conversation.negotiation && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Briefcase size={20} />
              Negotiation Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <InfoRow label="Status" value={conversation.negotiation.negotiation_status} />
              <InfoRow label="Rounds" value={conversation.negotiation.negotiation_rounds} />
              {conversation.negotiation.negotiation_topic && (
                <InfoRow label="Topic" value={conversation.negotiation.negotiation_topic} />
              )}
              {conversation.negotiation.current_position && (
                <InfoRow label="Current Position" value={conversation.negotiation.current_position} />
              )}
              {conversation.negotiation.negotiation_strategy && (
                <div className="p-3 bg-primary-50 border border-primary-200 rounded-lg">
                  <p className="text-xs font-semibold text-primary-900">🎯 Strategy</p>
                  {conversation.negotiation.negotiation_strategy.primary_approach && (
                    <p className="text-xs text-primary-800 mt-1">{conversation.negotiation.negotiation_strategy.primary_approach}</p>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* SUPPLIER RESPONSE ANALYSIS */}
      {conversation.supplier_response_analysis && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle size={20} />
              Supplier Response Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {conversation.supplier_response_analysis.supplier_intent && (
                <InfoRow label="Supplier Intent" value={conversation.supplier_response_analysis.supplier_intent.intent_type} />
              )}
              {conversation.supplier_response_analysis.analysis_confidence && (
                <InfoRow label="Analysis Confidence" value={`${(conversation.supplier_response_analysis.analysis_confidence * 100).toFixed(0)}%`} />
              )}
              {conversation.supplier_response_analysis.supplier_offers?.length > 0 && (
                <div className="p-2 bg-success-50 rounded border border-success-200">
                  <p className="text-xs font-semibold text-success-900 mb-1">✅ Supplier Offers:</p>
                  <ul className="text-xs text-success-800 space-y-1">
                    {conversation.supplier_response_analysis.supplier_offers.map((offer, i) => (
                      <li key={i}>• {offer}</li>
                    ))}
                  </ul>
                </div>
              )}
              {conversation.supplier_response_analysis.risk_alerts?.length > 0 && (
                <div className="p-2 bg-error-50 rounded border border-error-200">
                  <p className="text-xs font-semibold text-error-900 mb-1">⚠️ Risk Alerts:</p>
                  <ul className="text-xs text-error-800 space-y-1">
                    {conversation.supplier_response_analysis.risk_alerts.map((alert, i) => (
                      <li key={i}>• {alert}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* CLARIFICATION */}
      {conversation.clarification && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle size={20} />
              Clarification Required
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <InfoRow label="Request Type" value={conversation.clarification.request_type} />
              {conversation.clarification.urgency_level && (
                <InfoRow label="Urgency" value={conversation.clarification.urgency_level} />
              )}
              {conversation.clarification.root_cause_analysis && (
                <div className="p-2 bg-warning-50 rounded border border-warning-200">
                  <p className="text-xs font-semibold text-warning-900">Root Cause:</p>
                  <p className="text-xs text-warning-800 mt-1">{conversation.clarification.root_cause_analysis}</p>
                </div>
              )}
              {conversation.clarification.questions?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-neutral-700 mb-2">Questions to Address:</p>
                  {conversation.clarification.questions.map((q, i) => (
                    <div key={i} className="text-xs p-2 bg-neutral-50 rounded mb-1">
                      <p className="font-medium text-neutral-900">{q.question_text}</p>
                      <p className="text-neutral-600 mt-1">Type: {q.question_type} | Priority: {q.priority}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* CONTRACT */}
      {conversation.contract && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen size={20} />
              Contract Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {conversation.contract.contract_id && (
                <InfoRow label="Contract ID" value={conversation.contract.contract_id} />
              )}
              <InfoRow label="Ready" value={conversation.contract.contract_ready ? 'Yes' : 'No'} />
              <InfoRow label="Legal Review Required" value={conversation.contract.requires_legal_review ? 'Yes' : 'No'} />
              {conversation.contract.contract_confidence && (
                <InfoRow label="Confidence" value={`${(conversation.contract.contract_confidence * 100).toFixed(0)}%`} />
              )}
              {conversation.contract.risk_assessment && (
                <div className="p-2 bg-warning-50 rounded border border-warning-200">
                  <p className="text-xs font-semibold text-warning-900">⚠️ Risk Assessment</p>
                  <p className="text-xs text-warning-800 mt-1">Level: {conversation.contract.risk_assessment.overall_risk_level}</p>
                  {conversation.contract.risk_assessment.risk_factors?.length > 0 && (
                    <ul className="text-xs text-warning-800 mt-1 space-y-1">
                      {conversation.contract.risk_assessment.risk_factors.map((factor, i) => (
                        <li key={i}>• {factor}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* FOLLOW-UP */}
      {conversation.follow_up && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock size={20} />
              Follow-up Schedule
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {conversation.follow_up.schedule_id && (
                <InfoRow label="Schedule ID" value={conversation.follow_up.schedule_id} />
              )}
              {conversation.follow_up.next_follow_up_date && (
                <InfoRow label="Next Follow-up" value={new Date(conversation.follow_up.next_follow_up_date).toLocaleString()} />
              )}
              {conversation.follow_up.follow_up_dates?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-neutral-700 mb-2">Scheduled Dates:</p>
                  <ul className="text-xs text-neutral-600 space-y-1">
                    {conversation.follow_up.follow_up_dates.map((date, i) => (
                      <li key={i}>• {new Date(date).toLocaleString()}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* NEXT STEPS */}
      {conversation.next_steps_recommendations && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp size={20} />
              Next Steps & Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {conversation.next_steps_recommendations.immediate_actions?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-neutral-900 mb-1">🚀 Immediate Actions:</p>
                <ul className="text-xs text-neutral-700 space-y-1">
                  {conversation.next_steps_recommendations.immediate_actions.map((action, i) => (
                    <li key={i}>• {action}</li>
                  ))}
                </ul>
              </div>
            )}
            {conversation.next_steps_recommendations.short_term_strategies?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-neutral-900 mb-1">📅 Short-term Strategies:</p>
                <ul className="text-xs text-neutral-700 space-y-1">
                  {conversation.next_steps_recommendations.short_term_strategies.map((strategy, i) => (
                    <li key={i}>• {strategy}</li>
                  ))}
                </ul>
              </div>
            )}
            {conversation.next_steps_recommendations.alternative_suppliers?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-neutral-900 mb-1">🔄 Alternative Suppliers:</p>
                {conversation.next_steps_recommendations.alternative_suppliers.map((supplier, i) => (
                  <div key={i} className="text-xs p-2 bg-neutral-50 rounded mb-1">
                    <p className="font-medium text-neutral-900">{supplier.supplier_name}</p>
                    <p className="text-neutral-600">{supplier.why_better}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ERRORS */}
      {conversation.error && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-error-900">
              <XCircle size={20} />
              Error Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-3 bg-error-50 border border-error-200 rounded-lg">
              {conversation.error_type && (
                <p className="text-xs font-semibold text-error-900 mb-1">Type: {conversation.error_type}</p>
              )}
              <p className="text-sm text-error-800">{conversation.error}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function MessagesTab({ messages }) {
  if (!messages || messages.length === 0) {
    return (
      <Card>
        <CardContent>
          <div className="text-center py-12 text-neutral-500">
            <MessageSquare size={48} className="mx-auto mb-4 text-neutral-400" />
            <p>No messages yet</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Message History</CardTitle>
        <CardDescription>{messages.length} messages</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {messages.map((msg, idx) => (
            <div 
              key={idx}
              className="p-4 bg-neutral-50 rounded-lg border border-neutral-200"
            >
              <div className="flex items-start gap-3">
                <MessageSquare size={16} className="text-primary-600 mt-1" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-primary-700 uppercase">
                      {msg.role || 'Assistant'}
                    </span>
                    {msg.timestamp && (
                      <span className="text-xs text-neutral-500">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-neutral-700">{msg.content}</p>
                  {msg.node && (
                    <p className="text-xs text-neutral-500 mt-1">
                      Node: {msg.node}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ContinueTab({ input, setInput, onSubmit, disabled }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send size={18} />
          Continue Conversation
        </CardTitle>
        <CardDescription>
          Send a new message to continue this conversation
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Textarea
            placeholder="What would you like to do next? (e.g., 'Can you improve the lead time?')"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            rows={5}
            disabled={disabled}
          />
          <div className="flex gap-3">
            <Button
              onClick={onSubmit}
              disabled={!input.trim() || disabled}
              leftIcon={<Zap size={18} />}
              fullWidth
            >
              Continue with Live Updates
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ResumeTab({ input, setInput, onSubmit }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Play size={18} />
          Resume Negotiation
        </CardTitle>
        <CardDescription>
          Provide the supplier's response to continue negotiation
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Textarea
            placeholder="Paste the supplier's response here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            rows={8}
          />
          <div className="flex gap-3">
            <Button
              onClick={onSubmit}
              disabled={!input.trim()}
              leftIcon={<Zap size={18} />}
              fullWidth
            >
              Resume with Live Updates
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================
// UTILITY COMPONENTS
// ============================================

function TabButton({ active, onClick, icon, children, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        flex items-center gap-2 px-4 py-2 border-b-2 transition-all
        ${active 
          ? 'border-primary-600 text-primary-700 font-medium' 
          : 'border-transparent text-neutral-600 hover:text-neutral-900 hover:border-neutral-300'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {icon}
      {children}
    </button>
  );
}

function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || { color: 'neutral', label: status };
  
  const colorClasses = {
    success: 'bg-success-50 text-success-700 border-success-200',
    warning: 'bg-warning-50 text-warning-700 border-warning-200',
    error: 'bg-error-50 text-error-700 border-error-200',
    info: 'bg-primary-50 text-primary-700 border-primary-200',
    neutral: 'bg-neutral-100 text-neutral-700 border-neutral-200',
  };

  return (
    <div className={`px-3 py-1.5 rounded-lg border ${colorClasses[config.color] || colorClasses.neutral}`}>
      <span className="text-sm font-medium">{config.label}</span>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-neutral-100 last:border-0">
      <span className="text-sm font-medium text-neutral-700">{label}</span>
      <span className="text-sm text-neutral-900">{value}</span>
    </div>
  );
}
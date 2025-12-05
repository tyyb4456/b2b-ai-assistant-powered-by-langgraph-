import { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000/api/v1/supplier';

export default function ResponseModal({ requestId, isOpen, onClose, onSuccess }) {
  const [request, setRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [responseType, setResponseType] = useState('accept');
  const [responseText, setResponseText] = useState('');
  const [responseData, setResponseData] = useState({
    new_price: '',
    new_lead_time: '',
    new_payment_terms: '',
  });

  useEffect(() => {
    if (isOpen && requestId) {
      fetchRequestDetail();
    }
  }, [isOpen, requestId]);

  const fetchRequestDetail = async () => {
    try {
      const token = localStorage.getItem('supplier_token');
      const response = await fetch(`${API_BASE}/requests/${requestId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setRequest(data.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch request:', error);
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!responseText.trim()) {
      alert('Please enter a response message');
      return;
    }

    setSubmitting(true);

    try {
      const token = localStorage.getItem('supplier_token');
      
      const response = await fetch(`${API_BASE}/requests/${requestId}/respond`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          response_text: responseText,
          response_type: responseType,
          response_data: responseType === 'counteroffer' ? responseData : null
        })
      });

      const result = await response.json();

      if (response.ok) {
        alert('✅ Response submitted. Awaiting buyer to resume workflow.');
        onSuccess && onSuccess();
        onClose();
      } else {
        alert(`❌ Failed to submit response: ${result.error?.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Submission error:', error);
      alert('❌ Network error. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 shrink-0">
          <h2 className="text-xl font-semibold text-gray-900">
            Respond to Request
          </h2>
          <button
            onClick={onClose}
            disabled={submitting}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading request details...</p>
            </div>
          ) : !request ? (
            <div className="text-center py-12">
              <p className="text-xl text-gray-900 mb-4">Request not found</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Request Info Summary */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-2">{request.request_subject}</h3>
                <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                  <div>ID: {request.request_id}</div>
                  <div>Round: {request.conversation_round}</div>
                  <div>Type: {request.request_type}</div>
                  <div>Priority: {request.priority}</div>
                </div>
              </div>

              {/* Request Message */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Request Message
                </label>
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 max-h-32 overflow-y-auto">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{request.request_message}</p>
                </div>
              </div>

              {/* Response Type Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Response Type
                </label>
                <div className="grid grid-cols-5 gap-2">
                  {[
                    { value: 'accept', label: '✅ Accept', color: 'green' },
                    { value: 'counteroffer', label: '💬 Counter', color: 'blue' },
                    { value: 'reject', label: '❌ Reject', color: 'red' },
                    { value: 'clarification', label: '❓ Clarify', color: 'yellow' },
                    { value: 'delay', label: '⏰ Delay', color: 'orange' },
                  ].map((option) => (
                    <button
                      key={option.value}
                      onClick={() => setResponseType(option.value)}
                      className={`
                        px-2 py-2 rounded-lg border-2 text-xs font-medium transition-all
                        ${responseType === option.value
                          ? `border-${option.color}-500 bg-${option.color}-50 text-${option.color}-700`
                          : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                        }
                      `}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Counteroffer Fields (conditional) */}
              {responseType === 'counteroffer' && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
                  <h3 className="text-sm font-semibold text-blue-900">
                    Counteroffer Terms
                  </h3>
                  
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        New Price
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={responseData.new_price}
                        onChange={(e) => setResponseData({...responseData, new_price: e.target.value})}
                        className="w-full px-2 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., 4.50"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Lead Time (days)
                      </label>
                      <input
                        type="number"
                        value={responseData.new_lead_time}
                        onChange={(e) => setResponseData({...responseData, new_lead_time: e.target.value})}
                        className="w-full px-2 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., 30"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Payment Terms
                      </label>
                      <input
                        type="text"
                        value={responseData.new_payment_terms}
                        onChange={(e) => setResponseData({...responseData, new_payment_terms: e.target.value})}
                        className="w-full px-2 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., 50% advance"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Response Message */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Response Message *
                </label>
                <textarea
                  value={responseText}
                  onChange={(e) => setResponseText(e.target.value)}
                  rows={5}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  placeholder="Enter your detailed response here..."
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Provide a clear and professional response.
                </p>
              </div>
            </div>
          )}
        </div>

{/* Modal Footer */}
        {!loading && request && (
          <div className="flex gap-3 p-6 border-t border-gray-200 bg-gray-50 shrink-0">
            <button
              onClick={handleSubmit}
              disabled={submitting || !responseText.trim() || request.status !== 'pending'}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
            >
              {submitting ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Submitting...
                </span>
              ) : (
                'Submit Response & Resume Workflow'
              )}
            </button>

            <button
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 transition-all text-sm"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

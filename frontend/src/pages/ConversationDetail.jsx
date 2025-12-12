/* ---------------  ConversationDetail.jsx (Refactored Layout)  ---------------- */

import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  useConversationComprehensive,
  useConversationStatus,
  useSelectSupplier,
} from "../api/hooks";
import * as api from "../api/endpoints";
import Card, { CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import Button from "../components/ui/Button";
import { ArrowLeft, FileText, Package, BarChart3, XCircle } from "lucide-react";

const WS_BASE = "ws://localhost:8000/api/v1";

export default function ConversationDetail() {
  const { threadId } = useParams();
  const navigate = useNavigate();

  const { data: conversation, isLoading, refetch } = useConversationComprehensive(threadId);
  const { data: statusData } = useConversationStatus(threadId, { refetchInterval: 5000 });
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [supplierResponseAvailable, setSupplierResponseAvailable] = useState(false);
  const wsRef = useRef(null);
  const selectSupplierMutation = useSelectSupplier();

  useEffect(() => {
    if (!conversation || !statusData?.is_paused) return;

    const ws = new WebSocket(`${WS_BASE}/ws/conversations/${threadId}`);
    wsRef.current = ws;

    ws.onopen = () => setWsConnected(true);
    ws.onerror = () => setWsConnected(false);
    ws.onclose = () => setWsConnected(false);

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "supplier_response_received") {
        setSupplierResponseAvailable(true);
        refetch();
      }
    };

    return () => ws.close();
  }, [threadId, conversation, statusData, refetch]);

  if (isLoading) return <div className="flex items-center justify-center py-20 text-neutral-500">Loading…</div>;
  if (!conversation)
    return (
      <div className="max-w-4xl mx-auto mt-10">
        <Card>
          <CardContent className="text-center py-16">
            <XCircle size={48} className="mx-auto text-red-600 mb-4" />
            <h2 className="text-xl font-bold">Conversation Not Found</h2>
            <Button className="mt-4" onClick={() => navigate("/")}>Go Back</Button>
          </CardContent>
        </Card>
      </div>
    );

  return (
    <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
      {/* HEADER */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<ArrowLeft size={16} />}
            onClick={() => navigate(`/conversation/${threadId}`)}
          >
            Back
          </Button>
          <div>
            <h1 className="text-xl font-bold">Conversation Details</h1>
            <p className="text-xs text-neutral-500 font-mono">{threadId}</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-md text-xs border ${wsConnected ? "bg-green-50 text-green-700 border-green-400" : "bg-gray-100 text-gray-600 border-gray-300"
          }`}
        >
          {wsConnected ? "Live" : "Offline"}
        </div>
      </div>

      {/* TWO-COLUMN GRID: Basic Info | Extracted Parameters */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <OverviewCard conversation={conversation} />
        <ExtractedParametersCard conversation={conversation} />
      </div>

      {/* FULL-WIDTH SUPPLIER SECTION */}
      <SupplierCard
        conversation={conversation}
        selectedSupplier={selectedSupplier}
        setSelectedSupplier={setSelectedSupplier}
        selectSupplierMutation={selectSupplierMutation}
        threadId={threadId}
      />
    </div>
  );
}

/* --------------------- COMPONENTS ------------------------ */

function OverviewCard({ conversation }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText size={18} /> Basic Information
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <InfoRow label="Intent" value={conversation.intent} />
        <InfoRow label="Status" value={conversation.status} />
        <InfoRow label="Paused" value={conversation.is_paused ? "Yes" : "No"} />
        <InfoRow label="Created" value={new Date(conversation.created_at).toLocaleString()} />
        <InfoRow label="Updated" value={new Date(conversation.updated_at).toLocaleString()} />
      </CardContent>
    </Card>
  );
}

function ExtractedParametersCard({ conversation }) {
  const params = conversation.extracted_parameters;
  if (!params) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Package size={18} /> Extracted Parameters
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {params.fabric_details && (
          <>
            <InfoRow label="Fabric" value={params.fabric_details.type} />
            <InfoRow label="Qty" value={`${params.fabric_details.quantity} ${params.fabric_details.unit}`} />
          </>
        )}
        {params.urgency_level && <InfoRow label="Urgency" value={params.urgency_level} />}
        {params.payment_terms && <InfoRow label="Payment Terms" value={params.payment_terms} />}
      </CardContent>
    </Card>
  );
}

function SupplierCard({ conversation, selectedSupplier, setSelectedSupplier, selectSupplierMutation, threadId }) {
  if (!conversation.supplier_search) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 size={18} /> Supplier Information
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {conversation.supplier_search.top_recommendations?.map((s) => (
          <div
            key={s.supplier_id}
            className={`p-3 rounded border ${selectedSupplier?.supplier_id === s.supplier_id
              ? "bg-primary-100 border-primary-400"
              : "bg-neutral-50 border-neutral-200 hover:border-primary-300"
              }`}
          >
            <div className="flex justify-between">
              <div>
                <p className="font-semibold">{s.name}</p>
                <p className="text-xs text-neutral-500">{s.location}</p>
              </div>
              <Button
                size="sm"
                onClick={() => {
                  setSelectedSupplier(s);
                  selectSupplierMutation.mutate({ threadId, supplierData: s });
                }}
              >
                {selectedSupplier?.supplier_id === s.supplier_id ? "✓ Selected" : "Select"}
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between text-xs py-0.5">
      <span className="font-semibold">{label}</span>
      <span>{value}</span>
    </div>
  );
}

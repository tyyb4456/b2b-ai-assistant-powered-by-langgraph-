"""
Enhanced Conversation Service with comprehensive data mapping

Maps rich AgentState data to detailed API responses
"""
from typing import Optional, Any
from datetime import datetime
import uuid
from loguru import logger

from app.services.graph_manager import get_graph_manager 
from app.schemas.conversation_schemas import (
    # Comprehensive response
    ConversationComprehensiveResponse,
    
    # Workflow-specific responses
    QuoteWorkflowResponse,
    NegotiationWorkflowResponse,
    
    # Component responses
    ExtractedParametersResponse,
    FabricDetailsResponse,
    SupplierSearchResponse,
    SupplierDetailResponse,
    GeneratedQuoteResponse,
    SupplierQuoteOptionResponse,
    LogisticsCostResponse,
    QuoteAnalysisResponse,
    NegotiationStateResponse,
    DraftedMessageResponse,
    NegotiationStrategyResponse,
    MessageValidationResponse,
    SupplierResponseAnalysisResponse,
    SupplierIntentResponse,
    ExtractedTermsResponse,
    NegotiationAnalysisResponse,
    ClarificationStateResponse,
    ClarificationQuestionResponse,
    ContractStateResponse,
    ContractTermsResponse,
    ContractMetadataResponse,
    RiskAssessmentResponse,
    FollowUpStateResponse,
    FollowUpAnalysisResponse,
    FollowUpScheduleResponse,
    NextStepsResponse,
    FailureAnalysisResponse,
    AlternativeSupplierResponse,
    NegotiationAdjustmentResponse,
)


class EnhancedConversationService:
    """
    Service for managing conversation lifecycle with comprehensive data exposure
    """
    
    def __init__(self):
        self.graph_manager = get_graph_manager()
    
    def generate_thread_id(self, user_id: Optional[str] = None) -> str:
        """Generate a unique thread ID"""
        unique_id = str(uuid.uuid4())
        return f"{user_id}_{unique_id}" if user_id else f"thread_{unique_id}"
    
    # ============================================
    # HELPER - Convert Pydantic models to dicts safely
    # ============================================
    
    def _to_dict(self, data: Any) -> Optional[dict]:
        """
        Safely convert Pydantic model or dict to dict
        
        Handles:
        - None -> None
        - dict -> dict
        - Pydantic model -> dict
        """
        if data is None:
            return None
        
        # Already a dict
        if isinstance(data, dict):
            return data
        
        # Pydantic model (v2)
        if hasattr(data, 'model_dump'):
            return data.model_dump()
        
        # Pydantic model (v1)
        if hasattr(data, 'dict'):
            return data.dict()
        
        # Unknown type - try to return as-is
        logger.warning(f"Unknown data type in _to_dict: {type(data)}")
        return data
    
    def _to_datetime(self, value: Any) -> datetime:
        """
        Safely convert value to datetime
        
        Handles:
        - datetime -> datetime (pass through)
        - str -> datetime (parse ISO format)
        - None -> current datetime
        """
        if value is None:
            return datetime.utcnow()
        
        # Already a datetime
        if isinstance(value, datetime):
            return value
        
        # String - parse it
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                logger.warning(f"Invalid datetime string: {value}")
                return datetime.utcnow()
        
        # Unknown type
        logger.warning(f"Unknown datetime type: {type(value)}")
        return datetime.utcnow()
    
    # ============================================
    # MAPPING HELPERS - Convert AgentState to API Responses
    # ============================================
    
    def _map_fabric_details(self, fabric_data: Optional[Any]) -> Optional[FabricDetailsResponse]:
        """Map fabric details from state"""
        fabric_dict = self._to_dict(fabric_data)
        if not fabric_dict:
            return None
        
        return FabricDetailsResponse(
            type=fabric_dict.get('type'),
            quantity=fabric_dict.get('quantity'),
            unit=fabric_dict.get('unit'),
            quality_specs=fabric_dict.get('quality_specs', []),
            color=fabric_dict.get('color'),
            width=fabric_dict.get('width'),
            composition=fabric_dict.get('composition'),
            finish=fabric_dict.get('finish'),
            certifications=fabric_dict.get('certifications', [])
        )
    
    def _map_extracted_parameters(self, params: Optional[Any]) -> Optional[ExtractedParametersResponse]:
        """Map extracted parameters from state"""
        params_dict = self._to_dict(params)
        if not params_dict:
            return None
        
        fabric_details = self._map_fabric_details(params_dict.get('fabric_details'))
        
        return ExtractedParametersResponse(
            item_id=params_dict.get('item_id'),
            request_type=params_dict.get('request_type'),
            confidence=params_dict.get('confidence'),
            fabric_details=fabric_details,
            urgency_level=params_dict.get('urgency_level'),
            supplier_preference=params_dict.get('supplier_preference'),
            moq_flexibility=params_dict.get('moq_flexibility'),
            payment_terms=params_dict.get('payment_terms'),
            additional_notes=params_dict.get('additional_notes'),
            needs_clarification=params_dict.get('needs_clarification', False),
            clarification_questions=params_dict.get('clarification_questions', []),
            missing_info=params_dict.get('missing_info', [])
        )
    
    def _map_supplier_search(self, search_data: Optional[Any], suppliers: Optional[list]) -> Optional[SupplierSearchResponse]:
        """Map supplier search results"""
        if not search_data and not suppliers:
            return None
        
        # Convert to dict if Pydantic model
        search_dict = self._to_dict(search_data)
        
        # Map individual suppliers
        supplier_details = []
        if suppliers:
            for supp in suppliers:
                supp_dict = self._to_dict(supp)
                if not supp_dict:
                    continue
                    
                supplier_details.append(SupplierDetailResponse(
                    supplier_id=supp_dict.get('supplier_id', ''),
                    name=supp_dict.get('name', ''),
                    location=supp_dict.get('location', ''),
                    email=supp_dict.get('email'),
                    phone=supp_dict.get('phone'),
                    website=supp_dict.get('website'),
                    price_per_unit=supp_dict.get('price_per_unit'),
                    currency=supp_dict.get('currency', 'USD'),
                    lead_time_days=supp_dict.get('lead_time_days'),
                    minimum_order_qty=supp_dict.get('minimum_order_qty'),
                    reputation_score=supp_dict.get('reputation_score', 5.0),
                    overall_score=supp_dict.get('overall_score', 0.0),
                    specialties=supp_dict.get('specialties', []),
                    certifications=supp_dict.get('certifications', []),
                    active=supp_dict.get('active', True),
                    source=supp_dict.get('source'),
                    notes=supp_dict.get('notes')
                ))
        
        return SupplierSearchResponse(
            total_suppliers_found=search_dict.get('total_suppliers_found', 0) if search_dict else len(supplier_details),
            filtered_suppliers=search_dict.get('filtered_suppliers', 0) if search_dict else len(supplier_details),
            top_recommendations=supplier_details,
            search_strategy=search_dict.get('search_strategy') if search_dict else None,
            market_insights=search_dict.get('market_insights') if search_dict else None,
            confidence=search_dict.get('confidence') if search_dict else None,
            alternative_suggestions=search_dict.get('alternative_suggestions', []) if search_dict else []
        )
    
    def _map_quote(self, quote_data: Optional[Any]) -> Optional[GeneratedQuoteResponse]:
        """Map quote generation data"""
        quote_dict = self._to_dict(quote_data)
        if not quote_dict:
            return None
        
        # Map supplier options
        supplier_options = []
        if quote_dict.get('supplier_options'):
            for opt in quote_dict['supplier_options']:
                opt_dict = self._to_dict(opt)
                if not opt_dict:
                    continue
                    
                logistics = opt_dict.get('logistics_cost', {})
                logistics_dict = self._to_dict(logistics) if logistics else {}
                
                supplier_options.append(SupplierQuoteOptionResponse(
                    supplier_name=opt_dict.get('supplier_name', ''),
                    supplier_location=opt_dict.get('supplier_location', ''),
                    unit_price=opt_dict.get('unit_price', 0.0),
                    material_cost=opt_dict.get('material_cost', 0.0),
                    logistics_cost=LogisticsCostResponse(
                        shipping_cost=logistics_dict.get('shipping_cost', 0.0) if logistics_dict else 0.0,
                        insurance_cost=logistics_dict.get('insurance_cost', 0.0) if logistics_dict else 0.0,
                        customs_duties=logistics_dict.get('customs_duties', 0.0) if logistics_dict else 0.0,
                        handling_fees=logistics_dict.get('handling_fees', 0.0) if logistics_dict else 0.0,
                        total_logistics=logistics_dict.get('total_logistics', 0.0) if logistics_dict else 0.0
                    ),
                    total_landed_cost=opt_dict.get('total_landed_cost', 0.0),
                    lead_time_days=opt_dict.get('lead_time_days', 0),
                    reliability_score=opt_dict.get('reliability_score', 5.0),
                    overall_score=opt_dict.get('overall_score', 0.0),
                    key_advantages=opt_dict.get('key_advantages', []),
                    potential_risks=opt_dict.get('potential_risks', [])
                ))
        
        # Map strategic analysis
        analysis_data = quote_dict.get('strategic_analysis', {})
        analysis_dict = self._to_dict(analysis_data) if analysis_data else None
        
        strategic_analysis = QuoteAnalysisResponse(
            market_assessment=analysis_dict.get('market_assessment') if analysis_dict else None,
            recommended_supplier=analysis_dict.get('recommended_supplier') if analysis_dict else None,
            recommendation_reasoning=analysis_dict.get('recommendation_reasoning') if analysis_dict else None,
            risk_factors=analysis_dict.get('risk_factors', []) if analysis_dict else [],
            negotiation_opportunities=analysis_dict.get('negotiation_opportunities', []) if analysis_dict else [],
            alternative_strategies=analysis_dict.get('alternative_strategies', []) if analysis_dict else []
        ) if analysis_dict else None
        
        return GeneratedQuoteResponse(
            quote_id=quote_dict.get('quote_id', ''),
            quote_date=self._to_datetime(quote_dict.get('quote_date')),
            validity_days=quote_dict.get('validity_days', 30),
            client_summary=quote_dict.get('client_summary'),
            supplier_options=supplier_options,
            strategic_analysis=strategic_analysis,
            total_options_count=quote_dict.get('total_options_count', len(supplier_options)),
            estimated_savings=quote_dict.get('estimated_savings')
        )
    
    def _map_negotiation_state(self, state: dict) -> Optional[NegotiationStateResponse]:
        """Map negotiation state"""
        if not state.get('negotiation_rounds') and not state.get('drafted_message_data'):
            return None
        
        # Map drafted message
        msg_data = state.get('drafted_message_data', {})
        drafted_message = DraftedMessageResponse(
            message_id=msg_data.get('message_id'),
            recipient=msg_data.get('recipient'),
            subject_line=msg_data.get('subject_line'),
            message_body=msg_data.get('message_body'),
            message_type=msg_data.get('message_type'),
            priority_level=msg_data.get('priority_level'),
            expected_response_time=msg_data.get('expected_response_time'),
            fallback_options=msg_data.get('fallback_options', []),
            confidence_score=msg_data.get('confidence_score')
        ) if msg_data else None
        
        # Map negotiation strategy
        strategy_data = state.get('negotiation_strategy', {})
        negotiation_strategy = NegotiationStrategyResponse(
            primary_approach=strategy_data.get('primary_approach'),
            supporting_arguments=strategy_data.get('supporting_arguments', []),
            tone_assessment=strategy_data.get('tone_assessment'),
            cultural_considerations=strategy_data.get('cultural_considerations'),
            risk_factors=strategy_data.get('risk_factors', [])
        ) if strategy_data else None
        
        # Map message validation
        validation_data = state.get('message_validation', {})
        message_validation = MessageValidationResponse(
            clarity_score=validation_data.get('clarity_score'),
            completeness_score=validation_data.get('completeness_score'),
            professionalism_score=validation_data.get('professionalism_score'),
            overall_quality_score=validation_data.get('overall_quality_score'),
            requires_human_review=validation_data.get('requires_human_review', False),
            auto_enhancement_possible=validation_data.get('auto_enhancement_possible', False),
            recommended_action=validation_data.get('recommended_action'),
            validation_confidence=validation_data.get('validation_confidence'),
            critical_issues_count=validation_data.get('critical_issues_count', 0),
            high_priority_fixes=validation_data.get('high_priority_fixes', [])
        ) if validation_data else None
        
        return NegotiationStateResponse(
            negotiation_rounds=state.get('negotiation_rounds', 0),
            negotiation_status=state.get('negotiation_status'),
            negotiation_topic=state.get('negotiation_topic'),
            conversation_tone=state.get('conversation_tone'),
            negotiation_objective=state.get('negotiation_objective'),
            drafted_message=drafted_message,
            negotiation_strategy=negotiation_strategy,
            message_validation=message_validation,
            validated_message=state.get('validated_message'),
            validation_passed=state.get('validation_passed', False),
            last_message_confidence=state.get('last_message_confidence'),
            active_supplier_email=state.get('active_supplier_email'),
            current_request_id=state.get('current_request_id'),
            email_sent=state.get('email_sent', False),
            pdf_generated=state.get('pdf_generated', False)
        )
    
    def _map_supplier_response_analysis(self, state: dict) -> Optional[SupplierResponseAnalysisResponse]:
        """Map supplier response analysis"""
        if not state.get('supplier_response'):
            return None
        
        # Map supplier intent
        intent_data = state.get('supplier_intent', {})
        supplier_intent = SupplierIntentResponse(
            intent=intent_data.get('intent'),
            confidence=intent_data.get('confidence'),
            sentiment=intent_data.get('sentiment'),
            urgency_indicators=intent_data.get('urgency_indicators', []),
            relationship_signals=intent_data.get('relationship_signals', [])
        ) if intent_data else None
        
        # Map extracted terms
        terms_data = state.get('extracted_terms', {})
        extracted_terms = ExtractedTermsResponse(
            new_price=terms_data.get('new_price'),
            price_currency=terms_data.get('price_currency'),
            price_unit=terms_data.get('price_unit'),
            new_lead_time=terms_data.get('new_lead_time'),
            new_minimum_quantity=terms_data.get('new_minimum_quantity'),
            new_payment_terms=terms_data.get('new_payment_terms'),
            new_incoterms=terms_data.get('new_incoterms'),
            new_quantity=terms_data.get('new_quantity'),
            quality_adjustments=terms_data.get('quality_adjustments'),
            additional_conditions=terms_data.get('additional_conditions', []),
            concessions_offered=terms_data.get('concessions_offered', [])
        ) if terms_data else None
        
        # Map negotiation analysis
        analysis_data = state.get('negotiation_analysis', {})
        negotiation_analysis = NegotiationAnalysisResponse(
            market_comparison=analysis_data.get('market_comparison'),
            movement_analysis=analysis_data.get('movement_analysis'),
            strategic_assessment=analysis_data.get('strategic_assessment'),
            negotiation_leverage=analysis_data.get('negotiation_leverage'),
            recommended_response=analysis_data.get('recommended_response'),
            risk_factors=analysis_data.get('risk_factors', []),
            opportunities=analysis_data.get('opportunities', []),
            confidence_score=analysis_data.get('confidence_score')
        ) if analysis_data else None
        
        return SupplierResponseAnalysisResponse(
            supplier_response=state.get('supplier_response'),
            supplier_intent=supplier_intent,
            extracted_terms=extracted_terms,
            negotiation_analysis=negotiation_analysis,
            negotiation_advice=state.get('negotiation_advice'),
            analysis_confidence=state.get('analysis_confidence'),
            supplier_offers=state.get('supplier_offers', []),
            is_follow_up_response=state.get('is_follow_up_response', False),
            risk_alerts=state.get('risk_alerts', []),
            requires_attention=state.get('requires_attention', False),
            identified_opportunities=state.get('identified_opportunities', [])
        )
    
    def _map_clarification_state(self, state: dict) -> Optional[ClarificationStateResponse]:
        """Map clarification handling state"""
        clarification_data = state.get('clarification_classification', {})
        if not clarification_data:
            return None
        
        # Map individual questions
        questions = []
        if clarification_data.get('questions'):
            for q in clarification_data['questions']:
                questions.append(ClarificationQuestionResponse(
                    question_text=q.get('question_text', ''),
                    question_type=q.get('question_type', 'general_info'),
                    priority=q.get('priority', 'medium'),
                    blocks_negotiation=q.get('blocks_negotiation', False),
                    complexity=q.get('complexity', 0.5),
                    requires_internal_consultation=q.get('requires_internal_consultation', False)
                ))
        
        return ClarificationStateResponse(
            request_type=clarification_data.get('request_type'),
            questions=questions,
            supplier_confusion_level=clarification_data.get('supplier_confusion_level'),
            root_cause_analysis=clarification_data.get('root_cause_analysis'),
            urgency_level=clarification_data.get('urgency_level'),
            deal_impact=clarification_data.get('deal_impact'),
            supplier_engagement_signal=clarification_data.get('supplier_engagement_signal'),
            recommended_response_approach=clarification_data.get('recommended_response_approach'),
            escalation_recommended=clarification_data.get('escalation_recommended', False),
            can_answer_completely=state.get('information_validation', {}).get('can_answer_completely', False),
            completeness_score=state.get('information_validation', {}).get('completeness_score')
        )
    
    def _map_contract_state(self, state: dict) -> Optional[ContractStateResponse]:
        """Map contract initiation state"""
        if not state.get('contract_id') and not state.get('drafted_contract'):
            return None
        
        # Map contract terms
        terms_data = state.get('contract_terms', {})
        contract_terms = ContractTermsResponse(
            fabric_specifications=terms_data.get('fabric_specifications'),
            quantity=terms_data.get('quantity'),
            unit_price=terms_data.get('unit_price'),
            total_value=terms_data.get('total_value'),
            currency=terms_data.get('currency', 'USD'),
            delivery_terms=terms_data.get('delivery_terms'),
            payment_terms=terms_data.get('payment_terms'),
            quality_standards=terms_data.get('quality_standards'),
            penalties_and_incentives=terms_data.get('penalties_and_incentives', [])
        ) if terms_data else None
        
        # Map contract metadata
        metadata = state.get('contract_metadata', {})
        contract_metadata = ContractMetadataResponse(
            contract_id=metadata.get('contract_id'),
            contract_type=metadata.get('contract_type', 'textile_procurement'),
            contract_version=metadata.get('contract_version', '1.0'),
            buyer_company=metadata.get('buyer_company'),
            supplier_company=metadata.get('supplier_company'),
            creation_date=metadata.get('creation_date'),
            effective_date=metadata.get('effective_date'),
            expiry_date=metadata.get('expiry_date'),
            governing_law=metadata.get('governing_law', 'International Commercial Law')
        ) if metadata else None
        
        # Map risk assessment
        risk_data = state.get('risk_assessment', {})
        risk_assessment = RiskAssessmentResponse(
            overall_risk_level=risk_data.get('overall_risk_level'),
            risk_score=risk_data.get('risk_score'),
            supplier_reliability_risk=risk_data.get('supplier_reliability_risk'),
            negotiation_complexity_risk=risk_data.get('negotiation_complexity_risk'),
            financial_risk=risk_data.get('financial_risk'),
            geographic_risk=risk_data.get('geographic_risk'),
            quality_risk=risk_data.get('quality_risk'),
            risk_factors=risk_data.get('risk_factors', []),
            mitigation_requirements=risk_data.get('mitigation_requirements', []),
            recommended_clauses=risk_data.get('recommended_clauses', [])
        ) if risk_data else None
        
        return ContractStateResponse(
            contract_id=state.get('contract_id'),
            contract_ready=state.get('contract_ready', False),
            contract_confidence=state.get('contract_confidence'),
            requires_legal_review=state.get('requires_legal_review', True),
            contract_terms=contract_terms,
            contract_metadata=contract_metadata,
            risk_assessment=risk_assessment,
            contract_generation_timestamp=state.get('contract_generation_timestamp')
        )
    
    def _map_follow_up_state(self, state: dict) -> Optional[FollowUpStateResponse]:
        """Map follow-up scheduling state"""
        if not state.get('follow_up_schedule') and not state.get('follow_up_analysis'):
            return None
        
        # Map follow-up analysis
        analysis_data = state.get('follow_up_analysis', {})
        follow_up_analysis = FollowUpAnalysisResponse(
            delay_reason=analysis_data.get('delay_reason'),
            delay_type=analysis_data.get('delay_type'),
            estimated_delay_duration=analysis_data.get('estimated_delay_duration'),
            supplier_commitment_level=analysis_data.get('supplier_commitment_level'),
            urgency_of_our_timeline=analysis_data.get('urgency_of_our_timeline'),
            competitive_risk=analysis_data.get('competitive_risk'),
            relationship_preservation_importance=analysis_data.get('relationship_preservation_importance'),
            market_dynamics_impact=analysis_data.get('market_dynamics_impact')
        ) if analysis_data else None
        
        # Map follow-up schedule
        schedule_data = state.get('follow_up_schedule', {})
        follow_up_schedule = FollowUpScheduleResponse(
            schedule_id=schedule_data.get('schedule_id'),
            primary_follow_up_date=schedule_data.get('primary_follow_up_date'),
            follow_up_method=schedule_data.get('follow_up_method'),
            follow_up_intervals=schedule_data.get('follow_up_intervals', []),
            escalation_timeline=schedule_data.get('escalation_timeline'),
            initial_follow_up_tone=schedule_data.get('initial_follow_up_tone'),
            escalation_tone=schedule_data.get('escalation_tone'),
            confidence_in_schedule=schedule_data.get('confidence_in_schedule')
        ) if schedule_data else None
        
        return FollowUpStateResponse(
            follow_up_analysis=follow_up_analysis,
            follow_up_schedule=follow_up_schedule,
            schedule_id=state.get('schedule_id'),
            follow_up_dates=state.get('follow_up_dates', []),
            next_follow_up_date=state.get('next_follow_up_date'),
            follow_up_ready=state.get('follow_up_ready', False),
            last_follow_up_confidence=state.get('last_follow_up_confidence')
        )
    
    def _map_next_steps(self, state: dict) -> Optional[NextStepsResponse]:
        """Map next steps recommendations"""
        if not state.get('next_steps_recommendations'):
            return None
        
        recommendations = state['next_steps_recommendations']
        
        # Map failure analysis
        failure_data = recommendations.get('failure_analysis', {})
        failure_analysis = FailureAnalysisResponse(
            failure_category=failure_data.get('failure_category'),
            root_causes=failure_data.get('root_causes', []),
            supplier_constraints=failure_data.get('supplier_constraints', []),
            market_factors=failure_data.get('market_factors', []),
            severity=failure_data.get('severity')
        ) if failure_data else None
        
        # Map alternative suppliers
        alt_suppliers = []
        if recommendations.get('alternative_suppliers'):
            for alt in recommendations['alternative_suppliers']:
                alt_suppliers.append(AlternativeSupplierResponse(
                    supplier_name=alt.get('supplier_name', ''),
                    location=alt.get('location', ''),
                    estimated_price=alt.get('estimated_price'),
                    lead_time_days=alt.get('lead_time_days'),
                    reliability_score=alt.get('reliability_score', 5.0),
                    why_better=alt.get('why_better', ''),
                    contact_priority=alt.get('contact_priority', 'medium')
                ))
        
        # Map negotiation adjustments
        adjustments = []
        if recommendations.get('negotiation_adjustments'):
            for adj in recommendations['negotiation_adjustments']:
                adjustments.append(NegotiationAdjustmentResponse(
                    parameter=adj.get('parameter', ''),
                    current_value=adj.get('current_value', ''),
                    suggested_value=adj.get('suggested_value', ''),
                    rationale=adj.get('rationale', ''),
                    success_probability=adj.get('success_probability', 0.5)
                ))
        
        return NextStepsResponse(
            failure_analysis=failure_analysis,
            immediate_actions=recommendations.get('immediate_actions', []),
            short_term_strategies=recommendations.get('short_term_strategies', []),
            long_term_approaches=recommendations.get('long_term_approaches', []),
            alternative_suppliers=alt_suppliers,
            negotiation_adjustments=adjustments,
            budget_impact=recommendations.get('budget_impact'),
            confidence_score=recommendations.get('confidence_score'),
            priority_ranking=recommendations.get('priority_ranking', [])
        )
    
    # ============================================
    # PUBLIC METHODS - Enhanced API Operations
    # ============================================
    
    async def start_conversation(
        self,
        user_input: str,
        recipient_email: Optional[str] = None,
        # channel: str = "api",
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Start a new conversation workflow"""
        thread_id = self.generate_thread_id(user_id)
        
        logger.info(f"Starting new conversation: {thread_id}")
        
        initial_state = {
            "thread_id": thread_id,  # Include thread_id in initial state
            "user_input": user_input,
            "status": "starting",
            # "channel": channel,
        }

        print(initial_state)
        
        if recipient_email:
            initial_state["recipient_email"] = recipient_email
        
        try:
            events_log = []
            
            async for event in self.graph_manager.execute_workflow(thread_id, initial_state):
                events_log.append(event)
            
            logger.success(f"Conversation workflow completed: {thread_id}")
            
            # Give checkpoint time to save
            import asyncio
            await asyncio.sleep(0.1)
            
            # Get final state
            current_state = await self.graph_manager.get_state(thread_id)
            
            return {
                "thread_id": thread_id,
                "status": current_state.get("status", "completed") if current_state else "completed",
                "intent": current_state.get("intent") if current_state else None,
                "next_step": current_state.get("next_step") if current_state else None,
                "is_paused": await self.graph_manager.is_workflow_paused(thread_id),
                "events_count": len(events_log),
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to start conversation {thread_id}: {e}")
            raise
    
    async def get_conversation_comprehensive(
        self,
        thread_id: str
    ) -> Optional[ConversationComprehensiveResponse]:
        """Get COMPREHENSIVE conversation details with ALL data"""
        logger.debug(f"Retrieving comprehensive conversation: {thread_id}")
        
        state = await self.graph_manager.get_state(thread_id)
        
        if not state:
            logger.warning(f"⚠️ No state found for thread: {thread_id}")
            return None
        
        is_paused = await self.graph_manager.is_workflow_paused(thread_id)
        
        return ConversationComprehensiveResponse(
            thread_id=thread_id,
            status=state.get("status", "unknown"),
            intent=state.get("intent"),
            intent_confidence=state.get("intent_confidence"),
            next_step=state.get("next_step"),
            is_paused=is_paused,
            requires_human_review=state.get("requires_human_review", False),
            created_at=self._to_datetime(state.get("timestamp")),
            updated_at=datetime.utcnow(),
            
            # Map all the rich data
            extracted_parameters=self._map_extracted_parameters(state.get('extracted_parameters')),
            supplier_search=self._map_supplier_search(
                state.get('supplier_search_result'),
                state.get('top_suppliers')
            ),
            quote=self._map_quote(state.get('generated_quote')),
            negotiation=self._map_negotiation_state(state),
            supplier_response_analysis=self._map_supplier_response_analysis(state),
            clarification=self._map_clarification_state(state),
            contract=self._map_contract_state(state),
            follow_up=self._map_follow_up_state(state),
            next_steps_recommendations=self._map_next_steps(state),
            
            # Error info
            error=state.get("error"),
            error_type=state.get("error_type")
        )
    
    async def get_quote_workflow_details(
        self,
        thread_id: str
    ) -> Optional[QuoteWorkflowResponse]:
        """Get details specifically for quote workflow"""
        logger.debug(f"Retrieving quote workflow: {thread_id}")
        
        state = await self.graph_manager.get_state(thread_id)
        
        if not state or state.get('intent') != 'get_quote':
            return None
        
        return QuoteWorkflowResponse(
            thread_id=thread_id,
            status=state.get("status", "unknown"),
            intent="get_quote",
            extracted_parameters=self._map_extracted_parameters(state.get('extracted_parameters')),
            supplier_search=self._map_supplier_search(
                state.get('supplier_search_result'),
                state.get('top_suppliers')
            ),
            quote=self._map_quote(state.get('generated_quote')),
            email_sent=state.get('email_sent', False),
            pdf_generated=state.get('pdf_generated', False),
            is_paused=await self.graph_manager.is_workflow_paused(thread_id),
            created_at=self._to_datetime(state.get("timestamp")),
            updated_at=datetime.utcnow()
        )
    
    async def get_negotiation_workflow_details(
        self,
        thread_id: str
    ) -> Optional[NegotiationWorkflowResponse]:
        """Get details specifically for negotiation workflow"""
        logger.debug(f"Retrieving negotiation workflow: {thread_id}")
        
        state = await self.graph_manager.get_state(thread_id)
        
        if not state or state.get('intent') != 'negotiate':
            return None
        
        negotiation = self._map_negotiation_state(state)
        if not negotiation:
            return None
        
        return NegotiationWorkflowResponse(
            thread_id=thread_id,
            status=state.get("status", "unknown"),
            intent="negotiate",
            negotiation=negotiation,
            supplier_response_analysis=self._map_supplier_response_analysis(state),
            clarification=self._map_clarification_state(state),
            contract=self._map_contract_state(state),
            follow_up=self._map_follow_up_state(state),
            next_steps_recommendations=self._map_next_steps(state),
            is_paused=await self.graph_manager.is_workflow_paused(thread_id),
            created_at=self._to_datetime(state.get("timestamp")),
            updated_at=datetime.utcnow()
        )
    
    async def resume_with_supplier_response(
        self,
        thread_id: str,
        supplier_response: str
    ) -> dict[str, Any]:
        """Resume a PAUSED conversation with supplier's response"""
        logger.info(f"Resuming conversation with supplier response: {thread_id}")
        
        if not await self.graph_manager.thread_exists(thread_id):
            raise ValueError(f"Conversation not found: {thread_id}")
        
        if not await self.graph_manager.is_workflow_paused(thread_id):
            raise ValueError(
                f"Conversation is not paused. Use /continue endpoint for completed workflows."
            )
        
        try:
            events_log = []
            
            async for event in self.graph_manager.resume_with_supplier_response(
                thread_id, 
                supplier_response
            ):
                if "error" in event:
                    raise RuntimeError(event["error"]["message"])
                
                events_log.append(event)
            
            logger.success(f"Conversation resumed successfully: {thread_id}")
            
            import asyncio
            await asyncio.sleep(0.1)
            
            current_state = await self.graph_manager.get_state(thread_id)
            
            return {
                "thread_id": thread_id,
                "status": current_state.get("status", "resumed") if current_state else "resumed",
                "intent": current_state.get("intent") if current_state else None,
                "negotiation_rounds": current_state.get("negotiation_rounds", 0) if current_state else 0,
                "negotiation_status": current_state.get("negotiation_status") if current_state else None,
                "is_paused": await self.graph_manager.is_workflow_paused(thread_id),
                "events_count": len(events_log),
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to resume conversation {thread_id}: {e}")
            raise
    
    async def continue_conversation(
        self,
        thread_id: str,
        user_input: str
    ) -> dict[str, Any]:
        """Continue a conversation with new user input"""
        logger.info(f"Continuing conversation: {thread_id}")
        
        if not await self.graph_manager.thread_exists(thread_id):
            raise ValueError(f"Conversation not found: {thread_id}")
        
        try:
            updates = {"user_input": user_input}
            
            events_log = []
            
            async for event in self.graph_manager.continue_workflow(thread_id, updates):
                events_log.append(event)
            
            logger.success(f"Conversation continued successfully: {thread_id}")
            
            import asyncio
            await asyncio.sleep(0.1)
            
            current_state = await self.graph_manager.get_state(thread_id)
            
            return {
                "thread_id": thread_id,
                "status": current_state.get("status", "continued") if current_state else "continued",
                "intent": current_state.get("intent") if current_state else None,
                "is_paused": await self.graph_manager.is_workflow_paused(thread_id),
                "events_count": len(events_log),
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to continue conversation {thread_id}: {e}")
            raise
    
    async def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> list[dict]:
        """List conversations with summary info"""
        logger.debug(f"Listing conversations (user_id={user_id}, limit={limit})")
        
        user_prefix = f"{user_id}_" if user_id else None
        thread_ids = await self.graph_manager.list_threads(user_prefix)
        
        thread_ids = thread_ids[:limit]
        
        conversations = []
        
        for thread_id in thread_ids:
            state = await self.graph_manager.get_state(thread_id)
            
            if not state:
                continue
            
            user_input = state.get("user_input", "")
            preview = user_input[:100] if user_input else "No preview available"
            
            conversations.append({
                "thread_id": thread_id,
                "status": state.get("status", "unknown"),
                "intent": state.get("intent"),
                "preview": preview,
                "created_at": self._to_datetime(state.get("timestamp")),
                "updated_at": datetime.utcnow()
            })
        
        logger.info(f"Found {len(conversations)} conversations")
        
        return conversations
    
    async def conversation_exists(self, thread_id: str) -> bool:
        """Check if a conversation exists"""
        return await self.graph_manager.thread_exists(thread_id)


# Global singleton instance
_enhanced_conversation_service: Optional[EnhancedConversationService] = None


def get_enhanced_conversation_service() -> EnhancedConversationService:
    """Get or create the global EnhancedConversationService instance"""
    global _enhanced_conversation_service
    
    if _enhanced_conversation_service is None:
        _enhanced_conversation_service = EnhancedConversationService()
    
    return _enhanced_conversation_service
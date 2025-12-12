"""
Graph Manager Service - Bridge between FastAPI and LangGraph

FIXED: Properly handle continue vs resume workflows
"""
from typing import Optional, AsyncIterator, Any
import aiosqlite
from pathlib import Path
from loguru import logger

from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Import your existing graph setup
from graph_builder import graph_builder, Config as GraphConfig
from state import AgentState
from app.core.config import settings


class GraphManager:
    """
    Manages LangGraph workflow execution and state management
    """
    
    def __init__(self):
        """Initialize the graph manager with checkpoint database"""
        self._graph = None
        self._checkpointer = None
        self._conn = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """
        Lazily initialize the LangGraph with async SQLite checkpointing
        """
        if self._initialized:
            return
            
        try:
            checkpoint_db_path = settings.checkpoint_db_path
            
            logger.info(f"Initializing checkpoint database: {checkpoint_db_path}")
            
            # Create async connection using aiosqlite
            self._conn = await aiosqlite.connect(
                database=str(checkpoint_db_path),
                check_same_thread=False
            )
            
            # Create async checkpointer with the connection
            self._checkpointer = AsyncSqliteSaver(conn=self._conn)
            
            # Setup the checkpointer (creates tables if needed)
            await self._checkpointer.setup()
            
            # Compile graph with checkpointing and interruption points
            self._graph = graph_builder.compile(
                checkpointer=self._checkpointer,
                interrupt_before=['receive_supplier_response'],
                debug=settings.GRAPH_DEBUG
            )
            
            self._initialized = True
            logger.success("LangGraph initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangGraph: {e}")
            raise
    
    async def execute_workflow(
        self,
        thread_id: str,
        initial_state: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Execute a workflow and stream events
        
        Args:
            thread_id: Unique identifier for this conversation
            initial_state: Initial state to start the workflow
        
        Yields:
            Dict containing workflow events as they occur
        """
        await self._ensure_initialized()
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            logger.info(f"Starting workflow execution for thread: {thread_id}")
            
            # Stream workflow events using async iterator
            async for event in self._graph.astream(initial_state, config):
                logger.debug(f"Workflow event: {list(event.keys())}")
                yield event
            
            logger.success(f"Workflow completed for thread: {thread_id}")
            
        except Exception as e:
            logger.error(f"Workflow execution failed for thread {thread_id}: {e}")
            yield {"error": {"message": str(e), "thread_id": thread_id}}
    
    async def get_state(self, thread_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieve the current state for a thread
        
        Args:
            thread_id: Conversation identifier
        
        Returns:
            Current state dictionary or None if not found
        """
        await self._ensure_initialized()
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            # Use async method
            state = await self._graph.aget_state(config)
            
            if state and state.values:
                logger.debug(f"Retrieved state for thread: {thread_id}")
                return state.values
            
            logger.warning(f"No state found for thread: {thread_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve state for thread {thread_id}: {e}")
            return None
    
    async def update_state(
        self,
        thread_id: str,
        updates: dict[str, Any],
        as_node: Optional[str] = None
    ) -> bool:
        """
        Update the state for a thread (used for resuming paused workflows)
        
        Args:
            thread_id: Conversation identifier
            updates: State updates to apply
            as_node: Optional node name to update as
        
        Returns:
            True if update successful, False otherwise
        """
        await self._ensure_initialized()
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            
            # Use async method
            if as_node:
                await self._graph.aupdate_state(config, updates, as_node=as_node)
            else:
                await self._graph.aupdate_state(config, updates)
            
            logger.info(f"Updated state for thread: {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update state for thread {thread_id}: {e}")
            return False
    
    async def resume_with_supplier_response(
        self,
        thread_id: str,
        supplier_response: str
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Resume a paused workflow with supplier response
        
        This mirrors the EXACT pattern from graph_builder.py:
        1. Check if workflow is paused
        2. Update state as_node="receive_supplier_response"
        3. Stream from None to resume
        
        Args:
            thread_id: Conversation identifier
            supplier_response: Supplier's response message
        
        Yields:
            Dict containing workflow events as they occur
        """
        await self._ensure_initialized()
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Check if workflow is paused at interruption point
            state = await self._graph.aget_state(config)
            
            if not state.next:
                error_msg = f"No paused workflow found for thread: {thread_id}"
                logger.error(error_msg)
                yield {"error": {"message": error_msg, "thread_id": thread_id}}
                return
            
            logger.info(f"Resuming paused workflow with supplier response: {thread_id}")
            logger.debug(f"Paused at nodes: {state.next}")
            
            # Update state AS IF we're at the interrupted node
            # This is crucial for LangGraph to know where to resume from
            await self._graph.aupdate_state(
                config,
                {"supplier_response": supplier_response},
                as_node="receive_supplier_response"  # 👈 CRITICAL!
            )
            
            logger.debug(f"State updated as node: receive_supplier_response")
            
            # Now stream from None to continue from interruption point
            async for event in self._graph.astream(None, config):
                logger.debug(f"Resume event: {list(event.keys())}")
                yield event
            
            logger.success(f"Workflow resumed and completed for thread: {thread_id}")
            
        except Exception as e:
            logger.error(f"Failed to resume workflow for thread {thread_id}: {e}")
            yield {"error": {"message": str(e), "thread_id": thread_id}}

    async def continue_workflow(
        self,
        thread_id: str,
        updates: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Continue a workflow by re-executing with updated state
        
        This mirrors graph_builder.py's continue_workflow() pattern:
        - Loads existing checkpoint
        - Merges updates into state
        - Re-executes entire workflow from START
        
        Args:
            thread_id: Conversation identifier
            updates: State updates to apply (e.g., {"user_input": "new message"})
        
        Yields:
            Dict containing workflow events as they occur
        """
        await self._ensure_initialized()
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            logger.info(f"Continuing workflow with updates for thread: {thread_id}")
            logger.debug(f"Updates: {list(updates.keys())}")
            
            # THIS IS THE KEY: Stream with updates on existing thread
            # LangGraph will:
            # 1. Load checkpoint
            # 2. Merge updates
            # 3. Re-execute from START
            async for event in self._graph.astream(updates, config):
                logger.debug(f"Continue event: {list(event.keys())}")
                logger.info(f"Continue event: {list(event.keys())}")
                yield event
            
            logger.success(f"Workflow continued successfully for thread: {thread_id}")
            
        except Exception as e:
            logger.error(f"Failed to continue workflow for thread {thread_id}: {e}")
            yield {"error": {"message": str(e), "thread_id": thread_id}}
    
    async def list_threads(self, user_prefix: Optional[str] = None) -> list[str]:
        """
        List all thread IDs in the checkpoint database
        
        Args:
            user_prefix: Optional prefix to filter threads (e.g., "user123_")
        
        Returns:
            List of thread IDs
        """
        await self._ensure_initialized()
        
        try:
            # Use the existing connection
            if user_prefix:
                query = "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE ?"
                cursor = await self._conn.execute(query, (f"{user_prefix}%",))
            else:
                query = "SELECT DISTINCT thread_id FROM checkpoints"
                cursor = await self._conn.execute(query)
            
            rows = await cursor.fetchall()
            threads = [row[0] for row in rows]
            
            logger.debug(f"Found {len(threads)} threads")
            return threads
            
        except Exception as e:
            logger.error(f"Failed to list threads: {e}")
            return []
    
    async def thread_exists(self, thread_id: str) -> bool:
        """
        Check if a thread exists in the checkpoint database
        
        Args:
            thread_id: Conversation identifier
        
        Returns:
            True if thread exists, False otherwise
        """
        state = await self.get_state(thread_id)
        return state is not None
    
    async def is_workflow_paused(self, thread_id: str) -> bool:
        """
        Check if a workflow is paused (waiting for input at interrupt_before)
        
        Args:
            thread_id: Conversation identifier
        
        Returns:
            True if workflow is paused, False otherwise
        """
        await self._ensure_initialized()
        
        try:
            config = {"configurable": {"thread_id": thread_id}}
            # Use async method
            state = await self._graph.aget_state(config)
            
            # If state.next exists, workflow is paused at interruption point
            return bool(state.next) if state else False
            
        except Exception as e:
            logger.error(f"Failed to check pause status for thread {thread_id}: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources (call on shutdown)"""
        if self._conn:
            await self._conn.close()
            logger.info("Checkpoint database connection closed")


# Global singleton instance
_graph_manager: Optional[GraphManager] = None


def get_graph_manager() -> GraphManager:
    """
    Get or create the global GraphManager instance
    
    Returns:
        GraphManager singleton
    """
    global _graph_manager
    
    if _graph_manager is None:
        _graph_manager = GraphManager()
    
    return _graph_manager



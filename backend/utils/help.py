from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

def get_active_follow_up_schedule(supplier_id: str) -> Optional[Dict[str, Any]]:
    """Check if there's an active follow-up schedule for this supplier"""
    
    from backend.database import SessionLocal, FollowUpSchedule as FollowUpScheduleDB
    from sqlalchemy import desc
    
    db = SessionLocal()
    
    try:
        schedule = db.query(FollowUpScheduleDB).filter(
            FollowUpScheduleDB.supplier_id == supplier_id,
            FollowUpScheduleDB.status == 'active'
        ).order_by(desc(FollowUpScheduleDB.created_at)).first()
        
        if schedule:
            return {
                'schedule_id': schedule.schedule_id,
                'delay_reason': schedule.delay_reason,
                'next_follow_up_date': schedule.next_follow_up_date.isoformat(),
                'follow_ups_sent': schedule.follow_ups_sent,
                'commitment_level': schedule.supplier_commitment_level
            }
        
        return None
        
    finally:
        db.close()


def update_follow_up_on_response(schedule_id: str, response_type: str):
    """Update follow-up schedule when supplier responds"""
    
    from backend.database import SessionLocal, FollowUpSchedule as FollowUpScheduleDB, FollowUpMessage as FollowUpMessageDB
    from sqlalchemy import desc
    
    db = SessionLocal()
    
    try:
        schedule = db.query(FollowUpScheduleDB).filter(
            FollowUpScheduleDB.schedule_id == schedule_id
        ).first()
        
        if not schedule:
            return
        
        # Mark response received
        latest_message = db.query(FollowUpMessageDB).filter(
            FollowUpMessageDB.schedule_id == schedule_id,
            FollowUpMessageDB.status == 'sent'
        ).order_by(desc(FollowUpMessageDB.actual_send_date)).first()
        
        if latest_message:
            latest_message.response_received = True
        
        # Update schedule based on response type
        if response_type in ['accept', 'counteroffer']:
            # Positive response - cancel remaining follow-ups
            schedule.status = 'completed'
            
            pending_messages = db.query(FollowUpMessageDB).filter(
                FollowUpMessageDB.schedule_id == schedule_id,
                FollowUpMessageDB.status == 'pending'
            ).all()
            
            for msg in pending_messages:
                msg.status = 'cancelled'
            
            print(f"✅ Follow-up schedule completed - supplier responded positively")
        
        elif response_type == 'delay':
            # Still delaying - extend schedule
            schedule.next_follow_up_date = datetime.now() + timedelta(days=3)
            print(f"⏰ Follow-up extended by 3 days")
        
        elif response_type == 'reject':
            # Rejection - cancel schedule
            schedule.status = 'cancelled'
            print(f"❌ Follow-up cancelled - supplier rejected")
        
        db.commit()
        
    except Exception as e:
        print(f"Error updating follow-up: {e}")
        db.rollback()
    finally:
        db.close()


def get_all_active_follow_ups() -> List[Dict[str, Any]]:
    """Get all active follow-up schedules (for dashboard/monitoring)"""
    
    from backend.database import SessionLocal, FollowUpSchedule as FollowUpScheduleDB, FollowUpMessage as FollowUpMessageDB
    from sqlalchemy import func
    
    db = SessionLocal()
    
    try:
        schedules = db.query(
            FollowUpScheduleDB,
            func.count(FollowUpMessageDB.id).label('total_messages'),
            func.sum(
                func.case([(FollowUpMessageDB.status == 'sent', 1)], else_=0)
            ).label('sent_messages')
        ).outerjoin(
            FollowUpMessageDB, 
            FollowUpScheduleDB.schedule_id == FollowUpMessageDB.schedule_id
        ).filter(
            FollowUpScheduleDB.status == 'active'
        ).group_by(
            FollowUpScheduleDB.id
        ).all()
        
        results = []
        for schedule, total, sent in schedules:
            results.append({
                'schedule_id': schedule.schedule_id,
                'supplier_id': schedule.supplier_id,
                'delay_reason': schedule.delay_reason,
                'next_follow_up': schedule.next_follow_up_date.isoformat(),
                'commitment_level': schedule.supplier_commitment_level,
                'messages_sent': sent or 0,
                'messages_total': total or 0,
                'created_at': schedule.created_at.isoformat()
            })
        
        return results
        
    finally:
        db.close()


# Usage example
if __name__ == "__main__":
    active = get_all_active_follow_ups()
    print(f"\n📊 Active Follow-Ups: {len(active)}")
    for f in active:
        print(f"   • {f['supplier_id']}: {f['delay_reason']} - Next: {f['next_follow_up']}")
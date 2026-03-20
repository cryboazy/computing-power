import uuid
import json
import threading
from datetime import datetime, date, timedelta
from typing import Optional, List

from app.local_database import LocalSessionLocal
from app.local_models import LocalAggregationTask
from app.database import SessionLocal
from app.aggregator import DataAggregator


task_lock = threading.Lock()
running_task_id: Optional[str] = None


def create_task(task_type: str = "refresh", target_dates: List[date] = None) -> str:
    global running_task_id
    
    with task_lock:
        if running_task_id is not None:
            db = LocalSessionLocal()
            try:
                running = db.query(LocalAggregationTask).filter(
                    LocalAggregationTask.task_id == running_task_id
                ).first()
                if running and running.status in ["pending", "running"]:
                    return None
            finally:
                db.close()
        
        task_id = str(uuid.uuid4())
        db = LocalSessionLocal()
        try:
            dates_json = json.dumps([d.isoformat() for d in target_dates]) if target_dates else "[]"
            total_days = len(target_dates) if target_dates else 0
            total_steps = total_days * 6
            
            task = LocalAggregationTask(
                task_id=task_id,
                task_type=task_type,
                status="pending",
                target_dates=dates_json,
                total_days=total_days,
                total_steps=total_steps
            )
            db.add(task)
            db.commit()
            
            running_task_id = task_id
            return task_id
        finally:
            db.close()


def update_task_progress(task_id: str, **kwargs):
    db = LocalSessionLocal()
    try:
        task = db.query(LocalAggregationTask).filter(
            LocalAggregationTask.task_id == task_id
        ).first()
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            db.commit()
    finally:
        db.close()


def get_task(task_id: str) -> Optional[dict]:
    db = LocalSessionLocal()
    try:
        task = db.query(LocalAggregationTask).filter(
            LocalAggregationTask.task_id == task_id
        ).first()
        if task:
            return {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": task.status,
                "progress": task.progress,
                "current_step": task.current_step,
                "total_steps": task.total_steps,
                "processed_days": task.processed_days,
                "total_days": task.total_days,
                "error_message": task.error_message,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "end_time": task.end_time.isoformat() if task.end_time else None,
                "create_time": task.create_time.isoformat() if task.create_time else None,
            }
        return None
    finally:
        db.close()


def get_recent_tasks(limit: int = 10) -> List[dict]:
    db = LocalSessionLocal()
    try:
        tasks = db.query(LocalAggregationTask).order_by(
            LocalAggregationTask.create_time.desc()
        ).limit(limit).all()
        return [
            {
                "task_id": t.task_id,
                "task_type": t.task_type,
                "status": t.status,
                "progress": t.progress,
                "current_step": t.current_step,
                "total_steps": t.total_steps,
                "processed_days": t.processed_days,
                "total_days": t.total_days,
                "error_message": t.error_message,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "end_time": t.end_time.isoformat() if t.end_time else None,
                "create_time": t.create_time.isoformat() if t.create_time else None,
            }
            for t in tasks
        ]
    finally:
        db.close()


def cancel_task(task_id: str) -> bool:
    global running_task_id
    
    db = LocalSessionLocal()
    try:
        task = db.query(LocalAggregationTask).filter(
            LocalAggregationTask.task_id == task_id
        ).first()
        if task and task.status in ["pending", "running"]:
            task.status = "cancelled"
            task.end_time = datetime.now()
            db.commit()
            
            with task_lock:
                if running_task_id == task_id:
                    running_task_id = None
            
            return True
        return False
    finally:
        db.close()


def execute_aggregation_task(task_id: str):
    global running_task_id
    
    target_dates_json = None
    db = LocalSessionLocal()
    try:
        task = db.query(LocalAggregationTask).filter(
            LocalAggregationTask.task_id == task_id
        ).first()
        if not task:
            return
        
        if task.status == "cancelled":
            return
        
        target_dates_json = task.target_dates
        
        task.status = "running"
        task.start_time = datetime.now()
        db.commit()
    finally:
        db.close()
    
    main_db = None
    local_db = None
    try:
        main_db = SessionLocal()
        local_db = LocalSessionLocal()
        aggregator = DataAggregator(main_db, local_db)
        
        target_dates = json.loads(target_dates_json)
        target_dates = [date.fromisoformat(d) for d in target_dates]
        
        total_steps = len(target_dates) * 6
        current_step = 0
        
        steps = [
            ('daily_summary', '日汇总'),
            ('device_summary', '设备汇总'),
            ('device_hourly', '设备小时数据'),
            ('org_summary', '组织汇总'),
            ('statistics', '统计数据'),
            ('org_hourly', '组织小时数据')
        ]
        
        for i, dt in enumerate(target_dates):
            db = LocalSessionLocal()
            try:
                t = db.query(LocalAggregationTask).filter(
                    LocalAggregationTask.task_id == task_id
                ).first()
                if t and t.status == "cancelled":
                    return
            finally:
                db.close()
            
            date_str = dt.strftime("%Y-%m-%d")
            
            update_task_progress(
                task_id,
                processed_days=i + 1,
                current_step=f"处理 {date_str}"
            )
            
            for step_name, step_desc in steps:
                db = LocalSessionLocal()
                try:
                    t = db.query(LocalAggregationTask).filter(
                        LocalAggregationTask.task_id == task_id
                    ).first()
                    if t and t.status == "cancelled":
                        return
                finally:
                    db.close()
                
                current_step += 1
                progress = int((current_step / total_steps) * 100)
                
                update_task_progress(
                    task_id,
                    progress=progress,
                    current_step=f"{date_str} - {step_desc}"
                )
                
                if step_name == 'daily_summary':
                    aggregator.aggregate_daily_summary(dt)
                elif step_name == 'device_summary':
                    aggregator.aggregate_device_summary(dt)
                elif step_name == 'device_hourly':
                    aggregator.aggregate_device_hourly_stats(dt)
                elif step_name == 'org_summary':
                    aggregator.aggregate_org_summary(dt)
                elif step_name == 'statistics':
                    aggregator.aggregate_statistics_data(dt)
                elif step_name == 'org_hourly':
                    aggregator.aggregate_org_hourly_stats(dt)
        
        update_task_progress(
            task_id,
            status="completed",
            progress=100,
            current_step="完成",
            end_time=datetime.now()
        )
        
    except Exception as e:
        update_task_progress(
            task_id,
            status="failed",
            error_message=str(e),
            end_time=datetime.now()
        )
    finally:
        if main_db:
            main_db.close()
        if local_db:
            local_db.close()
        
        with task_lock:
            if running_task_id == task_id:
                running_task_id = None


def start_aggregation_task(target_dates: List[date]) -> Optional[str]:
    task_id = create_task("refresh", target_dates)
    if not task_id:
        return None
    
    thread = threading.Thread(
        target=execute_aggregation_task,
        args=(task_id,),
        daemon=True
    )
    thread.start()
    
    return task_id


def get_running_task_id() -> Optional[str]:
    global running_task_id
    with task_lock:
        return running_task_id

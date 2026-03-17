import hashlib
import secrets
import json
import asyncio
from datetime import datetime, date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.local_database import get_local_db
from app.local_models import LocalSystemConfig, LocalDailyGpuUsageSummary, LocalDailyDeviceSummary, LocalOrgGpuUsageSummary, LocalStatisticsData, LocalOrgHourlyStats
from app.aggregator import DataAggregator
from app.database import SessionLocal


router = APIRouter()


ADMIN_PASSWORD_KEY = "admin_password"
DEFAULT_PASSWORD = "admin123"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(stored_hash: str, provided_password: str) -> bool:
    return stored_hash == hash_password(provided_password)


def get_or_create_password_config(db: Session) -> LocalSystemConfig:
    config = db.query(LocalSystemConfig).filter(
        LocalSystemConfig.config_key == ADMIN_PASSWORD_KEY
    ).first()
    
    if not config:
        config = LocalSystemConfig(
            config_key=ADMIN_PASSWORD_KEY,
            config_value=hash_password(DEFAULT_PASSWORD),
            description="管理员密码(SHA256加密)"
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return config


class PasswordVerifyRequest(BaseModel):
    password: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class ConfigUpdateRequest(BaseModel):
    work_hour_start: Optional[int] = None
    work_hour_end: Optional[int] = None
    high_usage_threshold: Optional[float] = None
    low_usage_threshold: Optional[float] = None


class ConfigResponse(BaseModel):
    work_hour_start: int
    work_hour_end: int
    high_usage_threshold: float
    low_usage_threshold: float


class AggregationRequest(BaseModel):
    days: int = 1


@router.post("/verify-password")
def verify_admin_password(request: PasswordVerifyRequest, db: Session = Depends(get_local_db)):
    config = get_or_create_password_config(db)
    
    if verify_password(config.config_value, request.password):
        return {"success": True, "message": "密码验证成功"}
    else:
        raise HTTPException(status_code=401, detail="密码错误")


@router.post("/change-password")
def change_admin_password(request: PasswordChangeRequest, db: Session = Depends(get_local_db)):
    config = get_or_create_password_config(db)
    
    if not verify_password(config.config_value, request.old_password):
        raise HTTPException(status_code=401, detail="原密码错误")
    
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")
    
    config.config_value = hash_password(request.new_password)
    config.update_time = datetime.now()
    db.commit()
    
    return {"success": True, "message": "密码修改成功"}


@router.get("/config", response_model=ConfigResponse)
def get_system_config(db: Session = Depends(get_local_db)):
    configs = db.query(LocalSystemConfig).all()
    config_map = {c.config_key: c.config_value for c in configs}
    
    return ConfigResponse(
        work_hour_start=int(config_map.get("work_hour_start", 9)),
        work_hour_end=int(config_map.get("work_hour_end", 18)),
        high_usage_threshold=float(config_map.get("high_usage_threshold", 60.0)),
        low_usage_threshold=float(config_map.get("low_usage_threshold", 30.0))
    )


@router.put("/config")
def update_system_config(request: ConfigUpdateRequest, db: Session = Depends(get_local_db)):
    updates = []
    
    if request.work_hour_start is not None:
        if request.work_hour_start < 0 or request.work_hour_start > 23:
            raise HTTPException(status_code=400, detail="工作开始时间必须在0-23之间")
        config = db.query(LocalSystemConfig).filter(
            LocalSystemConfig.config_key == "work_hour_start"
        ).first()
        if config:
            config.config_value = str(request.work_hour_start)
            config.update_time = datetime.now()
        else:
            config = LocalSystemConfig(
                config_key="work_hour_start",
                config_value=str(request.work_hour_start),
                description="工作时段开始时间"
            )
            db.add(config)
        updates.append("work_hour_start")
    
    if request.work_hour_end is not None:
        if request.work_hour_end < 0 or request.work_hour_end > 23:
            raise HTTPException(status_code=400, detail="工作结束时间必须在0-23之间")
        config = db.query(LocalSystemConfig).filter(
            LocalSystemConfig.config_key == "work_hour_end"
        ).first()
        if config:
            config.config_value = str(request.work_hour_end)
            config.update_time = datetime.now()
        else:
            config = LocalSystemConfig(
                config_key="work_hour_end",
                config_value=str(request.work_hour_end),
                description="工作时段结束时间"
            )
            db.add(config)
        updates.append("work_hour_end")
    
    if request.high_usage_threshold is not None:
        if request.high_usage_threshold < 0 or request.high_usage_threshold > 100:
            raise HTTPException(status_code=400, detail="高使用率阈值必须在0-100之间")
        config = db.query(LocalSystemConfig).filter(
            LocalSystemConfig.config_key == "high_usage_threshold"
        ).first()
        if config:
            config.config_value = str(request.high_usage_threshold)
            config.update_time = datetime.now()
        else:
            config = LocalSystemConfig(
                config_key="high_usage_threshold",
                config_value=str(request.high_usage_threshold),
                description="高使用率阈值(%)"
            )
            db.add(config)
        updates.append("high_usage_threshold")
    
    if request.low_usage_threshold is not None:
        if request.low_usage_threshold < 0 or request.low_usage_threshold > 100:
            raise HTTPException(status_code=400, detail="低使用率阈值必须在0-100之间")
        config = db.query(LocalSystemConfig).filter(
            LocalSystemConfig.config_key == "low_usage_threshold"
        ).first()
        if config:
            config.config_value = str(request.low_usage_threshold)
            config.update_time = datetime.now()
        else:
            config = LocalSystemConfig(
                config_key="low_usage_threshold",
                config_value=str(request.low_usage_threshold),
                description="低使用率阈值(%)"
            )
            db.add(config)
        updates.append("low_usage_threshold")
    
    db.commit()
    
    return {"success": True, "message": f"配置更新成功: {', '.join(updates)}"}


@router.get("/aggregation/refresh")
async def refresh_aggregation(days: int = 1, db: Session = Depends(get_local_db)):
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="天数必须在1-365之间")
    
    async def generate_progress():
        main_db = SessionLocal()
        try:
            aggregator = DataAggregator(main_db, db)
            total_steps = days * 5
            current_step = 0
            
            yield f"data: {json.dumps({'type': 'start', 'total_steps': total_steps, 'days': days})}\n\n"
            await asyncio.sleep(0)
            
            for i in range(days):
                target_date = date.today() - timedelta(days=i+1)
                date_str = target_date.strftime("%Y-%m-%d")
                
                yield f"data: {json.dumps({'type': 'day_start', 'day': i+1, 'total_days': days, 'date': date_str})}\n\n"
                await asyncio.sleep(0)
                
                steps = [
                    ('daily_summary', '日汇总'),
                    ('device_summary', '设备汇总'),
                    ('org_summary', '组织汇总'),
                    ('statistics', '统计数据'),
                    ('org_hourly', '组织小时数据')
                ]
                
                for step_name, step_desc in steps:
                    current_step += 1
                    progress = int((current_step / total_steps) * 100)
                    yield f"data: {json.dumps({'type': 'progress', 'step': current_step, 'total_steps': total_steps, 'progress': progress, 'current_task': f'{date_str} - {step_desc}'})}\n\n"
                    await asyncio.sleep(0)
                    
                    if step_name == 'daily_summary':
                        aggregator.aggregate_daily_summary(target_date)
                    elif step_name == 'device_summary':
                        aggregator.aggregate_device_summary(target_date)
                    elif step_name == 'org_summary':
                        aggregator.aggregate_org_summary(target_date)
                    elif step_name == 'statistics':
                        aggregator.aggregate_statistics_data(target_date)
                    elif step_name == 'org_hourly':
                        aggregator.aggregate_org_hourly_stats(target_date)
                    
                    await asyncio.sleep(0)
            
            yield f"data: {json.dumps({'type': 'complete', 'success': True, 'message': f'成功刷新 {days} 天的聚合数据'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'success': False, 'message': f'刷新失败: {str(e)}'})}\n\n"
        finally:
            main_db.close()
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/aggregation/reset")
def reset_aggregation(db: Session = Depends(get_local_db)):
    try:
        db.query(LocalDailyGpuUsageSummary).delete()
        db.query(LocalDailyDeviceSummary).delete()
        db.query(LocalOrgGpuUsageSummary).delete()
        db.query(LocalStatisticsData).delete()
        db.query(LocalOrgHourlyStats).delete()
        db.commit()
        
        return {
            "success": True,
            "message": "聚合数据已重置，请点击刷新重新生成数据"
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"重置失败: {str(e)}"}


@router.get("/aggregation/status")
def get_aggregation_status(db: Session = Depends(get_local_db)):
    daily_count = db.query(func.count(LocalDailyGpuUsageSummary.id)).scalar()
    device_count = db.query(func.count(LocalDailyDeviceSummary.id)).scalar()
    org_count = db.query(func.count(LocalOrgGpuUsageSummary.id)).scalar()
    stats_count = db.query(func.count(LocalStatisticsData.id)).scalar()
    org_hourly_count = db.query(func.count(LocalOrgHourlyStats.id)).scalar()
    
    latest_daily = db.query(LocalDailyGpuUsageSummary).order_by(
        LocalDailyGpuUsageSummary.summary_date.desc()
    ).first()
    
    latest_time = None
    if latest_daily:
        latest_time = latest_daily.summary_date.strftime("%Y-%m-%d")
    
    return {
        "daily_summary_count": daily_count,
        "device_summary_count": device_count,
        "org_summary_count": org_count,
        "statistics_count": stats_count,
        "org_hourly_count": org_hourly_count,
        "latest_aggregation_time": latest_time
    }

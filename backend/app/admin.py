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
from app.local_models import LocalSystemConfig, LocalDailyGpuUsageSummary, LocalDailyDeviceSummary, LocalOrgGpuUsageSummary, LocalStatisticsData, LocalOrgHourlyStats, LocalPurposeDict
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
async def refresh_aggregation(days: int = 1, target_date_str: Optional[str] = None, db: Session = Depends(get_local_db)):
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="天数必须在1-365之间")
    
    async def generate_progress():
        main_db = SessionLocal()
        try:
            aggregator = DataAggregator(main_db, db)
            
            target_dates = []
            if target_date_str:
                try:
                    single_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
                    target_dates = [single_date]
                except ValueError:
                    yield f"data: {json.dumps({'type': 'error', 'success': False, 'message': '日期格式错误，请使用YYYY-MM-DD格式'})}\n\n"
                    return
            else:
                for i in range(days):
                    dt = date.today() - timedelta(days=i+1)
                    target_dates.append(dt)
            
            total_steps = len(target_dates) * 6
            current_step = 0
            
            yield f"data: {json.dumps({'type': 'start', 'total_steps': total_steps, 'days': len(target_dates)})}\n\n"
            await asyncio.sleep(0)
            
            for i, dt in enumerate(target_dates):
                date_str = dt.strftime("%Y-%m-%d")
                
                yield f"data: {json.dumps({'type': 'day_start', 'day': i+1, 'total_days': len(target_dates), 'date': date_str})}\n\n"
                await asyncio.sleep(0)
                
                steps = [
                    ('daily_summary', '日汇总'),
                    ('device_summary', '设备汇总'),
                    ('device_hourly', '设备小时数据'),
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
                    
                    await asyncio.sleep(0)
            
            yield f"data: {json.dumps({'type': 'complete', 'success': True, 'message': f'成功刷新 {len(target_dates)} 天的聚合数据'})}\n\n"
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


class PurposeDictRequest(BaseModel):
    dict_label: str
    dict_value: int
    dict_sort: int = 0
    status: int = 1
    remark: str = ""


class PurposeStatusRequest(BaseModel):
    status: int


@router.post("/dict/purpose")
def create_purpose(request: PurposeDictRequest, db: Session = Depends(get_local_db)):
    # 检查dict_value是否已存在
    existing = db.query(LocalPurposeDict).filter(
        LocalPurposeDict.dict_type == "device_purpose",
        LocalPurposeDict.dict_value == request.dict_value
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="设备用途值已存在")
    
    # 检查dict_label是否已存在
    existing_label = db.query(LocalPurposeDict).filter(
        LocalPurposeDict.dict_type == "device_purpose",
        LocalPurposeDict.dict_label == request.dict_label
    ).first()
    
    if existing_label:
        raise HTTPException(status_code=400, detail="设备用途标签已存在")
    
    # 获取最大ID
    max_id = db.query(func.max(LocalPurposeDict.id)).scalar() or 0
    
    purpose = LocalPurposeDict(
        id=max_id + 1,
        dict_type="device_purpose",
        dict_label=request.dict_label,
        dict_value=request.dict_value,
        dict_sort=request.dict_sort,
        status=request.status,
        remark=request.remark,
        deleted=0
    )
    
    db.add(purpose)
    db.commit()
    db.refresh(purpose)
    
    return {"success": True, "message": "设备用途添加成功", "data": {
        "id": purpose.id,
        "dict_label": purpose.dict_label,
        "dict_value": purpose.dict_value,
        "dict_sort": purpose.dict_sort,
        "status": purpose.status,
        "remark": purpose.remark
    }}


@router.put("/dict/purpose/{purpose_id}")
def update_purpose(purpose_id: int, request: PurposeDictRequest, db: Session = Depends(get_local_db)):
    purpose = db.query(LocalPurposeDict).filter(
        LocalPurposeDict.id == purpose_id,
        LocalPurposeDict.dict_type == "device_purpose"
    ).first()
    
    if not purpose:
        raise HTTPException(status_code=404, detail="设备用途不存在")
    
    # 检查dict_value是否已被其他记录使用
    existing = db.query(LocalPurposeDict).filter(
        LocalPurposeDict.dict_type == "device_purpose",
        LocalPurposeDict.dict_value == request.dict_value,
        LocalPurposeDict.id != purpose_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="设备用途值已存在")
    
    # 检查dict_label是否已被其他记录使用
    existing_label = db.query(LocalPurposeDict).filter(
        LocalPurposeDict.dict_type == "device_purpose",
        LocalPurposeDict.dict_label == request.dict_label,
        LocalPurposeDict.id != purpose_id
    ).first()
    
    if existing_label:
        raise HTTPException(status_code=400, detail="设备用途标签已存在")
    
    purpose.dict_label = request.dict_label
    purpose.dict_value = request.dict_value
    purpose.dict_sort = request.dict_sort
    purpose.status = request.status
    purpose.remark = request.remark
    purpose.update_time = datetime.now()
    
    db.commit()
    db.refresh(purpose)
    
    return {"success": True, "message": "设备用途更新成功", "data": {
        "id": purpose.id,
        "dict_label": purpose.dict_label,
        "dict_value": purpose.dict_value,
        "dict_sort": purpose.dict_sort,
        "status": purpose.status,
        "remark": purpose.remark
    }}


@router.patch("/dict/purpose/{purpose_id}/status")
def update_purpose_status(purpose_id: int, request: PurposeStatusRequest, db: Session = Depends(get_local_db)):
    purpose = db.query(LocalPurposeDict).filter(
        LocalPurposeDict.id == purpose_id,
        LocalPurposeDict.dict_type == "device_purpose"
    ).first()
    
    if not purpose:
        raise HTTPException(status_code=404, detail="设备用途不存在")
    
    if request.status not in [0, 1]:
        raise HTTPException(status_code=400, detail="状态值必须为0或1")
    
    purpose.status = request.status
    purpose.update_time = datetime.now()
    
    db.commit()
    
    return {"success": True, "message": "状态更新成功"}


@router.delete("/dict/purpose/{purpose_id}")
def delete_purpose(purpose_id: int, db: Session = Depends(get_local_db)):
    purpose = db.query(LocalPurposeDict).filter(
        LocalPurposeDict.id == purpose_id,
        LocalPurposeDict.dict_type == "device_purpose"
    ).first()
    
    if not purpose:
        raise HTTPException(status_code=404, detail="设备用途不存在")
    
    # 软删除
    purpose.deleted = 1
    purpose.update_time = datetime.now()
    
    db.commit()
    
    return {"success": True, "message": "设备用途删除成功"}

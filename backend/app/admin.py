import hashlib
import secrets
import json
import asyncio
import os
from datetime import datetime, date, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.local_database import get_local_db, LOCAL_DB_PATH, local_engine
from app.local_models import LocalSystemConfig, LocalDailyGpuUsageSummary, LocalDailyDeviceSummary, LocalOrgGpuUsageSummary, LocalStatisticsData, LocalOrgHourlyStats, LocalPurposeDict, LocalGpuTierDict, LocalCacheMetadata
from app.gpu_tier_utils import GPUTierManager
from app.aggregator import DataAggregator
from app.database import SessionLocal, engine
from app import task_executor


router = APIRouter()

_aggregation_config_changed_callback = None


def set_aggregation_config_changed_callback(callback):
    global _aggregation_config_changed_callback
    _aggregation_config_changed_callback = callback


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
    auto_aggregation_enabled: Optional[bool] = None
    auto_aggregation_hour: Optional[int] = None
    auto_aggregation_minute: Optional[int] = None


class ConfigResponse(BaseModel):
    work_hour_start: int
    work_hour_end: int
    high_usage_threshold: float
    low_usage_threshold: float
    auto_aggregation_enabled: bool
    auto_aggregation_hour: int
    auto_aggregation_minute: int


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
        low_usage_threshold=float(config_map.get("low_usage_threshold", 30.0)),
        auto_aggregation_enabled=config_map.get("auto_aggregation_enabled", "true").lower() == "true",
        auto_aggregation_hour=int(config_map.get("auto_aggregation_hour", 1)),
        auto_aggregation_minute=int(config_map.get("auto_aggregation_minute", 0))
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
    
    if request.auto_aggregation_enabled is not None:
        config = db.query(LocalSystemConfig).filter(
            LocalSystemConfig.config_key == "auto_aggregation_enabled"
        ).first()
        if config:
            config.config_value = str(request.auto_aggregation_enabled).lower()
            config.update_time = datetime.now()
        else:
            config = LocalSystemConfig(
                config_key="auto_aggregation_enabled",
                config_value=str(request.auto_aggregation_enabled).lower(),
                description="自动聚合任务开关"
            )
            db.add(config)
        updates.append("auto_aggregation_enabled")
    
    if request.auto_aggregation_hour is not None:
        if request.auto_aggregation_hour < 0 or request.auto_aggregation_hour > 23:
            raise HTTPException(status_code=400, detail="自动聚合小时必须在0-23之间")
        config = db.query(LocalSystemConfig).filter(
            LocalSystemConfig.config_key == "auto_aggregation_hour"
        ).first()
        if config:
            config.config_value = str(request.auto_aggregation_hour)
            config.update_time = datetime.now()
        else:
            config = LocalSystemConfig(
                config_key="auto_aggregation_hour",
                config_value=str(request.auto_aggregation_hour),
                description="自动聚合执行小时"
            )
            db.add(config)
        updates.append("auto_aggregation_hour")
    
    if request.auto_aggregation_minute is not None:
        if request.auto_aggregation_minute < 0 or request.auto_aggregation_minute > 59:
            raise HTTPException(status_code=400, detail="自动聚合分钟必须在0-59之间")
        config = db.query(LocalSystemConfig).filter(
            LocalSystemConfig.config_key == "auto_aggregation_minute"
        ).first()
        if config:
            config.config_value = str(request.auto_aggregation_minute)
            config.update_time = datetime.now()
        else:
            config = LocalSystemConfig(
                config_key="auto_aggregation_minute",
                config_value=str(request.auto_aggregation_minute),
                description="自动聚合执行分钟"
            )
            db.add(config)
        updates.append("auto_aggregation_minute")
    
    db.commit()
    
    if _aggregation_config_changed_callback and any(u in updates for u in ["auto_aggregation_enabled", "auto_aggregation_hour", "auto_aggregation_minute"]):
        _aggregation_config_changed_callback()
    
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
    
    running_task_id = task_executor.get_running_task_id()
    
    return {
        "daily_summary_count": daily_count,
        "device_summary_count": device_count,
        "org_summary_count": org_count,
        "statistics_count": stats_count,
        "org_hourly_count": org_hourly_count,
        "latest_aggregation_time": latest_time,
        "running_task_id": running_task_id
    }


class CreateTaskRequest(BaseModel):
    days: Optional[int] = 1
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@router.post("/aggregation/tasks")
def create_aggregation_task(request: CreateTaskRequest):
    running_task_id = task_executor.get_running_task_id()
    if running_task_id:
        raise HTTPException(status_code=400, detail="已有任务正在运行，请等待完成或取消后再试")
    
    target_dates = []
    
    if request.start_date and request.end_date:
        try:
            start = datetime.strptime(request.start_date, "%Y-%m-%d").date()
            end = datetime.strptime(request.end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
        
        if start > end:
            raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")
        
        days_diff = (end - start).days + 1
        if days_diff > 365:
            raise HTTPException(status_code=400, detail="日期范围不能超过365天")
        
        current = start
        while current <= end:
            target_dates.append(current)
            current += timedelta(days=1)
    else:
        if request.days < 1 or request.days > 365:
            raise HTTPException(status_code=400, detail="天数必须在1-365之间")
        
        for i in range(request.days):
            dt = date.today() - timedelta(days=i+1)
            target_dates.append(dt)
    
    task_id = task_executor.start_aggregation_task(target_dates)
    if not task_id:
        raise HTTPException(status_code=500, detail="创建任务失败")
    
    return {
        "success": True,
        "task_id": task_id,
        "message": f"已创建刷新任务，共 {len(target_dates)} 天"
    }


@router.get("/aggregation/tasks/{task_id}")
def get_task_status(task_id: str):
    task = task_executor.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/aggregation/tasks")
def get_task_list(limit: int = 10):
    tasks = task_executor.get_recent_tasks(limit)
    return {"tasks": tasks}


@router.post("/aggregation/tasks/{task_id}/cancel")
def cancel_aggregation_task(task_id: str):
    success = task_executor.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="无法取消任务，任务可能已完成或已取消")
    return {"success": True, "message": "任务已取消"}


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


@router.get("/database/status")
def get_database_status(local_db: Session = Depends(get_local_db)):
    result = {
        "main_database": {
            "status": "unknown",
            "host": None,
            "port": None,
            "database": None,
            "connection_pool": None,
            "error": None
        },
        "local_database": {
            "status": "unknown",
            "path": LOCAL_DB_PATH,
            "size_mb": 0,
            "size_human": "0 MB",
            "tables": {},
            "error": None
        },
        "cache_status": []
    }
    
    # 检测主数据库状态
    try:
        from app.config import settings
        result["main_database"]["host"] = settings.DB_HOST
        result["main_database"]["port"] = settings.DB_PORT
        result["main_database"]["database"] = settings.DB_NAME
        
        main_db = SessionLocal()
        try:
            main_db.execute(text("SELECT 1"))
            result["main_database"]["status"] = "connected"
            
            # 获取连接池状态
            pool = engine.pool
            pool_info = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow()
            }
            # invalidatedcount 方法可能不存在于所有版本
            try:
                pool_info["invalid"] = pool.invalidatedcount()
            except AttributeError:
                pool_info["invalid"] = 0
            result["main_database"]["connection_pool"] = pool_info
        finally:
            main_db.close()
    except Exception as e:
        result["main_database"]["status"] = "disconnected"
        result["main_database"]["error"] = str(e)
    
    # 检测本地数据库状态
    try:
        # 检查文件是否存在并获取大小
        if os.path.exists(LOCAL_DB_PATH):
            file_size = os.path.getsize(LOCAL_DB_PATH)
            result["local_database"]["size_mb"] = round(file_size / (1024 * 1024), 2)
            if file_size >= 1024 * 1024 * 1024:
                result["local_database"]["size_human"] = f"{round(file_size / (1024 * 1024 * 1024), 2)} GB"
            elif file_size >= 1024 * 1024:
                result["local_database"]["size_human"] = f"{round(file_size / (1024 * 1024), 2)} MB"
            elif file_size >= 1024:
                result["local_database"]["size_human"] = f"{round(file_size / 1024, 2)} KB"
            else:
                result["local_database"]["size_human"] = f"{file_size} Bytes"
        
        # 测试连接
        local_db.execute(text("SELECT 1"))
        result["local_database"]["status"] = "connected"
        
        # 获取各表记录数
        tables_to_check = [
            ("cached_organization", "组织缓存"),
            ("cached_device", "设备缓存"),
            ("cached_gpu_card_info", "GPU卡信息缓存"),
            ("cached_network", "网络缓存"),
            ("daily_gpu_usage_summary", "日GPU使用汇总"),
            ("daily_device_summary", "日设备汇总"),
            ("org_gpu_usage_summary", "组织GPU使用汇总"),
            ("device_hourly_stats", "设备小时统计"),
            ("org_hourly_stats", "组织小时统计"),
            ("statistics_data", "统计数据"),
            ("cache_metadata", "缓存元数据"),
            ("aggregation_task", "聚合任务")
        ]
        
        for table_name, display_name in tables_to_check:
            try:
                count = local_db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                result["local_database"]["tables"][table_name] = {
                    "display_name": display_name,
                    "count": count
                }
            except Exception:
                result["local_database"]["tables"][table_name] = {
                    "display_name": display_name,
                    "count": 0,
                    "error": "表不存在或查询失败"
                }
        
        # 获取SQLite页面信息
        try:
            page_count = local_db.execute(text("PRAGMA page_count")).scalar()
            page_size = local_db.execute(text("PRAGMA page_size")).scalar()
            result["local_database"]["sqlite_info"] = {
                "page_count": page_count,
                "page_size": page_size,
                "journal_mode": local_db.execute(text("PRAGMA journal_mode")).scalar(),
                "synchronous": local_db.execute(text("PRAGMA synchronous")).scalar()
            }
        except Exception:
            pass
            
    except Exception as e:
        result["local_database"]["status"] = "disconnected"
        result["local_database"]["error"] = str(e)
    
    # 获取缓存同步状态
    try:
        cache_metadata = local_db.query(LocalCacheMetadata).all()
        for m in cache_metadata:
            result["cache_status"].append({
                "cache_name": m.cache_name,
                "last_sync_time": m.last_sync_time.isoformat() if m.last_sync_time else None,
                "sync_interval_seconds": m.sync_interval_seconds,
                "record_count": m.record_count,
                "status": m.status,
                "error_message": m.error_message
            })
    except Exception as e:
        pass
    
    return result


@router.get("/database/test-connection")
def test_database_connection():
    results = {
        "main_database": {"success": False, "latency_ms": None, "error": None},
        "local_database": {"success": False, "latency_ms": None, "error": None}
    }
    
    # 测试主数据库连接
    import time
    try:
        start_time = time.time()
        main_db = SessionLocal()
        try:
            main_db.execute(text("SELECT 1"))
            latency = (time.time() - start_time) * 1000
            results["main_database"]["success"] = True
            results["main_database"]["latency_ms"] = round(latency, 2)
        finally:
            main_db.close()
    except Exception as e:
        results["main_database"]["error"] = str(e)
    
    # 测试本地数据库连接
    try:
        start_time = time.time()
        local_db = next(get_local_db())
        try:
            local_db.execute(text("SELECT 1"))
            latency = (time.time() - start_time) * 1000
            results["local_database"]["success"] = True
            results["local_database"]["latency_ms"] = round(latency, 2)
        finally:
            local_db.close()
    except Exception as e:
        results["local_database"]["error"] = str(e)
    
    return results


class GpuTierDictRequest(BaseModel):
    dict_label: str
    dict_value: int
    dict_sort: int = 0
    status: int = 1
    remark: str = ""


class GpuTierStatusRequest(BaseModel):
    status: int


@router.get("/dict/gpu-tier")
def get_gpu_tier_list(db: Session = Depends(get_local_db)):
    tiers = db.query(LocalGpuTierDict).filter(
        LocalGpuTierDict.dict_type == "gpu_tier",
        LocalGpuTierDict.deleted == 0
    ).order_by(LocalGpuTierDict.dict_sort).all()

    return [
        {
            "id": tier.id,
            "dict_label": tier.dict_label,
            "dict_value": tier.dict_value,
            "dict_sort": tier.dict_sort,
            "status": tier.status,
            "remark": tier.remark
        }
        for tier in tiers
    ]


@router.post("/dict/gpu-tier")
def create_gpu_tier(request: GpuTierDictRequest, db: Session = Depends(get_local_db)):
    existing = db.query(LocalGpuTierDict).filter(
        LocalGpuTierDict.dict_type == "gpu_tier",
        LocalGpuTierDict.dict_value == request.dict_value
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="档次值已存在")

    existing_label = db.query(LocalGpuTierDict).filter(
        LocalGpuTierDict.dict_type == "gpu_tier",
        LocalGpuTierDict.dict_label == request.dict_label
    ).first()

    if existing_label:
        raise HTTPException(status_code=400, detail="档次名称已存在")

    max_id = db.query(func.max(LocalGpuTierDict.id)).scalar() or 0

    tier = LocalGpuTierDict(
        id=max_id + 1,
        dict_type="gpu_tier",
        dict_label=request.dict_label,
        dict_value=request.dict_value,
        dict_sort=request.dict_sort,
        status=request.status,
        remark=request.remark,
        deleted=0
    )

    db.add(tier)
    db.commit()
    db.refresh(tier)

    return {"success": True, "message": "GPU档次添加成功", "data": {
        "id": tier.id,
        "dict_label": tier.dict_label,
        "dict_value": tier.dict_value,
        "dict_sort": tier.dict_sort,
        "status": tier.status,
        "remark": tier.remark
    }}


@router.get("/dict/gpu-tier/{tier_id}")
def get_gpu_tier(tier_id: int, db: Session = Depends(get_local_db)):
    tier = db.query(LocalGpuTierDict).filter(
        LocalGpuTierDict.id == tier_id,
        LocalGpuTierDict.dict_type == "gpu_tier"
    ).first()

    if not tier:
        raise HTTPException(status_code=404, detail="GPU档次不存在")

    return {
        "id": tier.id,
        "dict_label": tier.dict_label,
        "dict_value": tier.dict_value,
        "dict_sort": tier.dict_sort,
        "status": tier.status,
        "remark": tier.remark
    }


@router.put("/dict/gpu-tier/{tier_id}")
def update_gpu_tier(tier_id: int, request: GpuTierDictRequest, db: Session = Depends(get_local_db)):
    tier = db.query(LocalGpuTierDict).filter(
        LocalGpuTierDict.id == tier_id,
        LocalGpuTierDict.dict_type == "gpu_tier"
    ).first()

    if not tier:
        raise HTTPException(status_code=404, detail="GPU档次不存在")

    existing = db.query(LocalGpuTierDict).filter(
        LocalGpuTierDict.dict_type == "gpu_tier",
        LocalGpuTierDict.dict_value == request.dict_value,
        LocalGpuTierDict.id != tier_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="档次值已存在")

    existing_label = db.query(LocalGpuTierDict).filter(
        LocalGpuTierDict.dict_type == "gpu_tier",
        LocalGpuTierDict.dict_label == request.dict_label,
        LocalGpuTierDict.id != tier_id
    ).first()

    if existing_label:
        raise HTTPException(status_code=400, detail="档次名称已存在")

    tier.dict_label = request.dict_label
    tier.dict_value = request.dict_value
    tier.dict_sort = request.dict_sort
    tier.status = request.status
    tier.remark = request.remark
    tier.update_time = datetime.now()

    db.commit()
    db.refresh(tier)

    return {"success": True, "message": "GPU档次更新成功", "data": {
        "id": tier.id,
        "dict_label": tier.dict_label,
        "dict_value": tier.dict_value,
        "dict_sort": tier.dict_sort,
        "status": tier.status,
        "remark": tier.remark
    }}


@router.patch("/dict/gpu-tier/{tier_id}/status")
def update_gpu_tier_status(tier_id: int, request: GpuTierStatusRequest, db: Session = Depends(get_local_db)):
    tier = db.query(LocalGpuTierDict).filter(
        LocalGpuTierDict.id == tier_id,
        LocalGpuTierDict.dict_type == "gpu_tier"
    ).first()

    if not tier:
        raise HTTPException(status_code=404, detail="GPU档次不存在")

    if request.status not in [0, 1]:
        raise HTTPException(status_code=400, detail="状态值必须为0或1")

    tier.status = request.status
    tier.update_time = datetime.now()

    db.commit()

    return {"success": True, "message": "状态更新成功"}


@router.delete("/dict/gpu-tier/{tier_id}")
def delete_gpu_tier(tier_id: int, db: Session = Depends(get_local_db)):
    tier = db.query(LocalGpuTierDict).filter(
        LocalGpuTierDict.id == tier_id,
        LocalGpuTierDict.dict_type == "gpu_tier"
    ).first()

    if not tier:
        raise HTTPException(status_code=404, detail="GPU档次不存在")

    tier.deleted = 1
    tier.update_time = datetime.now()

    db.commit()

    return {"success": True, "message": "GPU档次删除成功"}

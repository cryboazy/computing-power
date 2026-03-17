from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, desc, literal_column
from sqlalchemy.sql import text
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.database import get_db
from app.local_database import get_local_db
from app.models import (
    Device, DeviceGpuMonitor, 
    GpuCardInfo, Organization, Network
)
from app.local_models import (
    LocalDailyGpuUsageSummary, LocalDailyDeviceSummary, 
    LocalOrgGpuUsageSummary, LocalStatisticsData, LocalSystemConfig, LocalOrgHourlyStats
)
from app.config import settings
from app.org_constants import ORG_CODE_CHINA


router = APIRouter()

ONLINE_THRESHOLD_MINUTES = 10

def sqlite_date_format(column, format_str):
    if format_str == 'YYYY-MM-DD':
        return func.strftime('%Y-%m-%d', column)
    elif format_str == 'YYYY-MM':
        return func.strftime('%Y-%m', column)
    elif format_str == 'YYYY-"W"IW':
        return func.strftime('%Y-W%W', column)
    elif format_str == 'HH24':
        return func.strftime('%H', column)
    return func.strftime('%Y-%m-%d', column)

def get_second_level_groups(db: Session) -> list:
    china_org = db.query(Organization).filter(
        Organization.code == ORG_CODE_CHINA,
        Organization.deleted == 0
    ).first()
    if not china_org:
        return []
    groups = db.query(Organization).filter(
        Organization.parent_id == china_org.id,
        Organization.deleted == 0
    ).all()
    return groups

def get_org_ids_by_parent(db: Session, parent_id: int) -> list:
    result = []
    orgs = db.query(Organization).filter(
        Organization.parent_id == parent_id,
        Organization.deleted == 0
    ).all()
    for org in orgs:
        result.append(org.id)
        result.extend(get_org_ids_by_parent(db, org.id))
    return result

def get_org_ids_by_type(db: Session, org_type: str) -> list:
    groups = get_second_level_groups(db)
    for group in groups:
        if org_type == 'local' and '地方厅局' in group.name:
            return get_org_ids_by_parent(db, group.id)
        elif org_type == 'central' and '部机关' in group.name:
            return get_org_ids_by_parent(db, group.id)
    return []

def check_device_online(db: Session, device_id: int) -> int:
    latest_monitor = db.query(DeviceGpuMonitor).filter(
        DeviceGpuMonitor.device_id == device_id
    ).order_by(desc(DeviceGpuMonitor.collection_timestamp)).first()
    
    if not latest_monitor:
        return 0
    
    time_diff = datetime.now() - latest_monitor.collection_timestamp
    if time_diff.total_seconds() < ONLINE_THRESHOLD_MINUTES * 60:
        return 1
    return 0


class TimeRangeParams:
    def __init__(
        self,
        time_range: str = Query("month", description="时间范围: month, quarter, half_year, year")
    ):
        self.time_range = time_range
    
    def get_date_range(self) -> tuple:
        end_date = date.today()
        if self.time_range == "month":
            start_date = end_date - timedelta(days=30)
        elif self.time_range == "quarter":
            start_date = end_date - timedelta(days=90)
        elif self.time_range == "half_year":
            start_date = end_date - timedelta(days=180)
        elif self.time_range == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        return start_date, end_date


class OverviewStats(BaseModel):
    total_devices: int
    total_memory_gb: float
    total_compute_tflops: float
    avg_gpu_usage: float


class TrendData(BaseModel):
    date: str
    value: float


class OrgRanking(BaseModel):
    org_id: int
    org_name: str
    device_count: int
    gpu_count: int
    memory_total: float
    compute_total: float
    cpu_cores: int
    memory_capacity: float
    disk_capacity: float
    avg_gpu_usage: float
    rank: int


@router.get("/overview/stats")
def get_overview_stats(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db), 
    local_db: Session = Depends(get_local_db)
):
    devices = db.query(Device).filter(Device.deleted == 0).all()
    total_devices = len(devices)
    
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    total_memory_gb = 0
    total_compute_tflops = 0
    total_gpus = 0
    
    for device in devices:
        gpu_count = device.gpu_count or 0
        gpu_model = device.gpu_model or ""
        gpu_info = gpu_infos.get(gpu_model)
        if gpu_info:
            total_memory_gb += float(gpu_info.memory_total_gb or 0) * gpu_count
            total_compute_tflops += float(gpu_info.tflops_fp16 or 0) * gpu_count
        total_gpus += gpu_count
    
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    summaries = local_db.query(LocalDailyGpuUsageSummary).filter(
        LocalDailyGpuUsageSummary.summary_date >= start_date,
        LocalDailyGpuUsageSummary.summary_date <= end_date
    ).all()
    
    if time_type == "work":
        values = [float(s.avg_gpu_usage_rate_work or 0) for s in summaries if s.avg_gpu_usage_rate_work is not None]
    elif time_type == "nonwork":
        values = [float(s.avg_gpu_usage_rate_nonwork or 0) for s in summaries if s.avg_gpu_usage_rate_nonwork is not None]
    else:
        values = [float(s.avg_gpu_usage_rate or 0) for s in summaries if s.avg_gpu_usage_rate is not None]
    
    avg_gpu_usage = round(sum(values) / len(values), 2) if values else 0
    
    return OverviewStats(
        total_devices=total_devices,
        total_memory_gb=round(total_memory_gb, 2),
        total_compute_tflops=round(total_compute_tflops, 2),
        avg_gpu_usage=avg_gpu_usage
    )


@router.get("/trend/device-count")
def get_device_count_trend(
    time_range: str = Query("month"),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db)
):
    params = TimeRangeParams(time_range=time_range)
    start_date, end_date = params.get_date_range()
    
    devices = db.query(Device).filter(Device.deleted == 0).all()
    total_devices = len(devices)
    
    result = []
    current_date = start_date
    while current_date <= end_date:
        result.append(TrendData(
            date=current_date.strftime("%Y-%m-%d"),
            value=total_devices
        ))
        current_date += timedelta(days=1)
    
    return result


@router.get("/trend/memory-total")
def get_memory_total_trend(
    time_range: str = Query("month"),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db)
):
    params = TimeRangeParams(time_range=time_range)
    start_date, end_date = params.get_date_range()
    
    devices = db.query(Device).filter(Device.deleted == 0).all()
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    total_memory_gb = 0
    for device in devices:
        gpu_count = device.gpu_count or 0
        gpu_model = device.gpu_model or ""
        gpu_info = gpu_infos.get(gpu_model)
        if gpu_info:
            total_memory_gb += float(gpu_info.memory_total_gb or 0) * gpu_count
    
    result = []
    current_date = start_date
    while current_date <= end_date:
        result.append(TrendData(
            date=current_date.strftime("%Y-%m-%d"),
            value=round(total_memory_gb, 2)
        ))
        current_date += timedelta(days=1)
    
    return result


@router.get("/trend/compute-total")
def get_compute_total_trend(
    time_range: str = Query("month"),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db)
):
    params = TimeRangeParams(time_range=time_range)
    start_date, end_date = params.get_date_range()
    
    devices = db.query(Device).filter(Device.deleted == 0).all()
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    total_compute_tflops = 0
    for device in devices:
        gpu_count = device.gpu_count or 0
        gpu_model = device.gpu_model or ""
        gpu_info = gpu_infos.get(gpu_model)
        if gpu_info:
            total_compute_tflops += float(gpu_info.tflops_fp16 or 0) * gpu_count
    
    total_compute_pflops = round(total_compute_tflops / 1000, 2)
    
    result = []
    current_date = start_date
    while current_date <= end_date:
        result.append(TrendData(
            date=current_date.strftime("%Y-%m-%d"),
            value=total_compute_pflops
        ))
        current_date += timedelta(days=1)
    
    return result


@router.get("/trend/gpu-usage")
def get_gpu_usage_trend(
    time_range: str = Query("month"),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db)
):
    params = TimeRangeParams(time_range=time_range)
    start_date, end_date = params.get_date_range()
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    summaries = local_db.query(LocalDailyGpuUsageSummary).filter(
        LocalDailyGpuUsageSummary.summary_date >= start_datetime,
        LocalDailyGpuUsageSummary.summary_date <= end_datetime
    ).order_by(LocalDailyGpuUsageSummary.summary_date).all()
    
    result = []
    for s in summaries:
        if time_type == "work":
            value = float(s.avg_gpu_usage_rate_work or 0)
        elif time_type == "nonwork":
            value = float(s.avg_gpu_usage_rate_nonwork or 0)
        else:
            value = float(s.avg_gpu_usage_rate or 0)
        result.append(TrendData(
            date=s.summary_date.strftime("%Y-%m-%d"),
            value=value
        ))
    
    return result


@router.get("/warning/usage-bar")
def get_usage_warning_bar(
    time_range: str = Query("month"),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db)
):
    params = TimeRangeParams(time_range=time_range)
    start_date, end_date = params.get_date_range()
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    if time_type == "work":
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_work
    elif time_type == "nonwork":
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_nonwork
    else:
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate
    
    org_summaries = local_db.query(
        LocalOrgGpuUsageSummary.organization_id3,
        LocalOrgGpuUsageSummary.organization_name3,
        func.avg(usage_field).label('avg_usage')
    ).filter(
        LocalOrgGpuUsageSummary.summary_time >= start_datetime,
        LocalOrgGpuUsageSummary.summary_time <= end_datetime
    ).group_by(
        LocalOrgGpuUsageSummary.organization_id3,
        LocalOrgGpuUsageSummary.organization_name3
    ).all()
    
    config_map = {c.config_key: c.config_value for c in local_db.query(LocalSystemConfig).all()}
    high_threshold = float(config_map.get("high_usage_threshold", settings.HIGH_USAGE_THRESHOLD))
    low_threshold = float(config_map.get("low_usage_threshold", settings.LOW_USAGE_THRESHOLD))
    
    result = []
    for org in org_summaries:
        avg_usage = float(org.avg_usage or 0)
        if avg_usage >= high_threshold:
            level = "high"
            color = "#f56c6c"
        elif avg_usage <= low_threshold:
            level = "low"
            color = "#67c23a"
        else:
            level = "medium"
            color = "#e6a23c"
        
        result.append({
            "org_id": org.organization_id3,
            "org_name": org.organization_name3,
            "avg_usage": round(avg_usage, 2),
            "level": level,
            "color": color
        })
    
    return sorted(result, key=lambda x: x["avg_usage"], reverse=True)


@router.get("/org/groups")
def get_org_groups(db: Session = Depends(get_db)):
    groups = get_second_level_groups(db)
    result = []
    for group in groups:
        org_ids = get_org_ids_by_parent(db, group.id)
        device_count = db.query(Device).filter(
            Device.organization_id.in_(org_ids),
            Device.deleted == 0
        ).count()
        result.append({
            "id": group.id,
            "name": group.name,
            "device_count": device_count
        })
    return result


@router.get("/distribution/org-type")
def get_org_type_distribution(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    groups = get_second_level_groups(db)
    result = {}
    for group in groups:
        org_ids = get_org_ids_by_parent(db, group.id)
        orgs = db.query(Organization).filter(
            Organization.id.in_(org_ids),
            Organization.deleted == 0
        ).all()
        
        group_data = []
        for org in orgs:
            count = db.query(Device).filter(
                Device.organization_id == org.id,
                Device.deleted == 0
            ).count()
            if count > 0:
                group_data.append({"name": org.name, "value": count})
        
        result[group.name] = group_data
    
    return result


@router.get("/distribution/network")
def get_network_distribution(db: Session = Depends(get_db)):
    networks = db.query(Network).filter(Network.deleted == 0).all()
    network_map = {n.code: n.name for n in networks}
    
    result = db.query(
        Device.net_module_code,
        func.count(Device.id).label('count')
    ).filter(
        Device.deleted == 0
    ).group_by(
        Device.net_module_code
    ).all()
    
    distribution = {}
    for r in result:
        net_name = network_map.get(r.net_module_code, r.net_module_code or "未知")
        if net_name not in distribution:
            distribution[net_name] = 0
        distribution[net_name] += r.count
    
    return [{"name": k, "value": v} for k, v in distribution.items()]


@router.get("/distribution/network-by-org")
def get_network_distribution_by_org(db: Session = Depends(get_db)):
    networks = db.query(Network).filter(Network.deleted == 0).all()
    network_map = {n.code: n.name for n in networks}
    network_names = sorted([n.name for n in networks])
    
    orgs = db.query(Organization).filter(
        Organization.deleted == 0
    ).all()
    
    result = []
    for org in orgs:
        devices = db.query(Device).filter(
            Device.organization_id == org.id,
            Device.deleted == 0
        ).all()
        
        if not devices:
            continue
        
        network_counts = {net: 0 for net in network_names}
        for device in devices:
            net_name = network_map.get(device.net_module_code, device.net_module_code or "未知")
            if net_name not in network_counts:
                network_counts[net_name] = 0
            network_counts[net_name] += 1
        
        result.append({
            "org_name": org.name,
            "networks": network_counts,
            "total": len(devices)
        })
    
    return {
        "networks": network_names,
        "data": sorted(result, key=lambda x: x["total"], reverse=True)
    }


@router.get("/distribution/gpu-tier")
def get_gpu_tier_distribution(db: Session = Depends(get_db)):
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    tier_counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    
    devices = db.query(Device).filter(Device.deleted == 0).all()
    for device in devices:
        gpu_model = device.gpu_model or ""
        gpu_info = gpu_infos.get(gpu_model)
        gpu_count = device.gpu_count or 1
        if gpu_info:
            if gpu_info.card_type == 1:
                tier_counts["high"] += gpu_count
            elif gpu_info.card_type == 2:
                tier_counts["medium"] += gpu_count
            elif gpu_info.card_type == 3:
                tier_counts["low"] += gpu_count
            else:
                tier_counts["unknown"] += gpu_count
        else:
            tier_counts["unknown"] += gpu_count
    
    return [
        {"name": "高端卡", "value": tier_counts["high"]},
        {"name": "中端卡", "value": tier_counts["medium"]},
        {"name": "低端卡", "value": tier_counts["low"]},
        {"name": "未知", "value": tier_counts["unknown"]}
    ]


@router.get("/distribution/gpu-tier-by-org")
def get_gpu_tier_by_org_distribution(db: Session = Depends(get_db)):
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    orgs = db.query(Organization).filter(
        Organization.deleted == 0
    ).all()
    
    result = []
    for org in orgs:
        devices = db.query(Device).filter(
            Device.organization_id == org.id,
            Device.deleted == 0
        ).all()
        
        if not devices:
            continue
        
        tier_counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
        
        for device in devices:
            gpu_model = device.gpu_model or ""
            gpu_info = gpu_infos.get(gpu_model)
            gpu_count = device.gpu_count or 1
            if gpu_info:
                if gpu_info.card_type == 1:
                    tier_counts["high"] += gpu_count
                elif gpu_info.card_type == 2:
                    tier_counts["medium"] += gpu_count
                elif gpu_info.card_type == 3:
                    tier_counts["low"] += gpu_count
                else:
                    tier_counts["unknown"] += gpu_count
            else:
                tier_counts["unknown"] += gpu_count
        
        result.append({
            "org_name": org.name,
            "high": tier_counts["high"],
            "medium": tier_counts["medium"],
            "low": tier_counts["low"],
            "unknown": tier_counts["unknown"],
            "total": sum(tier_counts.values())
        })
    
    return sorted(result, key=lambda x: x["total"], reverse=True)


@router.get("/distribution/purpose")
def get_purpose_distribution(db: Session = Depends(get_db)):
    purpose_map = {1: "训练", 2: "研发", 3: "推理"}
    
    result = db.query(
        Device.purpose,
        func.sum(Device.gpu_count).label('count')
    ).filter(
        Device.deleted == 0
    ).group_by(
        Device.purpose
    ).all()
    
    return [
        {"name": purpose_map.get(r.purpose, "未知"), "value": r.count or 0} 
        for r in result
    ]


@router.get("/distribution/purpose-by-org")
def get_purpose_distribution_by_org(db: Session = Depends(get_db)):
    purpose_map = {1: "训练", 2: "研发", 3: "推理"}
    purposes = ["训练", "研发", "推理"]
    
    orgs = db.query(Organization).filter(
        Organization.deleted == 0
    ).all()
    
    result = []
    for org in orgs:
        devices = db.query(Device).filter(
            Device.organization_id == org.id,
            Device.deleted == 0
        ).all()
        
        if not devices:
            continue
        
        purpose_counts = {p: 0 for p in purposes}
        total_gpus = 0
        for device in devices:
            purpose_name = purpose_map.get(device.purpose, "未知")
            gpu_count = device.gpu_count or 1
            if purpose_name not in purpose_counts:
                purpose_counts[purpose_name] = 0
            purpose_counts[purpose_name] += gpu_count
            total_gpus += gpu_count
        
        result.append({
            "org_name": org.name,
            "purposes": purpose_counts,
            "total": total_gpus
        })
    
    return {
        "purposes": purposes,
        "data": sorted(result, key=lambda x: x["total"], reverse=True)
    }


@router.get("/map/province")
def get_province_distribution(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    local_org_ids = get_org_ids_by_type(db, 'local')
    
    orgs = db.query(Organization).filter(
        Organization.id.in_(local_org_ids)
    ).all()
    org_map = {o.id: o for o in orgs}
    
    devices = db.query(Device).filter(
        Device.organization_id.in_(local_org_ids),
        Device.deleted == 0
    ).all()
    
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    province_stats = {}
    
    for device in devices:
        org = org_map.get(device.organization_id)
        if not org or not org.province:
            continue
        
        province = org.province
        if province not in province_stats:
            province_stats[province] = {
                "name": province,
                "code": org.province_code,
                "value": 0,
                "gpu_count": 0,
                "memory_gb": 0,
                "compute_tflops": 0,
                "org_ids": set()
            }
        
        province_stats[province]["value"] += 1
        province_stats[province]["org_ids"].add(device.organization_id)
        
        gpu_count = device.gpu_count or 0
        province_stats[province]["gpu_count"] += gpu_count
        
        gpu_model = device.gpu_model or ""
        gpu_info = gpu_infos.get(gpu_model)
        if gpu_info:
            province_stats[province]["memory_gb"] += float(gpu_info.memory_total_gb or 0) * gpu_count
            province_stats[province]["compute_tflops"] += float(gpu_info.tflops_fp16 or 0) * gpu_count
    
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    org_usage_data = {}
    for summary in local_db.query(LocalOrgGpuUsageSummary).filter(
        LocalOrgGpuUsageSummary.summary_time >= start_date,
        LocalOrgGpuUsageSummary.summary_time <= end_date
    ).all():
        org_name = summary.organization_name3
        if org_name not in org_usage_data:
            org_usage_data[org_name] = []
        
        if time_type == "work":
            val = summary.avg_gpu_usage_rate_work
        elif time_type == "nonwork":
            val = summary.avg_gpu_usage_rate_nonwork
        else:
            val = summary.avg_gpu_usage_rate
        
        if val is not None:
            org_usage_data[org_name].append(float(val))
    
    result = []
    for province, data in province_stats.items():
        all_usages = []
        for org_id in data["org_ids"]:
            org = org_map.get(org_id)
            if org and org.name:
                all_usages.extend(org_usage_data.get(org.name, []))
        
        result.append({
            "name": data["name"],
            "code": data["code"],
            "value": data["value"],
            "gpu_count": data["gpu_count"],
            "memory_gb": round(data["memory_gb"], 2),
            "compute_tflops": round(data["compute_tflops"], 2),
            "avg_gpu_usage": round(sum(all_usages) / len(all_usages), 2) if all_usages else 0
        })
    
    return result


@router.get("/bubble/central")
def get_central_bubble(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db)
):
    central_org_ids = get_org_ids_by_type(db, 'central')
    
    devices = db.query(Device).filter(
        Device.organization_id.in_(central_org_ids),
        Device.deleted == 0
    ).all()
    
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    org_stats = {}
    for device in devices:
        org_id = device.organization_id
        if org_id not in org_stats:
            org = db.query(Organization).filter(Organization.id == org_id).first()
            org_stats[org_id] = {
                "name": org.name if org else "",
                "device_count": 0,
                "gpu_count": 0,
                "compute_tflops": 0
            }
        
        org_stats[org_id]["device_count"] += 1
        gpu_count = device.gpu_count or 0
        org_stats[org_id]["gpu_count"] += gpu_count
        
        gpu_model = device.gpu_model or ""
        gpu_info = gpu_infos.get(gpu_model)
        if gpu_info:
            org_stats[org_id]["compute_tflops"] += float(gpu_info.tflops_fp16 or 0) * gpu_count
    
    return [
        {
            "org_id": org_id,
            "name": stats["name"],
            "value": stats["device_count"],
            "gpu_count": stats["gpu_count"],
            "compute_tflops": round(stats["compute_tflops"], 2)
        } for org_id, stats in org_stats.items()
    ]


@router.get("/local/stats")
def get_local_stats(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db), 
    local_db: Session = Depends(get_local_db)
):
    local_org_ids = get_org_ids_by_type(db, 'local')
    
    devices = db.query(Device).filter(
        Device.organization_id.in_(local_org_ids),
        Device.deleted == 0
    ).all()
    
    total_devices = len(devices)
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    total_memory_gb = 0
    total_compute_tflops = 0
    
    for device in devices:
        gpu_count = device.gpu_count or 0
        gpu_model = device.gpu_model or ""
        gpu_info = gpu_infos.get(gpu_model)
        if gpu_info:
            total_memory_gb += float(gpu_info.memory_total_gb or 0) * gpu_count
            total_compute_tflops += float(gpu_info.tflops_fp16 or 0) * gpu_count
    
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    summaries = local_db.query(LocalDailyGpuUsageSummary).filter(
        LocalDailyGpuUsageSummary.summary_date >= start_date,
        LocalDailyGpuUsageSummary.summary_date <= end_date
    ).all()
    
    if time_type == "work":
        values = [float(s.avg_gpu_usage_rate_work or 0) for s in summaries if s.avg_gpu_usage_rate_work is not None]
    elif time_type == "nonwork":
        values = [float(s.avg_gpu_usage_rate_nonwork or 0) for s in summaries if s.avg_gpu_usage_rate_nonwork is not None]
    else:
        values = [float(s.avg_gpu_usage_rate or 0) for s in summaries if s.avg_gpu_usage_rate is not None]
    
    avg_gpu_usage = round(sum(values) / len(values), 2) if values else 0
    
    return {
        "total_devices": total_devices,
        "total_memory_gb": round(total_memory_gb, 2),
        "total_compute_tflops": round(total_compute_tflops, 2),
        "avg_gpu_usage": avg_gpu_usage
    }


@router.get("/local/gpu-tier")
def get_local_gpu_tier(db: Session = Depends(get_db)):
    local_org_ids = get_org_ids_by_type(db, 'local')
    
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    devices = db.query(Device).filter(
        Device.organization_id.in_(local_org_ids),
        Device.deleted == 0
    ).all()
    
    tier_counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    
    for device in devices:
        gpu_model = device.gpu_model or ""
        gpu_count = device.gpu_count or 0
        gpu_info = gpu_infos.get(gpu_model)
        if gpu_info:
            if gpu_info.card_type == 1:
                tier_counts["high"] += gpu_count
            elif gpu_info.card_type == 2:
                tier_counts["medium"] += gpu_count
            elif gpu_info.card_type == 3:
                tier_counts["low"] += gpu_count
            else:
                tier_counts["unknown"] += gpu_count
        else:
            tier_counts["unknown"] += gpu_count
    
    return [
        {"name": "高端卡", "value": tier_counts["high"]},
        {"name": "中端卡", "value": tier_counts["medium"]},
        {"name": "低端卡", "value": tier_counts["low"]},
        {"name": "未知", "value": tier_counts["unknown"]}
    ]


@router.get("/local/purpose")
def get_local_purpose(db: Session = Depends(get_db)):
    local_org_ids = get_org_ids_by_type(db, 'local')
    
    purpose_map = {1: "训练", 2: "研发", 3: "推理"}
    
    result = db.query(
        Device.purpose,
        func.sum(Device.gpu_count).label('count')
    ).filter(
        Device.organization_id.in_(local_org_ids),
        Device.deleted == 0
    ).group_by(
        Device.purpose
    ).all()
    
    return [
        {"name": purpose_map.get(r.purpose, "未知"), "value": r.count or 0} 
        for r in result
    ]


@router.get("/local/trend")
def get_local_trend(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    local_org_ids = get_org_ids_by_type(db, 'local')
    
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    summaries = local_db.query(LocalDailyGpuUsageSummary).filter(
        LocalDailyGpuUsageSummary.summary_date >= start_date,
        LocalDailyGpuUsageSummary.summary_date <= end_date
    ).order_by(LocalDailyGpuUsageSummary.summary_date).all()
    
    result = []
    for s in summaries:
        if time_type == "work":
            value = float(s.avg_gpu_usage_rate_work or 0)
        elif time_type == "nonwork":
            value = float(s.avg_gpu_usage_rate_nonwork or 0)
        else:
            value = float(s.avg_gpu_usage_rate or 0)
        result.append({
            "date": s.summary_date.strftime("%Y-%m-%d"),
            "value": value
        })
    
    return result


@router.get("/central/stats")
def get_central_stats(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db), 
    local_db: Session = Depends(get_local_db)
):
    central_org_ids = get_org_ids_by_type(db, 'central')
    
    devices = db.query(Device).filter(
        Device.organization_id.in_(central_org_ids),
        Device.deleted == 0
    ).all()
    
    total_devices = len(devices)
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    total_memory_gb = 0
    total_compute_tflops = 0
    
    for device in devices:
        gpu_count = device.gpu_count or 0
        gpu_model = device.gpu_model or ""
        gpu_info = gpu_infos.get(gpu_model)
        if gpu_info:
            total_memory_gb += float(gpu_info.memory_total_gb or 0) * gpu_count
            total_compute_tflops += float(gpu_info.tflops_fp16 or 0) * gpu_count
    
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    summaries = local_db.query(LocalDailyGpuUsageSummary).filter(
        LocalDailyGpuUsageSummary.summary_date >= start_date,
        LocalDailyGpuUsageSummary.summary_date <= end_date
    ).all()
    
    if time_type == "work":
        values = [float(s.avg_gpu_usage_rate_work or 0) for s in summaries if s.avg_gpu_usage_rate_work is not None]
    elif time_type == "nonwork":
        values = [float(s.avg_gpu_usage_rate_nonwork or 0) for s in summaries if s.avg_gpu_usage_rate_nonwork is not None]
    else:
        values = [float(s.avg_gpu_usage_rate or 0) for s in summaries if s.avg_gpu_usage_rate is not None]
    
    avg_gpu_usage = round(sum(values) / len(values), 2) if values else 0
    
    return {
        "total_devices": total_devices,
        "total_memory_gb": round(total_memory_gb, 2),
        "total_compute_tflops": round(total_compute_tflops, 2),
        "avg_gpu_usage": avg_gpu_usage
    }


@router.get("/central/gpu-tier")
def get_central_gpu_tier(db: Session = Depends(get_db)):
    central_org_ids = get_org_ids_by_type(db, 'central')
    
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    devices = db.query(Device).filter(
        Device.organization_id.in_(central_org_ids),
        Device.deleted == 0
    ).all()
    
    tier_counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    
    for device in devices:
        gpu_model = device.gpu_model or ""
        gpu_count = device.gpu_count or 1
        gpu_info = gpu_infos.get(gpu_model)
        if gpu_info:
            if gpu_info.card_type == 1:
                tier_counts["high"] += gpu_count
            elif gpu_info.card_type == 2:
                tier_counts["medium"] += gpu_count
            elif gpu_info.card_type == 3:
                tier_counts["low"] += gpu_count
            else:
                tier_counts["unknown"] += gpu_count
        else:
            tier_counts["unknown"] += gpu_count
    
    return [
        {"name": "高端卡", "value": tier_counts["high"]},
        {"name": "中端卡", "value": tier_counts["medium"]},
        {"name": "低端卡", "value": tier_counts["low"]},
        {"name": "未知", "value": tier_counts["unknown"]}
    ]


@router.get("/central/purpose")
def get_central_purpose(db: Session = Depends(get_db)):
    central_org_ids = get_org_ids_by_type(db, 'central')
    
    purpose_map = {1: "训练", 2: "研发", 3: "推理"}
    
    result = db.query(
        Device.purpose,
        func.sum(Device.gpu_count).label('count')
    ).filter(
        Device.organization_id.in_(central_org_ids),
        Device.deleted == 0
    ).group_by(
        Device.purpose
    ).all()
    
    return [
        {"name": purpose_map.get(r.purpose, "未知"), "value": r.count or 0} 
        for r in result
    ]


@router.get("/central/trend")
def get_central_trend(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    central_org_ids = get_org_ids_by_type(db, 'central')
    
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    summaries = local_db.query(LocalDailyGpuUsageSummary).filter(
        LocalDailyGpuUsageSummary.summary_date >= start_date,
        LocalDailyGpuUsageSummary.summary_date <= end_date
    ).order_by(LocalDailyGpuUsageSummary.summary_date).all()
    
    result = []
    for s in summaries:
        if time_type == "work":
            value = float(s.avg_gpu_usage_rate_work or 0)
        elif time_type == "nonwork":
            value = float(s.avg_gpu_usage_rate_nonwork or 0)
        else:
            value = float(s.avg_gpu_usage_rate or 0)
        result.append({
            "date": s.summary_date.strftime("%Y-%m-%d"),
            "value": value
        })
    
    return result


def calculate_org_ranking(db, local_db, group_id=None, time_range='month', time_type='work'):
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    time_range_days = {
        'month': 30,
        'quarter': 90,
        'half_year': 180,
        'year': 365
    }
    days = time_range_days.get(time_range, 30)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    query = db.query(
        Organization.id,
        Organization.name,
        func.count(Device.id).label('device_count'),
        func.sum(Device.gpu_count).label('gpu_count'),
        func.sum(Device.total_memory).label('memory_total'),
        func.sum(Device.cpu_cores).label('cpu_cores'),
        func.sum(Device.memory_size).label('memory_capacity'),
        func.sum(Device.disk_size).label('disk_capacity')
    ).join(
        Device, Device.organization_id == Organization.id
    ).filter(
        Device.deleted == 0,
        Organization.deleted == 0
    )
    
    if group_id:
        org_ids = get_org_ids_by_parent(db, group_id)
        query = query.filter(Organization.id.in_(org_ids))
    
    result = query.group_by(
        Organization.id,
        Organization.name
    ).all()
    
    rankings = []
    for r in result:
        devices = db.query(Device).filter(
            Device.organization_id == r.id,
            Device.deleted == 0
        ).all()
        
        compute_total = 0
        
        for device in devices:
            gpu_model = device.gpu_model or ""
            if gpu_model:
                gpu_info = gpu_infos.get(gpu_model)
                if gpu_info and gpu_info.tflops_fp16:
                    compute_total += float(gpu_info.tflops_fp16) * (device.gpu_count or 1)
        
        if time_type == "work":
            usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_work
        elif time_type == "nonwork":
            usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_nonwork
        else:
            usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate
        
        org_usage = local_db.query(
            func.avg(usage_field).label('avg_usage')
        ).filter(
            LocalOrgGpuUsageSummary.organization_name3 == r.name,
            LocalOrgGpuUsageSummary.summary_time >= start_datetime,
            LocalOrgGpuUsageSummary.summary_time <= end_datetime
        ).first()
        
        avg_gpu_usage = round(float(org_usage.avg_usage or 0), 2) if org_usage and org_usage.avg_usage else 0
        
        rankings.append({
            'org_id': r.id,
            'org_name': r.name,
            'device_count': r.device_count,
            'gpu_count': r.gpu_count or 0,
            'memory_total': float(r.memory_total or 0),
            'compute_total': round(compute_total, 2),
            'cpu_cores': int(r.cpu_cores or 0),
            'memory_capacity': float(r.memory_capacity or 0),
            'disk_capacity': float(r.disk_capacity or 0),
            'avg_gpu_usage': avg_gpu_usage
        })
    
    rankings.sort(key=lambda x: x['avg_gpu_usage'], reverse=True)
    
    result_list = []
    for i, r in enumerate(rankings):
        result_list.append(OrgRanking(
            org_id=r['org_id'],
            org_name=r['org_name'],
            device_count=r['device_count'],
            gpu_count=r['gpu_count'],
            memory_total=r['memory_total'],
            compute_total=r['compute_total'],
            cpu_cores=r['cpu_cores'],
            memory_capacity=r['memory_capacity'],
            disk_capacity=r['disk_capacity'],
            avg_gpu_usage=r['avg_gpu_usage'],
            rank=i+1
        ))
    
    return result_list


@router.get("/ranking/all")
def get_all_ranking(
    time_range: str = Query('month'),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    return calculate_org_ranking(db, local_db, time_range=time_range, time_type=time_type)


@router.get("/ranking/group/{group_id}")
def get_group_ranking(
    group_id: int,
    time_range: str = Query('month'),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    return calculate_org_ranking(db, local_db, group_id=group_id, time_range=time_range, time_type=time_type)


@router.get("/ranking/groups")
def get_all_group_rankings(
    time_range: str = Query('month'),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    groups = get_second_level_groups(db)
    result = {}
    for group in groups:
        rankings = calculate_org_ranking(db, local_db, group_id=group.id, time_range=time_range, time_type=time_type)
        result[group.name] = rankings[:5]
    return result


@router.get("/ranking/local")
def get_local_ranking(
    time_range: str = Query('month'),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    return calculate_org_ranking(db, local_db, time_range=time_range, time_type=time_type)


@router.get("/ranking/central")
def get_central_ranking(
    time_range: str = Query('month'),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    return calculate_org_ranking(db, local_db, time_range=time_range, time_type=time_type)


@router.get("/ranking/province/{province_name}")
def get_province_ranking(
    province_name: str,
    time_range: str = Query('month'),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    time_range_days = {
        'month': 30,
        'quarter': 90,
        'half_year': 180,
        'year': 365
    }
    days = time_range_days.get(time_range, 30)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    query = db.query(
        Organization.id,
        Organization.name,
        func.count(Device.id).label('device_count'),
        func.sum(Device.gpu_count).label('gpu_count'),
        func.sum(Device.total_memory).label('memory_total'),
        func.sum(Device.cpu_cores).label('cpu_cores'),
        func.sum(Device.memory_size).label('memory_capacity'),
        func.sum(Device.disk_size).label('disk_capacity')
    ).join(
        Device, Device.organization_id == Organization.id
    ).filter(
        Device.deleted == 0,
        Organization.deleted == 0,
        Organization.province == province_name
    )
    
    result = query.group_by(
        Organization.id,
        Organization.name
    ).all()
    
    rankings = []
    for r in result:
        devices = db.query(Device).filter(
            Device.organization_id == r.id,
            Device.deleted == 0
        ).all()
        
        compute_total = 0
        
        for device in devices:
            gpu_model = device.gpu_model or ""
            if gpu_model:
                gpu_info = gpu_infos.get(gpu_model)
                if gpu_info and gpu_info.tflops_fp16:
                    compute_total += float(gpu_info.tflops_fp16) * (device.gpu_count or 1)
        
        if time_type == "work":
            usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_work
        elif time_type == "nonwork":
            usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_nonwork
        else:
            usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate
        
        org_usage = local_db.query(
            func.avg(usage_field).label('avg_usage')
        ).filter(
            LocalOrgGpuUsageSummary.organization_name3 == r.name,
            LocalOrgGpuUsageSummary.summary_time >= start_datetime,
            LocalOrgGpuUsageSummary.summary_time <= end_datetime
        ).first()
        
        avg_gpu_usage = round(float(org_usage.avg_usage or 0), 2) if org_usage and org_usage.avg_usage else 0
        
        rankings.append({
            'org_id': r.id,
            'org_name': r.name,
            'device_count': r.device_count,
            'gpu_count': r.gpu_count or 0,
            'memory_total': float(r.memory_total or 0),
            'compute_total': round(compute_total, 2),
            'cpu_cores': int(r.cpu_cores or 0),
            'memory_capacity': float(r.memory_capacity or 0),
            'disk_capacity': float(r.disk_capacity or 0),
            'avg_gpu_usage': avg_gpu_usage
        })
    
    rankings.sort(key=lambda x: x['avg_gpu_usage'], reverse=True)
    
    result_list = []
    for i, r in enumerate(rankings):
        result_list.append(OrgRanking(
            org_id=r['org_id'],
            org_name=r['org_name'],
            device_count=r['device_count'],
            gpu_count=r['gpu_count'],
            memory_total=r['memory_total'],
            compute_total=r['compute_total'],
            cpu_cores=r['cpu_cores'],
            memory_capacity=r['memory_capacity'],
            disk_capacity=r['disk_capacity'],
            avg_gpu_usage=r['avg_gpu_usage'],
            rank=i+1
        ))
    
    return result_list


@router.get("/carousel/usage-trend")
def get_carousel_usage_trend(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    org_type: str = Query(None, description="单位类型: central(部机关), local(地方厅局)"),
    org_name: str = Query(None, description="单位名称，支持模糊搜索"),
    time_grain: str = Query("day", description="时间粒度: hour(小时), day(天), week(周), month(月)"),
    start_date: str = Query(None, description="开始日期，格式YYYY-MM-DD"),
    end_date: str = Query(None, description="结束日期，格式YYYY-MM-DD"),
    drill_date: str = Query(None, description="下钻日期，格式YYYY-MM-DD，返回该日24小时数据"),
    drill_org_id: int = Query(None, description="下钻单位ID"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    if drill_date:
        try:
            target_date = datetime.strptime(drill_date, '%Y-%m-%d').date()
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}
        
        if time_type == "work":
            is_work = 1
        elif time_type == "nonwork":
            is_work = 0
        else:
            is_work = None
        
        if drill_org_id:
            hourly_stats = local_db.query(LocalOrgHourlyStats).filter(
                LocalOrgHourlyStats.organization_id3 == drill_org_id,
                func.date(LocalOrgHourlyStats.stat_date) == target_date
            )
            
            if is_work is not None:
                hourly_stats = hourly_stats.filter(LocalOrgHourlyStats.is_work_hour == is_work)
            
            hourly_stats = hourly_stats.order_by(LocalOrgHourlyStats.stat_hour).all()
            
            hour_trend = []
            for h in hourly_stats:
                hour_trend.append({
                    "date": f"{h.stat_hour:02d}:00",
                    "value": round(float(h.avg_gpu_usage_rate or 0), 2)
                })
            
            if hourly_stats:
                drill_org_name = hourly_stats[0].organization_name3
            else:
                drill_org_name = f"单位{drill_org_id}"
        else:
            hourly_stats = local_db.query(
                LocalStatisticsData.stat_hour,
                func.avg(LocalStatisticsData.avg_gpu_utilization).label('avg_usage')
            ).filter(
                func.date(LocalStatisticsData.stat_date) == target_date
            )
            
            if is_work is not None:
                hourly_stats = hourly_stats.filter(LocalStatisticsData.is_work_hour == is_work)
            
            hourly_stats = hourly_stats.group_by(LocalStatisticsData.stat_hour).order_by(LocalStatisticsData.stat_hour).all()
            
            hour_trend = []
            for h in hourly_stats:
                hour_trend.append({
                    "date": f"{h.stat_hour:02d}:00",
                    "value": round(float(h.avg_usage or 0), 2)
                })
        
        for hour in range(24):
            if not any(t["date"] == f"{hour:02d}:00" for t in hour_trend):
                hour_trend.append({"date": f"{hour:02d}:00", "value": 0})
        
        hour_trend.sort(key=lambda x: x["date"])
        
        return {
            "org_name": drill_org_id or "全部单位",
            "trend": hour_trend,
            "drill_date": drill_date
        }
    
    today = date.today()
    if start_date:
        try:
            start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date_parsed = today - timedelta(days=7)
    else:
        if time_grain == "hour":
            start_date_parsed = today - timedelta(days=1)
        elif time_grain == "week":
            start_date_parsed = today - timedelta(days=28)
        elif time_grain == "month":
            start_date_parsed = today - timedelta(days=90)
        else:
            start_date_parsed = today - timedelta(days=7)
    
    if end_date:
        try:
            end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date_parsed = today
    else:
        end_date_parsed = today
    
    start_datetime = datetime.combine(start_date_parsed, datetime.min.time())
    end_datetime = datetime.combine(end_date_parsed, datetime.max.time())
    
    if time_type == "work":
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_work
    elif time_type == "nonwork":
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_nonwork
    else:
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate
    
    org_ids_filter = None
    if org_type:
        org_ids_filter = get_org_ids_by_type(db, org_type)
    
    if time_grain == "week":
        date_format = 'YYYY-"W"IW'
    elif time_grain == "month":
        date_format = 'YYYY-MM'
    else:
        date_format = 'YYYY-MM-DD'
    
    query = local_db.query(
        LocalOrgGpuUsageSummary.organization_id3,
        LocalOrgGpuUsageSummary.organization_name3,
        sqlite_date_format(LocalOrgGpuUsageSummary.summary_time, date_format).label('stat_date'),
        func.avg(usage_field).label('avg_usage')
    ).filter(
        LocalOrgGpuUsageSummary.summary_time >= start_datetime,
        LocalOrgGpuUsageSummary.summary_time <= end_datetime
    )
    
    if org_name:
        query = query.filter(LocalOrgGpuUsageSummary.organization_name3.ilike(f"%{org_name}%"))
    
    org_summaries = query.group_by(
        LocalOrgGpuUsageSummary.organization_id3,
        LocalOrgGpuUsageSummary.organization_name3,
        sqlite_date_format(LocalOrgGpuUsageSummary.summary_time, date_format)
    ).order_by('stat_date').all()
    
    org_trends = {}
    org_ids = {}
    for s in org_summaries:
        org_name_result = s.organization_name3
        org_id_result = s.organization_id3
        if org_ids_filter is not None:
            if org_id_result and org_id_result not in org_ids_filter:
                continue
        if org_name_result not in org_trends:
            org_trends[org_name_result] = []
            org_ids[org_name_result] = org_id_result
        org_trends[org_name_result].append({
            "date": s.stat_date,
            "value": round(float(s.avg_usage or 0), 2)
        })
    
    return [
        {"org_id": org_ids.get(org_name_result), "org_name": org_name_result, "trend": trend}
        for org_name_result, trend in org_trends.items()
    ]

from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, desc, literal_column
from sqlalchemy.sql import text
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.database import get_db
from app.local_database import get_local_db
from app.models import DeviceGpuMonitor, Device, GpuCardInfo
from app.local_models import (
    LocalDailyGpuUsageSummary, LocalDailyDeviceSummary, LocalDeviceHourlyStats,
    LocalOrgGpuUsageSummary, LocalStatisticsData, LocalSystemConfig, LocalOrgHourlyStats,
    LocalOrganization, LocalDevice, LocalGpuCardInfo, LocalNetwork,
    LocalCacheMetadata, LocalPurposeDict
)
from app.config import settings
from app.org_constants import ORG_CODE_CHINA
from app.cache_sync import CacheSyncService


router = APIRouter()

ONLINE_THRESHOLD_MINUTES = 10

PURPOSE_DICT_TYPE = 'device_purpose'


def get_purpose_map(local_db: Session) -> Dict[int, str]:
    purpose_dicts = local_db.query(LocalPurposeDict).filter(
        LocalPurposeDict.dict_type == PURPOSE_DICT_TYPE,
        LocalPurposeDict.deleted == 0,
        LocalPurposeDict.status == 1
    ).all()
    
    if not purpose_dicts:
        return {1: "训练", 2: "研发", 3: "推理"}
    
    return {d.dict_value: d.dict_label for d in purpose_dicts}


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


def get_second_level_groups_cached(local_db: Session) -> list:
    china_org = local_db.query(LocalOrganization).filter(
        LocalOrganization.code == ORG_CODE_CHINA,
        LocalOrganization.deleted == 0
    ).first()
    if not china_org:
        return []
    groups = local_db.query(LocalOrganization).filter(
        LocalOrganization.parent_id == china_org.id,
        LocalOrganization.deleted == 0
    ).all()
    return groups


def get_org_ids_by_parent_cached(local_db: Session, parent_id: int) -> list:
    result = []
    orgs = local_db.query(LocalOrganization).filter(
        LocalOrganization.parent_id == parent_id,
        LocalOrganization.deleted == 0
    ).all()
    for org in orgs:
        result.append(org.id)
        result.extend(get_org_ids_by_parent_cached(local_db, org.id))
    return result


def get_org_ids_by_type_cached(local_db: Session, org_type: str) -> list:
    groups = get_second_level_groups_cached(local_db)
    for group in groups:
        if org_type == 'local' and '地方厅局' in group.name:
            return get_org_ids_by_parent_cached(local_db, group.id)
        elif org_type == 'central' and '部机关' in group.name:
            return get_org_ids_by_parent_cached(local_db, group.id)
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
    memory_used_gb: float
    memory_usage_rate: float
    avg_memory_utilization: float


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
    devices = local_db.query(LocalDevice).filter(LocalDevice.deleted == 0).all()
    total_devices = len(devices)
    
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
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
        gpu_values = [float(s.avg_gpu_usage_rate_work or 0) for s in summaries if s.avg_gpu_usage_rate_work is not None]
        memory_values = [float(s.avg_memory_usage_rate or 0) for s in summaries if s.avg_memory_usage_rate is not None]
    elif time_type == "nonwork":
        gpu_values = [float(s.avg_gpu_usage_rate_nonwork or 0) for s in summaries if s.avg_gpu_usage_rate_nonwork is not None]
        memory_values = [float(s.avg_memory_usage_rate or 0) for s in summaries if s.avg_memory_usage_rate is not None]
    else:
        gpu_values = [float(s.avg_gpu_usage_rate or 0) for s in summaries if s.avg_gpu_usage_rate is not None]
        memory_values = [float(s.avg_memory_usage_rate or 0) for s in summaries if s.avg_memory_usage_rate is not None]
    
    avg_gpu_usage = round(sum(gpu_values) / len(gpu_values), 2) if gpu_values else 0
    avg_memory_utilization = round(sum(memory_values) / len(memory_values), 2) if memory_values else 0
    
    memory_used_gb = round(total_memory_gb * avg_memory_utilization / 100, 2) if total_memory_gb > 0 and avg_memory_utilization > 0 else 0
    memory_usage_rate = avg_memory_utilization
    
    return OverviewStats(
        total_devices=total_devices,
        total_memory_gb=round(total_memory_gb, 2),
        total_compute_tflops=round(total_compute_tflops, 2),
        avg_gpu_usage=avg_gpu_usage,
        memory_used_gb=memory_used_gb,
        memory_usage_rate=memory_usage_rate,
        avg_memory_utilization=avg_memory_utilization
    )


@router.get("/trend/device-count")
def get_device_count_trend(
    time_range: str = Query("month"),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    db: Session = Depends(get_db)
):
    params = TimeRangeParams(time_range=time_range)
    start_date, end_date = params.get_date_range()
    
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    result = []
    current_date = start_date
    while current_date <= end_date:
        current_datetime = datetime.combine(current_date, datetime.max.time())
        count = db.query(Device).filter(
            Device.deleted == 0,
            Device.create_time <= current_datetime
        ).count()
        result.append(TrendData(
            date=current_date.strftime("%Y-%m-%d"),
            value=count
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
    
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    result = []
    current_date = start_date
    while current_date <= end_date:
        current_datetime = datetime.combine(current_date, datetime.max.time())
        
        devices = db.query(Device).filter(
            Device.deleted == 0,
            Device.create_time <= current_datetime
        ).all()
        
        total_memory_gb = 0
        for device in devices:
            gpu_count = device.gpu_count or 0
            gpu_model = device.gpu_model or ""
            gpu_info = gpu_infos.get(gpu_model)
            if gpu_info:
                total_memory_gb += float(gpu_info.memory_total_gb or 0) * gpu_count
        
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
    
    gpu_infos = {g.gpu_name: g for g in db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
    
    result = []
    current_date = start_date
    while current_date <= end_date:
        current_datetime = datetime.combine(current_date, datetime.max.time())
        
        devices = db.query(Device).filter(
            Device.deleted == 0,
            Device.create_time <= current_datetime
        ).all()
        
        total_compute_tflops = 0
        for device in devices:
            gpu_count = device.gpu_count or 0
            gpu_model = device.gpu_model or ""
            gpu_info = gpu_infos.get(gpu_model)
            if gpu_info:
                total_compute_tflops += float(gpu_info.tflops_fp16 or 0) * gpu_count
        
        total_compute_pflops = round(total_compute_tflops / 1000, 2)
        
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
            gpu_value = float(s.avg_gpu_usage_rate_work or 0)
        elif time_type == "nonwork":
            gpu_value = float(s.avg_gpu_usage_rate_nonwork or 0)
        else:
            gpu_value = float(s.avg_gpu_usage_rate or 0)
        
        memory_usage_rate = float(s.avg_memory_usage_rate or 0)
        memory_utilization = float(s.avg_memory_usage_rate or 0)
        
        result.append({
            "date": s.summary_date.strftime("%Y-%m-%d"),
            "gpu_usage": gpu_value,
            "memory_usage_rate": memory_usage_rate,
            "memory_utilization": memory_utilization
        })
    
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
def get_org_groups(local_db: Session = Depends(get_local_db)):
    groups = get_second_level_groups_cached(local_db)
    result = []
    for group in groups:
        org_ids = get_org_ids_by_parent_cached(local_db, group.id)
        device_count = local_db.query(LocalDevice).filter(
            LocalDevice.organization_id.in_(org_ids),
            LocalDevice.deleted == 0
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
    local_db: Session = Depends(get_local_db)
):
    groups = get_second_level_groups_cached(local_db)
    result = {}
    for group in groups:
        org_ids = get_org_ids_by_parent_cached(local_db, group.id)
        orgs = local_db.query(LocalOrganization).filter(
            LocalOrganization.id.in_(org_ids),
            LocalOrganization.deleted == 0
        ).all()
        
        group_data = []
        for org in orgs:
            count = local_db.query(LocalDevice).filter(
                LocalDevice.organization_id == org.id,
                LocalDevice.deleted == 0
            ).count()
            if count > 0:
                group_data.append({"name": org.name, "value": count})
        
        result[group.name] = group_data
    
    return result


@router.get("/distribution/network")
def get_network_distribution(local_db: Session = Depends(get_local_db)):
    networks = local_db.query(LocalNetwork).filter(LocalNetwork.deleted == 0).all()
    network_map = {n.code: n.name for n in networks}
    
    result = local_db.query(
        LocalDevice.net_module_code,
        func.count(LocalDevice.id).label('count')
    ).filter(
        LocalDevice.deleted == 0
    ).group_by(
        LocalDevice.net_module_code
    ).all()
    
    distribution = {}
    for r in result:
        net_name = network_map.get(r.net_module_code, r.net_module_code or "未知")
        if net_name not in distribution:
            distribution[net_name] = 0
        distribution[net_name] += r.count
    
    return [{"name": k, "value": v} for k, v in distribution.items()]


@router.get("/distribution/network-by-org")
def get_network_distribution_by_org(local_db: Session = Depends(get_local_db)):
    networks = local_db.query(LocalNetwork).filter(LocalNetwork.deleted == 0).all()
    network_map = {n.code: n.name for n in networks}
    network_names = sorted([n.name for n in networks])
    
    orgs = local_db.query(LocalOrganization).filter(
        LocalOrganization.deleted == 0
    ).all()
    
    result = []
    for org in orgs:
        devices = local_db.query(LocalDevice).filter(
            LocalDevice.organization_id == org.id,
            LocalDevice.deleted == 0
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
def get_gpu_tier_distribution(local_db: Session = Depends(get_local_db)):
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
    tier_counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    
    devices = local_db.query(LocalDevice).filter(LocalDevice.deleted == 0).all()
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
def get_gpu_tier_by_org_distribution(local_db: Session = Depends(get_local_db)):
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
    orgs = local_db.query(LocalOrganization).filter(
        LocalOrganization.deleted == 0
    ).all()
    
    result = []
    for org in orgs:
        devices = local_db.query(LocalDevice).filter(
            LocalDevice.organization_id == org.id,
            LocalDevice.deleted == 0
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
def get_purpose_distribution(local_db: Session = Depends(get_local_db)):
    purpose_map = get_purpose_map(local_db)
    
    result = local_db.query(
        LocalDevice.purpose,
        func.sum(LocalDevice.gpu_count).label('count')
    ).filter(
        LocalDevice.deleted == 0
    ).group_by(
        LocalDevice.purpose
    ).all()
    
    return [
        {"name": purpose_map.get(r.purpose, "未知"), "value": r.count or 0} 
        for r in result
    ]


@router.get("/distribution/purpose-by-org")
def get_purpose_distribution_by_org(local_db: Session = Depends(get_local_db)):
    purpose_map = get_purpose_map(local_db)
    purposes = list(purpose_map.values())
    
    orgs = local_db.query(LocalOrganization).filter(
        LocalOrganization.deleted == 0
    ).all()
    
    result = []
    for org in orgs:
        devices = local_db.query(LocalDevice).filter(
            LocalDevice.organization_id == org.id,
            LocalDevice.deleted == 0
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


@router.get("/dict/purpose")
def get_purpose_dict(local_db: Session = Depends(get_local_db)):
    purpose_dicts = local_db.query(LocalPurposeDict).filter(
        LocalPurposeDict.dict_type == PURPOSE_DICT_TYPE,
        LocalPurposeDict.deleted == 0,
        LocalPurposeDict.status == 1
    ).order_by(LocalPurposeDict.dict_sort).all()
    
    if not purpose_dicts:
        return [
            {"id": 1, "dict_value": 1, "dict_label": "训练", "status": 1, "dict_sort": 1, "remark": ""},
            {"id": 2, "dict_value": 2, "dict_label": "研发", "status": 1, "dict_sort": 2, "remark": ""},
            {"id": 3, "dict_value": 3, "dict_label": "推理", "status": 1, "dict_sort": 3, "remark": ""}
        ]
    
    return [
        {
            "id": d.id,
            "dict_value": d.dict_value,
            "dict_label": d.dict_label,
            "status": d.status,
            "dict_sort": d.dict_sort,
            "remark": d.remark
        }
        for d in purpose_dicts
    ]


@router.get("/map/province")
def get_province_distribution(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db)
):
    local_org_ids = get_org_ids_by_type_cached(local_db, 'local')
    
    orgs = local_db.query(LocalOrganization).filter(
        LocalOrganization.id.in_(local_org_ids)
    ).all()
    org_map = {o.id: o for o in orgs}
    
    devices = local_db.query(LocalDevice).filter(
        LocalDevice.organization_id.in_(local_org_ids),
        LocalDevice.deleted == 0
    ).all()
    
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
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
    local_db: Session = Depends(get_local_db)
):
    central_org_ids = get_org_ids_by_type_cached(local_db, 'central')
    
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
    orgs = local_db.query(LocalOrganization).filter(
        LocalOrganization.id.in_(central_org_ids),
        LocalOrganization.deleted == 0
    ).all()
    
    result = []
    for org in orgs:
        devices = local_db.query(LocalDevice).filter(
            LocalDevice.organization_id == org.id,
            LocalDevice.deleted == 0
        ).all()
        
        if not devices:
            continue
        
        device_count = len(devices)
        gpu_count = 0
        memory_gb = 0
        compute_tflops = 0
        
        for device in devices:
            dev_gpu_count = device.gpu_count or 0
            gpu_count += dev_gpu_count
            gpu_model = device.gpu_model or ""
            gpu_info = gpu_infos.get(gpu_model)
            if gpu_info:
                memory_gb += float(gpu_info.memory_total_gb or 0) * dev_gpu_count
                compute_tflops += float(gpu_info.tflops_fp16 or 0) * dev_gpu_count
        
        result.append({
            "org_id": org.id,
            "name": org.name,
            "value": device_count,
            "gpu_count": gpu_count,
            "memory_gb": round(memory_gb, 2),
            "compute_tflops": round(compute_tflops, 2)
        })
    
    return result


@router.get("/local/stats")
def get_local_stats(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db)
):
    local_org_ids = get_org_ids_by_type_cached(local_db, 'local')
    
    devices = local_db.query(LocalDevice).filter(
        LocalDevice.organization_id.in_(local_org_ids),
        LocalDevice.deleted == 0
    ).all()
    
    total_devices = len(devices)
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
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
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    if time_type == "work":
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_work
    elif time_type == "nonwork":
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_nonwork
    else:
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate
    
    org_summaries = local_db.query(
        func.avg(usage_field).label('avg_usage'),
        func.avg(LocalOrgGpuUsageSummary.avg_memory_usage_rate).label('avg_memory_usage')
    ).filter(
        LocalOrgGpuUsageSummary.organization_id3.in_(local_org_ids),
        LocalOrgGpuUsageSummary.summary_time >= start_datetime,
        LocalOrgGpuUsageSummary.summary_time <= end_datetime
    ).first()
    
    avg_gpu_usage = round(float(org_summaries.avg_usage or 0), 2) if org_summaries and org_summaries.avg_usage else 0
    avg_memory_utilization = round(float(org_summaries.avg_memory_usage or 0), 2) if org_summaries and org_summaries.avg_memory_usage else 0
    
    memory_used_gb = round(total_memory_gb * avg_memory_utilization / 100, 2) if total_memory_gb > 0 and avg_memory_utilization > 0 else 0
    memory_usage_rate = avg_memory_utilization
    
    return {
        "total_devices": total_devices,
        "total_memory_gb": round(total_memory_gb, 2),
        "total_compute_tflops": round(total_compute_tflops, 2),
        "avg_gpu_usage": avg_gpu_usage,
        "memory_used_gb": memory_used_gb,
        "memory_usage_rate": memory_usage_rate,
        "avg_memory_utilization": avg_memory_utilization
    }


@router.get("/local/gpu-tier")
def get_local_gpu_tier(local_db: Session = Depends(get_local_db)):
    local_org_ids = get_org_ids_by_type_cached(local_db, 'local')
    
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
    devices = local_db.query(LocalDevice).filter(
        LocalDevice.organization_id.in_(local_org_ids),
        LocalDevice.deleted == 0
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
def get_local_purpose(local_db: Session = Depends(get_local_db)):
    local_org_ids = get_org_ids_by_type_cached(local_db, 'local')
    
    purpose_map = get_purpose_map(local_db)
    
    result = local_db.query(
        LocalDevice.purpose,
        func.sum(LocalDevice.gpu_count).label('count')
    ).filter(
        LocalDevice.organization_id.in_(local_org_ids),
        LocalDevice.deleted == 0
    ).group_by(
        LocalDevice.purpose
    ).all()
    
    return [
        {"name": purpose_map.get(r.purpose, "未知"), "value": r.count or 0} 
        for r in result
    ]


@router.get("/local/trend")
def get_local_trend(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db)
):
    local_org_ids = get_org_ids_by_type_cached(local_db, 'local')
    
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
    local_db: Session = Depends(get_local_db)
):
    central_org_ids = get_org_ids_by_type_cached(local_db, 'central')
    
    devices = local_db.query(LocalDevice).filter(
        LocalDevice.organization_id.in_(central_org_ids),
        LocalDevice.deleted == 0
    ).all()
    
    total_devices = len(devices)
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
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
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    if time_type == "work":
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_work
    elif time_type == "nonwork":
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_nonwork
    else:
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate
    
    org_summaries = local_db.query(
        func.avg(usage_field).label('avg_usage'),
        func.avg(LocalOrgGpuUsageSummary.avg_memory_usage_rate).label('avg_memory_usage')
    ).filter(
        LocalOrgGpuUsageSummary.organization_id3.in_(central_org_ids),
        LocalOrgGpuUsageSummary.summary_time >= start_datetime,
        LocalOrgGpuUsageSummary.summary_time <= end_datetime
    ).first()
    
    avg_gpu_usage = round(float(org_summaries.avg_usage or 0), 2) if org_summaries and org_summaries.avg_usage else 0
    avg_memory_utilization = round(float(org_summaries.avg_memory_usage or 0), 2) if org_summaries and org_summaries.avg_memory_usage else 0
    
    memory_used_gb = round(total_memory_gb * avg_memory_utilization / 100, 2) if total_memory_gb > 0 and avg_memory_utilization > 0 else 0
    memory_usage_rate = avg_memory_utilization
    
    return {
        "total_devices": total_devices,
        "total_memory_gb": round(total_memory_gb, 2),
        "total_compute_tflops": round(total_compute_tflops, 2),
        "avg_gpu_usage": avg_gpu_usage,
        "memory_used_gb": memory_used_gb,
        "memory_usage_rate": memory_usage_rate,
        "avg_memory_utilization": avg_memory_utilization
    }


@router.get("/central/gpu-tier")
def get_central_gpu_tier(local_db: Session = Depends(get_local_db)):
    central_org_ids = get_org_ids_by_type_cached(local_db, 'central')
    
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
    devices = local_db.query(LocalDevice).filter(
        LocalDevice.organization_id.in_(central_org_ids),
        LocalDevice.deleted == 0
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
def get_central_purpose(local_db: Session = Depends(get_local_db)):
    central_org_ids = get_org_ids_by_type_cached(local_db, 'central')
    
    purpose_map = get_purpose_map(local_db)
    
    result = local_db.query(
        LocalDevice.purpose,
        func.sum(LocalDevice.gpu_count).label('count')
    ).filter(
        LocalDevice.organization_id.in_(central_org_ids),
        LocalDevice.deleted == 0
    ).group_by(
        LocalDevice.purpose
    ).all()
    
    return [
        {"name": purpose_map.get(r.purpose, "未知"), "value": r.count or 0} 
        for r in result
    ]


@router.get("/central/trend")
def get_central_trend(
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db)
):
    central_org_ids = get_org_ids_by_type_cached(local_db, 'central')
    
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


def calculate_org_ranking_cached(local_db, group_id=None, time_range='month', time_type='work'):
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
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
    
    query = local_db.query(
        LocalOrganization.id,
        LocalOrganization.name,
        func.count(LocalDevice.id).label('device_count'),
        func.sum(LocalDevice.gpu_count).label('gpu_count'),
        func.sum(LocalDevice.total_memory).label('memory_total'),
        func.sum(LocalDevice.cpu_cores).label('cpu_cores'),
        func.sum(LocalDevice.memory_size).label('memory_capacity'),
        func.sum(LocalDevice.disk_size).label('disk_capacity')
    ).join(
        LocalDevice, LocalDevice.organization_id == LocalOrganization.id
    ).filter(
        LocalDevice.deleted == 0,
        LocalOrganization.deleted == 0
    )
    
    if group_id:
        org_ids = get_org_ids_by_parent_cached(local_db, group_id)
        query = query.filter(LocalOrganization.id.in_(org_ids))
    
    result = query.group_by(
        LocalOrganization.id,
        LocalOrganization.name
    ).all()
    
    rankings = []
    for r in result:
        devices = local_db.query(LocalDevice).filter(
            LocalDevice.organization_id == r.id,
            LocalDevice.deleted == 0
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
            LocalOrgGpuUsageSummary.organization_id3 == r.id,
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
    local_db: Session = Depends(get_local_db)
):
    return calculate_org_ranking_cached(local_db, time_range=time_range, time_type=time_type)


@router.get("/ranking/group/{group_id}")
def get_group_ranking(
    group_id: int,
    time_range: str = Query('month'),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db)
):
    return calculate_org_ranking_cached(local_db, group_id=group_id, time_range=time_range, time_type=time_type)


@router.get("/ranking/groups")
def get_all_group_rankings(
    time_range: str = Query('month'),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db)
):
    groups = get_second_level_groups_cached(local_db)
    result = {}
    for group in groups:
        rankings = calculate_org_ranking_cached(local_db, group_id=group.id, time_range=time_range, time_type=time_type)
        result[group.name] = rankings[:5]
    return result


@router.get("/ranking/local")
def get_local_ranking(
    time_range: str = Query('month'),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db)
):
    return calculate_org_ranking_cached(local_db, time_range=time_range, time_type=time_type)


@router.get("/ranking/central")
def get_central_ranking(
    time_range: str = Query('month'),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db)
):
    return calculate_org_ranking_cached(local_db, time_range=time_range, time_type=time_type)


@router.get("/ranking/province/{province_name}")
def get_province_ranking(
    province_name: str,
    time_range: str = Query('month'),
    time_type: str = Query("work", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db)
):
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
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
    
    query = local_db.query(
        LocalOrganization.id,
        LocalOrganization.name,
        func.count(LocalDevice.id).label('device_count'),
        func.sum(LocalDevice.gpu_count).label('gpu_count'),
        func.sum(LocalDevice.total_memory).label('memory_total'),
        func.sum(LocalDevice.cpu_cores).label('cpu_cores'),
        func.sum(LocalDevice.memory_size).label('memory_capacity'),
        func.sum(LocalDevice.disk_size).label('disk_capacity')
    ).join(
        LocalDevice, LocalDevice.organization_id == LocalOrganization.id
    ).filter(
        LocalDevice.deleted == 0,
        LocalOrganization.deleted == 0,
        LocalOrganization.province == province_name
    )
    
    result = query.group_by(
        LocalOrganization.id,
        LocalOrganization.name
    ).all()
    
    rankings = []
    for r in result:
        devices = local_db.query(LocalDevice).filter(
            LocalDevice.organization_id == r.id,
            LocalDevice.deleted == 0
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
            LocalOrgGpuUsageSummary.organization_id3 == r.id,
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
                    "gpu_usage": round(float(h.avg_gpu_usage_rate or 0), 2),
                    "memory_usage_rate": round(float(h.avg_memory_usage_rate or 0), 2),
                    "memory_utilization": round(float(h.avg_memory_usage_rate or 0), 2)
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
                    "gpu_usage": round(float(h.avg_usage or 0), 2),
                    "memory_usage_rate": 0,
                    "memory_utilization": 0
                })
        
        for hour in range(24):
            if not any(t["date"] == f"{hour:02d}:00" for t in hour_trend):
                hour_trend.append({"date": f"{hour:02d}:00", "gpu_usage": 0, "memory_usage_rate": 0, "memory_utilization": 0})
        
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
        org_ids_filter = get_org_ids_by_type_cached(local_db, org_type)
    
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
        func.avg(usage_field).label('avg_usage'),
        func.avg(LocalOrgGpuUsageSummary.avg_memory_usage_rate).label('avg_memory_usage')
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
            "gpu_usage": round(float(s.avg_usage or 0), 2),
            "memory_usage_rate": round(float(s.avg_memory_usage or 0), 2),
            "memory_utilization": round(float(s.avg_memory_usage or 0), 2)
        })
    
    return [
        {"org_id": org_ids.get(org_name_result), "org_name": org_name_result, "trend": trend}
        for org_name_result, trend in org_trends.items()
    ]


@router.get("/cache/status")
def get_cache_status(local_db: Session = Depends(get_local_db)):
    metadatas = local_db.query(LocalCacheMetadata).all()
    
    result = []
    for m in metadatas:
        result.append({
            'cache_name': m.cache_name,
            'last_sync_time': m.last_sync_time.isoformat() if m.last_sync_time else None,
            'sync_interval_seconds': m.sync_interval_seconds,
            'record_count': m.record_count,
            'status': m.status,
            'error_message': m.error_message
        })
    
    return result


@router.post("/cache/sync")
def trigger_cache_sync(
    force: bool = Query(False, description="是否强制同步"),
    db: Session = Depends(get_db),
    local_db: Session = Depends(get_local_db)
):
    service = CacheSyncService(db, local_db)
    results = service.sync_all_static_data(force=force)
    return {"message": "缓存同步完成", "results": results}


@router.get("/org/detail/{org_id}")
def get_org_detail(
    org_id: int,
    time_range: str = Query('month', description="时间范围: month(月), quarter(季), half_year(半年), year(年)"),
    time_type: str = Query('work', description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    local_db: Session = Depends(get_local_db),
    db: Session = Depends(get_db)
):
    org = local_db.query(LocalOrganization).filter(LocalOrganization.id == org_id, LocalOrganization.deleted == 0).first()
    if not org:
        return {"error": "Organization not found"}
    
    devices = local_db.query(LocalDevice).filter(
        LocalDevice.organization_id == org_id,
        LocalDevice.deleted == 0
    ).all()
    
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    
    total_devices = len(devices)
    total_memory_gb = 0
    total_compute_tflops = 0
    total_gpus = 0
    
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
    
    if time_type == "work":
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_work
    elif time_type == "nonwork":
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate_nonwork
    else:
        usage_field = LocalOrgGpuUsageSummary.avg_gpu_usage_rate
    
    org_usage = local_db.query(
        func.avg(usage_field).label('avg_usage'),
        func.avg(LocalOrgGpuUsageSummary.avg_memory_usage_rate).label('avg_memory_usage')
    ).filter(
        LocalOrgGpuUsageSummary.organization_id3 == org_id,
        LocalOrgGpuUsageSummary.summary_time >= start_datetime,
        LocalOrgGpuUsageSummary.summary_time <= end_datetime
    ).first()
    
    avg_usage_rate = round(float(org_usage.avg_usage or 0), 2) if org_usage and org_usage.avg_usage else 0
    avg_memory_utilization = round(float(org_usage.avg_memory_usage or 0), 2) if org_usage and org_usage.avg_memory_usage else 0
    
    device_list = []
    for device in devices:
        gpu_count = device.gpu_count or 0
        gpu_model = device.gpu_model or ""
        gpu_info = gpu_infos.get(gpu_model)
        
        memory_gb = 0
        compute_tflops = 0
        if gpu_info:
            memory_gb = float(gpu_info.memory_total_gb or 0) * gpu_count
            compute_tflops = float(gpu_info.tflops_fp16 or 0) * gpu_count
        
        total_gpus += gpu_count
        total_memory_gb += memory_gb
        total_compute_tflops += compute_tflops
        
        latest_monitor = db.query(DeviceGpuMonitor).filter(
            DeviceGpuMonitor.device_id == device.id
        ).order_by(desc(DeviceGpuMonitor.collection_timestamp)).first()
        
        is_online = 0
        if latest_monitor:
            time_diff = datetime.now() - latest_monitor.collection_timestamp
            if time_diff.total_seconds() < ONLINE_THRESHOLD_MINUTES * 60:
                is_online = 1
        
        avg_usage = 0
        if latest_monitor and latest_monitor.avg_gpu_utilization is not None:
            avg_usage = float(latest_monitor.avg_gpu_utilization)
        
        memory_used_gb = 0
        memory_usage_rate = 0
        memory_utilization = 0
        if latest_monitor:
            if latest_monitor.used_memory_mb is not None:
                memory_used_gb = round(float(latest_monitor.used_memory_mb) / 1024, 2)
            if latest_monitor.memory_usage_percent is not None:
                memory_usage_rate = round(float(latest_monitor.memory_usage_percent), 2)
            if latest_monitor.avg_memory_utilization is not None:
                memory_utilization = round(float(latest_monitor.avg_memory_utilization), 2)
        
        updated_at = None
        if latest_monitor:
            updated_at = latest_monitor.collection_timestamp.isoformat() if latest_monitor.collection_timestamp else None

        device_list.append({
            "id": device.id,
            "name": device.name,
            "code": device.code,
            "gpu_model": device.gpu_model,
            "gpu_count": gpu_count,
            "memory_gb": round(memory_gb, 2),
            "compute_tflops": round(compute_tflops, 2),
            "cpu_cores": device.cpu_cores,
            "memory_size": float(device.memory_size or 0),
            "disk_size": float(device.disk_size or 0),
            "usage_rate": avg_usage,
            "memory_used_gb": memory_used_gb,
            "memory_usage_rate": memory_usage_rate,
            "memory_utilization": memory_utilization,
            "is_online": is_online,
            "purpose": device.purpose,
            "net_module_name": device.net_module_name,
            "updated_at": updated_at
        })
    
    memory_used_gb = round(total_memory_gb * avg_memory_utilization / 100, 2) if total_memory_gb > 0 and avg_memory_utilization > 0 else 0
    memory_usage_rate = avg_memory_utilization
    
    return {
        "org_id": org.id,
        "org_name": org.name,
        "org_code": org.code,
        "total_devices": total_devices,
        "total_gpus": total_gpus,
        "total_memory_gb": round(total_memory_gb, 2),
        "total_compute_tflops": round(total_compute_tflops, 2),
        "avg_usage_rate": avg_usage_rate,
        "memory_used_gb": memory_used_gb,
        "memory_usage_rate": memory_usage_rate,
        "avg_memory_utilization": avg_memory_utilization,
        "devices": device_list
    }


@router.get("/org/usage-trend/{org_id}")
def get_org_usage_trend(
    org_id: int,
    time_type: str = Query("all", description="时间类型: work(工作时间), nonwork(非工作时间), all(全天)"),
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期"),
    purpose: int = Query(None, description="用途过滤: 1-训练, 2-研发, 3-推理"),
    local_db: Session = Depends(get_local_db)
):
    org = local_db.query(LocalOrganization).filter(LocalOrganization.id == org_id, LocalOrganization.deleted == 0).first()
    if not org:
        return {"error": "Organization not found"}
    
    if not start_date:
        end_date_obj = date.today()
        start_date_obj = end_date_obj - timedelta(days=90)
    else:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else date.today()
    
    start_datetime = datetime.combine(start_date_obj, datetime.min.time())
    end_datetime = datetime.combine(end_date_obj, datetime.max.time())
    
    monthly_data = {}
    daily_data = {}
    hourly_data = {}
    monthly_memory_data = {}
    daily_memory_data = {}
    hourly_memory_data = {}
    
    if purpose is not None:
        device_query = local_db.query(LocalDevice.id).filter(
            LocalDevice.deleted == 0,
            LocalDevice.purpose == purpose
        )
        
        if org_id:
            device_query = device_query.filter(LocalDevice.organization_id == org_id)
        
        device_ids = [d.id for d in device_query.all()]
        
        if not device_ids:
            return {
                "org_id": org_id,
                "org_name": org.name,
                "monthly": [],
                "daily": [],
                "hourly": [],
                "warning": None
            }
        
        for summary in local_db.query(LocalDailyDeviceSummary).filter(
            LocalDailyDeviceSummary.device_id.in_(device_ids),
            LocalDailyDeviceSummary.summary_date >= start_date_obj,
            LocalDailyDeviceSummary.summary_date <= end_date_obj
        ).order_by(LocalDailyDeviceSummary.summary_date).all():
            month_key = summary.summary_date.strftime('%Y-%m')
            day_key = summary.summary_date.strftime('%Y-%m-%d')
            
            if time_type == "work":
                val = float(summary.avg_gpu_usage_rate_work or 0)
            elif time_type == "nonwork":
                val = float(summary.avg_gpu_usage_rate_nonwork or 0)
            else:
                val = float(summary.avg_gpu_usage_rate or 0)
            
            memory_val = float(summary.avg_memory_usage_rate or 0)
            
            if month_key not in monthly_data:
                monthly_data[month_key] = []
                monthly_memory_data[month_key] = []
            monthly_data[month_key].append(val)
            monthly_memory_data[month_key].append(memory_val)
            
            if day_key not in daily_data:
                daily_data[day_key] = []
                daily_memory_data[day_key] = []
            daily_data[day_key].append(val)
            daily_memory_data[day_key].append(memory_val)
        
        for hourly in local_db.query(LocalDeviceHourlyStats).filter(
            LocalDeviceHourlyStats.device_id.in_(device_ids),
            LocalDeviceHourlyStats.stat_date >= start_date_obj,
            LocalDeviceHourlyStats.stat_date <= end_date_obj
        ).order_by(LocalDeviceHourlyStats.stat_hour).all():
            if hourly.is_work_hour == 1 and time_type == "nonwork":
                continue
            if hourly.is_work_hour == 0 and time_type == "work":
                continue
            
            hour_key = str(hourly.stat_hour)
            if hour_key not in hourly_data:
                hourly_data[hour_key] = []
                hourly_memory_data[hour_key] = []
            hourly_data[hour_key].append(float(hourly.avg_gpu_usage_rate or 0))
            hourly_memory_data[hour_key].append(0)
    else:
        for summary in local_db.query(LocalOrgGpuUsageSummary).filter(
            LocalOrgGpuUsageSummary.organization_id3 == org_id,
            LocalOrgGpuUsageSummary.summary_time >= start_datetime,
            LocalOrgGpuUsageSummary.summary_time <= end_datetime
        ).order_by(LocalOrgGpuUsageSummary.summary_time).all():
            month_key = summary.summary_time.strftime('%Y-%m')
            day_key = summary.summary_time.strftime('%Y-%m-%d')
            
            if time_type == "work":
                val = float(summary.avg_gpu_usage_rate_work or 0)
            elif time_type == "nonwork":
                val = float(summary.avg_gpu_usage_rate_nonwork or 0)
            else:
                val = float(summary.avg_gpu_usage_rate or 0)
            
            memory_val = float(summary.avg_memory_usage_rate or 0)
            
            if month_key not in monthly_data:
                monthly_data[month_key] = []
                monthly_memory_data[month_key] = []
            monthly_data[month_key].append(val)
            monthly_memory_data[month_key].append(memory_val)
            
            if day_key not in daily_data:
                daily_data[day_key] = []
                daily_memory_data[day_key] = []
            daily_data[day_key].append(val)
            daily_memory_data[day_key].append(memory_val)
        
        for hourly in local_db.query(LocalOrgHourlyStats).filter(
            LocalOrgHourlyStats.organization_id3 == org_id,
            LocalOrgHourlyStats.stat_date >= start_date_obj,
            LocalOrgHourlyStats.stat_date <= end_date_obj
        ).order_by(LocalOrgHourlyStats.stat_hour).all():
            if hourly.is_work_hour == 1 and time_type == "nonwork":
                continue
            if hourly.is_work_hour == 0 and time_type == "work":
                continue
            
            hour_key = str(hourly.stat_hour)
            if hour_key not in hourly_data:
                hourly_data[hour_key] = []
                hourly_memory_data[hour_key] = []
            hourly_data[hour_key].append(float(hourly.avg_gpu_usage_rate or 0))
            hourly_memory_data[hour_key].append(0)
    
    monthly_result = [
        {
            "month": k, 
            "avg_usage": round(sum(monthly_data.get(k, [])) / len(monthly_data.get(k, [])), 2) if monthly_data.get(k) else 0,
            "avg_memory_usage": round(sum(monthly_memory_data.get(k, [])) / len(monthly_memory_data.get(k, [])), 2) if monthly_memory_data.get(k) else 0
        }
        for k in sorted(monthly_data.keys())
    ]
    
    daily_result = [
        {
            "date": k, 
            "avg_usage": round(sum(daily_data.get(k, [])) / len(daily_data.get(k, [])), 2) if daily_data.get(k) else 0,
            "avg_memory_usage": round(sum(daily_memory_data.get(k, [])) / len(daily_memory_data.get(k, [])), 2) if daily_memory_data.get(k) else 0
        }
        for k in sorted(daily_data.keys())
    ]
    
    hourly_result = []
    for hour in range(24):
        hour_key = str(hour)
        values = hourly_data.get(hour_key, [])
        memory_values = hourly_memory_data.get(hour_key, [])
        hourly_result.append({
            "hour": hour,
            "avg_usage": round(sum(values) / len(values), 2) if values else 0,
            "avg_memory_usage": round(sum(memory_values) / len(memory_values), 2) if memory_values else 0
        })
    
    warning_info = None
    config_map = {c.config_key: c.config_value for c in local_db.query(LocalSystemConfig).all()}
    high_threshold = float(config_map.get("high_usage_threshold", settings.HIGH_USAGE_THRESHOLD))
    low_threshold = float(config_map.get("low_usage_threshold", settings.LOW_USAGE_THRESHOLD))
    
    if len(monthly_result) >= 2:
        recent_months = monthly_result[-2:]
        avg_recent = sum(m["avg_usage"] for m in recent_months) / len(recent_months)
        
        if avg_recent > high_threshold:
            warning_info = {
                "type": "high",
                "value": round(avg_recent, 2),
                "threshold": high_threshold,
                "message": f"近两个月平均使用率{avg_recent:.1f}%超过{high_threshold}%阈值，建议增加设备或优化资源调度"
            }
        elif avg_recent < low_threshold:
            warning_info = {
                "type": "low",
                "value": round(avg_recent, 2),
                "threshold": low_threshold,
                "message": f"近两个月平均使用率{avg_recent:.1f}%低于{low_threshold}%阈值，建议分析原因或资源整合"
            }
    
    return {
        "org_id": org_id,
        "org_name": org.name,
        "monthly": monthly_result,
        "daily": daily_result,
        "hourly": hourly_result,
        "warning": warning_info
    }


@router.get("/org/distribution/{org_id}")
def get_org_distribution(
    org_id: int,
    local_db: Session = Depends(get_local_db)
):
    org = local_db.query(LocalOrganization).filter(LocalOrganization.id == org_id, LocalOrganization.deleted == 0).first()
    if not org:
        return {"error": "Organization not found"}
    
    devices = local_db.query(LocalDevice).filter(
        LocalDevice.organization_id == org_id,
        LocalDevice.deleted == 0
    ).all()
    
    gpu_infos = {g.gpu_name: g for g in local_db.query(LocalGpuCardInfo).filter(LocalGpuCardInfo.deleted == 0).all()}
    purpose_map = get_purpose_map(local_db)
    
    gpu_tier_dist = {}
    network_dist = {}
    purpose_dist = {}
    
    for device in devices:
        gpu_count = device.gpu_count or 1
        
        gpu_model = device.gpu_model or ""
        gpu_info = gpu_infos.get(gpu_model)
        gpu_tier = "未知"
        if gpu_info:
            tflops = float(gpu_info.tflops_fp16 or 0)
            if tflops >= 100:
                gpu_tier = "高端"
            elif tflops >= 50:
                gpu_tier = "中端"
            else:
                gpu_tier = "入门级"
        
        if gpu_tier not in gpu_tier_dist:
            gpu_tier_dist[gpu_tier] = 0
        gpu_tier_dist[gpu_tier] += gpu_count
        
        network = device.net_module_name or "未知"
        if network not in network_dist:
            network_dist[network] = 0
        network_dist[network] += gpu_count
        
        purpose = purpose_map.get(device.purpose, "未知")
        if purpose not in purpose_dist:
            purpose_dist[purpose] = 0
        purpose_dist[purpose] += gpu_count
    
    return {
        "org_id": org_id,
        "org_name": org.name,
        "gpu_tier": [{"name": k, "value": v} for k, v in gpu_tier_dist.items()],
        "network": [{"name": k, "value": v} for k, v in network_dist.items()],
        "purpose": [{"name": k, "value": v} for k, v in purpose_dist.items()]
    }


@router.get("/device/usage-trend/{device_id}")
def get_device_usage_trend(
    device_id: int,
    time_type: str = Query("all", description="时间类型：work(工作时间), nonwork(非工作时间), all(全天)"),
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期"),
    local_db: Session = Depends(get_local_db)
):
    from datetime import datetime, timedelta
    
    device = local_db.query(LocalDevice).filter(LocalDevice.id == device_id, LocalDevice.deleted == 0).first()
    if not device:
        return {"error": "Device not found"}
    
    if not start_date:
        end_date_obj = date.today()
        start_date_obj = end_date_obj - timedelta(days=90)
    else:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else date.today()
    
    monthly_data = {}
    daily_data = {}
    hourly_data = {}
    
    # 从 LocalDailyDeviceSummary 获取日度和月度数据
    for summary in local_db.query(LocalDailyDeviceSummary).filter(
        LocalDailyDeviceSummary.device_id == device_id,
        LocalDailyDeviceSummary.summary_date >= start_date_obj,
        LocalDailyDeviceSummary.summary_date <= end_date_obj
    ).order_by(LocalDailyDeviceSummary.summary_date).all():
        month_key = summary.summary_date.strftime('%Y-%m')
        day_key = summary.summary_date.strftime('%Y-%m-%d')
        
        # 根据时间类型选择字段
        if time_type == "work":
            val = float(summary.avg_gpu_usage_rate_work or 0)
        elif time_type == "nonwork":
            val = float(summary.avg_gpu_usage_rate_nonwork or 0)
        else:
            val = float(summary.avg_gpu_usage_rate or 0)
        
        if month_key not in monthly_data:
            monthly_data[month_key] = []
        monthly_data[month_key].append(val)
        
        daily_data[day_key] = val
    
    # 从 LocalDeviceHourlyStats 获取小时数据
    for summary in local_db.query(LocalDeviceHourlyStats).filter(
        LocalDeviceHourlyStats.device_id == device_id,
        func.date(LocalDeviceHourlyStats.stat_date) >= start_date_obj,
        func.date(LocalDeviceHourlyStats.stat_date) <= end_date_obj
    ).order_by(LocalDeviceHourlyStats.stat_hour).all():
        hour = summary.stat_hour
        val = float(summary.avg_gpu_usage_rate or 0)
        if hour not in hourly_data:
            hourly_data[hour] = []
        hourly_data[hour].append(val)
    
    monthly_result = []
    for month in sorted(monthly_data.keys()):
        values = monthly_data[month]
        avg_val = sum(values) / len(values) if values else 0
        monthly_result.append({
            "month": month,
            "avg_usage": round(avg_val, 2)
        })
    
    daily_result = [
        {"date": date_key, "avg_usage": round(val, 2)}
        for date_key, val in sorted(daily_data.items())
    ]
    
    hourly_result = [
        {"hour": hour, "avg_usage": round(sum(values) / len(values), 2) if values else 0}
        for hour, values in sorted(hourly_data.items())
    ]
    
    return {
        "device_id": device_id,
        "device_name": device.name,
        "monthly": monthly_result,
        "daily": daily_result,
        "hourly": hourly_result
    }

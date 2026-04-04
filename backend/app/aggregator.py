import logging
from datetime import date, timedelta, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)
from app.database import SessionLocal
from app.local_database import LocalSessionLocal
from app.models import (
    Device, DeviceGpuMonitor, DeviceGpuMonitorDetail, 
    GpuCardInfo, Organization
)
from app.local_models import (
    LocalDailyGpuUsageSummary, LocalDailyDeviceSummary, LocalDeviceHourlyStats,
    LocalOrgGpuUsageSummary, LocalStatisticsData, LocalSystemConfig, LocalOrgHourlyStats
)
from app.config import settings
from app.org_constants import ORG_CODE_CHINA, ORG_NAME_LOCAL_KEYWORD, ORG_NAME_MINISTRY_KEYWORD


class DataAggregator:
    def __init__(self, db: Session, local_db: Session):
        self.db = db
        self.local_db = local_db
        self._load_config()
        self._load_org_ids()
    
    def _load_config(self):
        configs = self.local_db.query(LocalSystemConfig).all()
        self.config = {c.config_key: c.config_value for c in configs}
        
        self.work_hour_start = int(self.config.get("work_hour_start", settings.WORK_HOUR_START))
        self.work_hour_end = int(self.config.get("work_hour_end", settings.WORK_HOUR_END))
        self.high_threshold = float(self.config.get("high_usage_threshold", settings.HIGH_USAGE_THRESHOLD))
        self.low_threshold = float(self.config.get("low_usage_threshold", settings.LOW_USAGE_THRESHOLD))
    
    def _load_org_ids(self):
        self.china_org_id = None
        self.local_group_id = None
        self.ministry_group_id = None
        
        china_org = self.db.query(Organization).filter(
            Organization.code == ORG_CODE_CHINA,
            Organization.deleted == 0
        ).first()
        
        if china_org:
            self.china_org_id = china_org.id
            
            groups = self.db.query(Organization).filter(
                Organization.parent_id == china_org.id,
                Organization.deleted == 0
            ).all()
            
            for group in groups:
                group_name = group.name or ""
                if ORG_NAME_LOCAL_KEYWORD in group_name:
                    self.local_group_id = group.id
                elif ORG_NAME_MINISTRY_KEYWORD in group_name:
                    self.ministry_group_id = group.id
    
    def aggregate_daily_summary(self, target_date: Optional[date] = None):
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        device_avg_usages = self.db.query(
            DeviceGpuMonitor.device_id,
            func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("device_avg_usage")
        ).filter(
            DeviceGpuMonitor.collection_timestamp >= start_time,
            DeviceGpuMonitor.collection_timestamp <= end_time
        ).group_by(
            DeviceGpuMonitor.device_id
        ).all()
        
        device_count = len(device_avg_usages)
        total_device_avg_usage = sum(float(d.device_avg_usage or 0) for d in device_avg_usages)
        avg_gpu_usage = round(total_device_avg_usage / device_count, 2) if device_count > 0 else 0
        
        work_start = datetime.combine(target_date, datetime.min.time().replace(hour=self.work_hour_start))
        work_end = datetime.combine(target_date, datetime.min.time().replace(hour=self.work_hour_end))
        
        device_avg_usages_work = self.db.query(
            DeviceGpuMonitor.device_id,
            func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("device_avg_usage")
        ).filter(
            DeviceGpuMonitor.collection_timestamp >= start_time,
            DeviceGpuMonitor.collection_timestamp <= end_time,
            DeviceGpuMonitor.collection_timestamp >= work_start,
            DeviceGpuMonitor.collection_timestamp < work_end
        ).group_by(
            DeviceGpuMonitor.device_id
        ).all()
        
        device_count_work = len(device_avg_usages_work)
        total_device_avg_usage_work = sum(float(d.device_avg_usage or 0) for d in device_avg_usages_work)
        avg_gpu_usage_work = round(total_device_avg_usage_work / device_count_work, 2) if device_count_work > 0 else 0
        
        device_avg_usages_nonwork = self.db.query(
            DeviceGpuMonitor.device_id,
            func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("device_avg_usage")
        ).filter(
            DeviceGpuMonitor.collection_timestamp >= start_time,
            DeviceGpuMonitor.collection_timestamp <= end_time,
            or_(
                DeviceGpuMonitor.collection_timestamp < work_start,
                DeviceGpuMonitor.collection_timestamp >= work_end
            )
        ).group_by(
            DeviceGpuMonitor.device_id
        ).all()
        
        device_count_nonwork = len(device_avg_usages_nonwork)
        total_device_avg_usage_nonwork = sum(float(d.device_avg_usage or 0) for d in device_avg_usages_nonwork)
        avg_gpu_usage_nonwork = round(total_device_avg_usage_nonwork / device_count_nonwork, 2) if device_count_nonwork > 0 else 0
        
        result = self.db.query(
            func.count(func.distinct(DeviceGpuMonitor.device_id)).label("device_count"),
            func.sum(DeviceGpuMonitor.gpu_count).label("gpu_count"),
            func.max(DeviceGpuMonitor.max_gpu_utilization).label("max_gpu_usage"),
            func.min(DeviceGpuMonitor.min_gpu_utilization).label("min_gpu_usage"),
            func.avg(DeviceGpuMonitor.memory_usage_percent).label("avg_memory_usage"),
            func.max(DeviceGpuMonitor.memory_usage_percent).label("max_memory_usage"),
            func.min(DeviceGpuMonitor.memory_usage_percent).label("min_memory_usage"),
            func.avg(DeviceGpuMonitor.avg_temperature).label("avg_temperature"),
            func.max(DeviceGpuMonitor.max_temperature).label("max_temperature"),
            func.sum(DeviceGpuMonitor.total_memory_mb).label("total_memory_mb"),
            func.count(DeviceGpuMonitor.id).label("sample_count"),
            func.sum(DeviceGpuMonitor.avg_gpu_utilization).label("gpu_rate_sum")
        ).filter(
            DeviceGpuMonitor.collection_timestamp >= start_time,
            DeviceGpuMonitor.collection_timestamp <= end_time
        ).first()
        
        if result and result.device_count > 0:
            device_ids_with_data = [d.device_id for d in device_avg_usages]
            devices = self.db.query(Device).filter(
                Device.id.in_(device_ids_with_data),
                Device.deleted == 0
            ).all()
            gpu_infos = {g.gpu_name: g for g in self.db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
            
            total_tflops = 0
            for device in devices:
                gpu_model = device.gpu_model or ""
                gpu_count = device.gpu_count or 0
                gpu_info = gpu_infos.get(gpu_model)
                if gpu_info and gpu_info.tflops_fp32:
                    total_tflops += float(gpu_info.tflops_fp32) * gpu_count
            
            existing = self.local_db.query(LocalDailyGpuUsageSummary).filter(
                LocalDailyGpuUsageSummary.summary_date == start_time
            ).first()
            
            if existing:
                summary = existing
            else:
                summary = LocalDailyGpuUsageSummary(summary_date=start_time)
            
            summary.total_device_count = result.device_count
            summary.total_gpu_count = result.gpu_count or 0
            summary.avg_gpu_usage_rate = avg_gpu_usage
            summary.max_gpu_usage_rate = round(float(result.max_gpu_usage or 0), 2)
            summary.min_gpu_usage_rate = round(float(result.min_gpu_usage or 0), 2)
            summary.avg_memory_usage_rate = round(float(result.avg_memory_usage or 0), 2)
            summary.max_memory_usage_rate = round(float(result.max_memory_usage or 0), 2)
            summary.min_memory_usage_rate = round(float(result.min_memory_usage or 0), 2)
            summary.avg_temperature = round(float(result.avg_temperature or 0), 2)
            summary.max_temperature = round(float(result.max_temperature or 0), 2)
            summary.memory_total_gb = round(float(result.total_memory_mb or 0) / 1024, 2)
            summary.compute_total_tflops = round(total_tflops, 2)
            summary.total_sample_count = result.sample_count
            summary.total_gpu_rate_sum = int(result.gpu_rate_sum or 0)
            summary.avg_gpu_usage_rate_work = avg_gpu_usage_work
            summary.avg_gpu_usage_rate_nonwork = avg_gpu_usage_nonwork
            
            if not existing:
                self.local_db.add(summary)
            
            self.local_db.commit()
            print(f"日汇总完成: {target_date}")
        
        return result
    
    def aggregate_device_summary(self, target_date: Optional[date] = None):
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        work_start = datetime.combine(target_date, datetime.min.time().replace(hour=self.work_hour_start))
        work_end = datetime.combine(target_date, datetime.min.time().replace(hour=self.work_hour_end))
        
        devices = self.db.query(Device).filter(Device.deleted == 0).all()
        
        for device in devices:
            result = self.db.query(
                func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("avg_usage"),
                func.avg(DeviceGpuMonitor.memory_usage_percent).label("avg_memory_usage"),
                func.avg(DeviceGpuMonitor.avg_memory_utilization).label("avg_memory_utilization")
            ).filter(
                DeviceGpuMonitor.device_id == device.id,
                DeviceGpuMonitor.collection_timestamp >= start_time,
                DeviceGpuMonitor.collection_timestamp <= end_time
            ).first()
            
            result_work = self.db.query(
                func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("avg_usage"),
                func.avg(DeviceGpuMonitor.memory_usage_percent).label("avg_memory_usage"),
                func.avg(DeviceGpuMonitor.avg_memory_utilization).label("avg_memory_utilization")
            ).filter(
                DeviceGpuMonitor.device_id == device.id,
                DeviceGpuMonitor.collection_timestamp >= start_time,
                DeviceGpuMonitor.collection_timestamp <= end_time,
                DeviceGpuMonitor.collection_timestamp >= work_start,
                DeviceGpuMonitor.collection_timestamp < work_end
            ).first()
            
            result_nonwork = self.db.query(
                func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("avg_usage"),
                func.avg(DeviceGpuMonitor.memory_usage_percent).label("avg_memory_usage"),
                func.avg(DeviceGpuMonitor.avg_memory_utilization).label("avg_memory_utilization")
            ).filter(
                DeviceGpuMonitor.device_id == device.id,
                DeviceGpuMonitor.collection_timestamp >= start_time,
                DeviceGpuMonitor.collection_timestamp <= end_time,
                or_(
                    DeviceGpuMonitor.collection_timestamp < work_start,
                    DeviceGpuMonitor.collection_timestamp >= work_end
                )
            ).first()
            
            if result and result.avg_usage is not None:
                org = self.db.query(Organization).filter(
                    Organization.id == device.organization_id,
                    Organization.deleted == 0
                ).first()
                
                existing = self.local_db.query(LocalDailyDeviceSummary).filter(
                    LocalDailyDeviceSummary.device_id == device.id,
                    LocalDailyDeviceSummary.summary_date == start_time
                ).first()
                
                if existing:
                    summary = existing
                else:
                    summary = LocalDailyDeviceSummary(
                        device_id=device.id,
                        device_name=device.name,
                        summary_date=start_time
                    )
                
                if org:
                    summary.organization_id3 = org.id
                    summary.organization_name3 = org.name or ""
                    summary.province_code = org.province_code or ""
                    summary.province = org.province or ""
                    
                    if self.china_org_id and org.parent_id == self.china_org_id:
                        summary.organization_id1 = org.id
                        summary.organization_name1 = org.name or ""
                    elif org.parent_id in [self.local_group_id, self.ministry_group_id]:
                        parent_org = self.db.query(Organization).filter(
                            Organization.id == org.parent_id,
                            Organization.deleted == 0
                        ).first()
                        if parent_org:
                            summary.organization_id1 = parent_org.id
                            summary.organization_name1 = parent_org.name or ""
                
                summary.avg_gpu_usage_rate = round(float(result.avg_usage or 0), 2)
                summary.avg_gpu_usage_rate_work = round(float(result_work.avg_usage or 0), 2)
                summary.avg_gpu_usage_rate_nonwork = round(float(result_nonwork.avg_usage or 0), 2)
                summary.avg_memory_usage_rate = round(float(result.avg_memory_usage or 0), 2)
                summary.avg_memory_utilization = round(float(result.avg_memory_utilization or 0), 2)
                
                if not existing:
                    self.local_db.add(summary)
        
        self.local_db.commit()
        print(f"设备日汇总完成：{target_date}")
    
    def aggregate_device_hourly_stats(self, target_date: Optional[date] = None):
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        devices = self.db.query(Device).filter(Device.deleted == 0).all()
        
        for device in devices:
            for hour in range(24):
                hour_start = start_time + timedelta(hours=hour)
                hour_end = hour_start + timedelta(hours=1)
                
                device_stats = self.db.query(
                    DeviceGpuMonitor.device_id,
                    func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("device_avg_usage"),
                    func.avg(DeviceGpuMonitor.memory_usage_percent).label("avg_memory_usage"),
                    func.avg(DeviceGpuMonitor.avg_memory_utilization).label("avg_memory_utilization")
                ).filter(
                    DeviceGpuMonitor.device_id == device.id,
                    DeviceGpuMonitor.collection_timestamp >= hour_start,
                    DeviceGpuMonitor.collection_timestamp < hour_end
                ).group_by(
                    DeviceGpuMonitor.device_id
                ).first()
                
                device_count = 0
                avg_gpu_usage = 0
                avg_memory_usage = 0
                avg_memory_utilization = 0
                if device_stats and device_stats.device_avg_usage is not None:
                    device_count = 1
                    avg_gpu_usage = round(float(device_stats.device_avg_usage or 0), 2)
                    avg_memory_usage = round(float(device_stats.avg_memory_usage or 0), 2)
                    avg_memory_utilization = round(float(device_stats.avg_memory_utilization or 0), 2)
                
                is_work_hour = 1 if self.work_hour_start <= hour < self.work_hour_end else 0
                
                if device_count > 0:
                    org = self.db.query(Organization).filter(
                        Organization.id == device.organization_id,
                        Organization.deleted == 0
                    ).first()
                    
                    existing = self.local_db.query(LocalDeviceHourlyStats).filter(
                        LocalDeviceHourlyStats.device_id == device.id,
                        LocalDeviceHourlyStats.stat_date == start_time,
                        LocalDeviceHourlyStats.stat_hour == hour
                    ).first()
                    
                    if existing:
                        stat = existing
                    else:
                        stat = LocalDeviceHourlyStats(
                            device_id=device.id,
                            device_name=device.name,
                            stat_date=start_time,
                            stat_hour=hour
                        )
                    
                    if org:
                        stat.organization_id3 = org.id
                        stat.organization_name3 = org.name or ""
                    
                    stat.avg_gpu_usage_rate = avg_gpu_usage
                    stat.avg_memory_usage_rate = avg_memory_usage
                    stat.avg_memory_utilization = avg_memory_utilization
                    stat.device_count = device_count
                    stat.is_work_hour = is_work_hour
                    
                    if not existing:
                        self.local_db.add(stat)
        
        self.local_db.commit()
        print(f"设备小时数据汇总完成：{target_date}")
    
    def aggregate_org_summary(self, target_date: Optional[date] = None):
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        orgs = self.db.query(Organization).filter(
            Organization.deleted == 0
        ).all()
        
        for org in orgs:
            devices = self.db.query(Device).filter(
                Device.organization_id == org.id,
                Device.deleted == 0
            ).all()
            
            if not devices:
                continue
            
            device_ids = [d.id for d in devices]
            
            device_avg_usages = self.db.query(
                DeviceGpuMonitor.device_id,
                func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("device_avg_usage")
            ).filter(
                DeviceGpuMonitor.device_id.in_(device_ids),
                DeviceGpuMonitor.collection_timestamp >= start_time,
                DeviceGpuMonitor.collection_timestamp <= end_time
            ).group_by(
                DeviceGpuMonitor.device_id
            ).all()
            
            device_count = len(device_avg_usages)
            total_device_avg_usage = sum(float(d.device_avg_usage or 0) for d in device_avg_usages)
            avg_gpu_usage = round(total_device_avg_usage / device_count, 2) if device_count > 0 else 0
            
            work_start = datetime.combine(target_date, datetime.min.time().replace(hour=self.work_hour_start))
            work_end = datetime.combine(target_date, datetime.min.time().replace(hour=self.work_hour_end))
            
            device_avg_usages_work = self.db.query(
                DeviceGpuMonitor.device_id,
                func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("device_avg_usage")
            ).filter(
                DeviceGpuMonitor.device_id.in_(device_ids),
                DeviceGpuMonitor.collection_timestamp >= start_time,
                DeviceGpuMonitor.collection_timestamp <= end_time,
                DeviceGpuMonitor.collection_timestamp >= work_start,
                DeviceGpuMonitor.collection_timestamp < work_end
            ).group_by(
                DeviceGpuMonitor.device_id
            ).all()
            
            device_count_work = len(device_avg_usages_work)
            total_device_avg_usage_work = sum(float(d.device_avg_usage or 0) for d in device_avg_usages_work)
            avg_gpu_usage_work = round(total_device_avg_usage_work / device_count_work, 2) if device_count_work > 0 else 0
            
            device_avg_usages_nonwork = self.db.query(
                DeviceGpuMonitor.device_id,
                func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("device_avg_usage")
            ).filter(
                DeviceGpuMonitor.device_id.in_(device_ids),
                DeviceGpuMonitor.collection_timestamp >= start_time,
                DeviceGpuMonitor.collection_timestamp <= end_time,
                or_(
                    DeviceGpuMonitor.collection_timestamp < work_start,
                    DeviceGpuMonitor.collection_timestamp >= work_end
                )
            ).group_by(
                DeviceGpuMonitor.device_id
            ).all()
            
            device_count_nonwork = len(device_avg_usages_nonwork)
            total_device_avg_usage_nonwork = sum(float(d.device_avg_usage or 0) for d in device_avg_usages_nonwork)
            avg_gpu_usage_nonwork = round(total_device_avg_usage_nonwork / device_count_nonwork, 2) if device_count_nonwork > 0 else 0
            
            result = self.db.query(
                func.count(func.distinct(DeviceGpuMonitor.device_id)).label("device_count"),
                func.sum(DeviceGpuMonitor.gpu_count).label("gpu_count"),
                func.avg(DeviceGpuMonitor.memory_usage_percent).label("avg_memory_usage"),
                func.avg(DeviceGpuMonitor.avg_memory_utilization).label("avg_memory_utilization"),
                func.max(DeviceGpuMonitor.max_gpu_utilization).label("max_gpu_usage"),
                func.min(DeviceGpuMonitor.min_gpu_utilization).label("min_gpu_usage"),
                func.max(DeviceGpuMonitor.collection_timestamp).label("latest_time")
            ).filter(
                DeviceGpuMonitor.device_id.in_(device_ids),
                DeviceGpuMonitor.collection_timestamp >= start_time,
                DeviceGpuMonitor.collection_timestamp <= end_time
            ).first()
            
            if result and result.device_count > 0:
                existing = self.local_db.query(LocalOrgGpuUsageSummary).filter(
                    LocalOrgGpuUsageSummary.organization_id3 == org.id,
                    LocalOrgGpuUsageSummary.summary_time == start_time
                ).first()
                
                if existing:
                    summary = existing
                else:
                    summary = LocalOrgGpuUsageSummary(
                        organization_id3=org.id,
                        organization_name3=org.name or "",
                        organization_code3=org.code or "",
                        summary_time=start_time
                    )
                
                if self.china_org_id and org.parent_id == self.china_org_id:
                    summary.organization_id1 = org.id
                    summary.organization_name1 = org.name or ""
                    summary.organization_id2 = org.id
                    summary.organization_name2 = org.name or ""
                elif org.parent_id in [self.local_group_id, self.ministry_group_id]:
                    parent_org = self.db.query(Organization).filter(
                        Organization.id == org.parent_id,
                        Organization.deleted == 0
                    ).first()
                    if parent_org:
                        summary.organization_id1 = parent_org.id
                        summary.organization_name1 = parent_org.name or ""
                    summary.organization_id2 = org.id
                    summary.organization_name2 = org.name or ""
                
                summary.province_code = org.province_code or ""
                summary.province = org.province or ""
                summary.device_count = result.device_count
                summary.gpu_count = result.gpu_count or 0
                summary.avg_gpu_usage_rate = avg_gpu_usage
                summary.avg_memory_usage_rate = round(float(result.avg_memory_usage or 0), 2)
                summary.avg_memory_utilization = round(float(result.avg_memory_utilization or 0), 2)
                summary.max_gpu_usage_rate = round(float(result.max_gpu_usage or 0), 2)
                summary.min_gpu_usage_rate = round(float(result.min_gpu_usage or 0), 2)
                summary.latest_collection_time = result.latest_time
                summary.avg_gpu_usage_rate_work = avg_gpu_usage_work
                summary.avg_gpu_usage_rate_nonwork = avg_gpu_usage_nonwork
                
                if not existing:
                    self.local_db.add(summary)
        
        self.local_db.commit()
        print(f"组织汇总完成: {target_date}")
    
    def aggregate_statistics_data(self, target_date: Optional[date] = None):
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        def get_all_org_ids(parent_id):
            result = []
            orgs = self.db.query(Organization).filter(
                Organization.parent_id == parent_id,
                Organization.deleted == 0
            ).all()
            for org in orgs:
                result.append(org.id)
                result.extend(get_all_org_ids(org.id))
            return result
        
        local_org_ids = []
        ministry_org_ids = []
        
        if self.local_group_id:
            local_org_ids = get_all_org_ids(self.local_group_id)
        
        if self.ministry_group_id:
            ministry_org_ids = get_all_org_ids(self.ministry_group_id)
        
        all_devices = self.db.query(Device).filter(Device.deleted == 0).all()
        device_org_map = {d.id: d.organization_id for d in all_devices}
        
        for hour in range(24):
            hour_start = start_time + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            
            for stat_type in ['ALL', 'LOCAL', 'MINISTRY']:
                if stat_type == 'LOCAL':
                    target_device_ids = [d.id for d in all_devices if device_org_map.get(d.id) in local_org_ids]
                elif stat_type == 'MINISTRY':
                    target_device_ids = [d.id for d in all_devices if device_org_map.get(d.id) in ministry_org_ids]
                else:
                    target_device_ids = [d.id for d in all_devices]
                
                if not target_device_ids:
                    continue
                
                device_avg_usages = self.db.query(
                    DeviceGpuMonitor.device_id,
                    func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("device_avg_usage")
                ).filter(
                    DeviceGpuMonitor.device_id.in_(target_device_ids),
                    DeviceGpuMonitor.collection_timestamp >= hour_start,
                    DeviceGpuMonitor.collection_timestamp < hour_end
                ).group_by(
                    DeviceGpuMonitor.device_id
                ).all()
                
                device_count = len(device_avg_usages)
                total_device_avg_usage = sum(float(d.device_avg_usage or 0) for d in device_avg_usages)
                avg_gpu_util = round(total_device_avg_usage / device_count, 2) if device_count > 0 else 0
                
                result = self.db.query(
                    func.count(func.distinct(DeviceGpuMonitor.device_id)).label("device_total"),
                    func.sum(DeviceGpuMonitor.total_memory_mb).label("memory_total"),
                    func.sum(DeviceGpuMonitor.used_memory_mb).label("memory_used"),
                    func.sum(DeviceGpuMonitor.gpu_count).label("gpu_count")
                ).filter(
                    DeviceGpuMonitor.device_id.in_(target_device_ids),
                    DeviceGpuMonitor.collection_timestamp >= hour_start,
                    DeviceGpuMonitor.collection_timestamp < hour_end
                ).first()
                
                if result and result.device_total > 0:
                    existing = self.local_db.query(LocalStatisticsData).filter(
                        LocalStatisticsData.stat_date == start_time,
                        LocalStatisticsData.stat_hour == hour,
                        LocalStatisticsData.stat_type == stat_type
                    ).first()
                    
                    if existing:
                        stat = existing
                    else:
                        stat = LocalStatisticsData(
                            stat_time=hour_start,
                            stat_date=start_time,
                            stat_hour=hour,
                            stat_type=stat_type
                        )
                    
                    is_work_hour = 1 if self.work_hour_start <= hour < self.work_hour_end else 0
                    
                    stat.device_total = result.device_total
                    stat.memory_total_gb = round(float(result.memory_total or 0) / 1024, 2)
                    stat.memory_used_gb = round(float(result.memory_used or 0) / 1024, 2)
                    stat.memory_free_gb = round(float(result.memory_total or 0) / 1024 - float(result.memory_used or 0) / 1024, 2)
                    stat.memory_usage_rate = round(float(result.memory_used or 0) / float(result.memory_total or 1) * 100, 2) if result.memory_total else 0
                    stat.avg_gpu_utilization = avg_gpu_util
                    stat.gpu_total_count = result.gpu_count or 0
                    stat.is_work_hour = is_work_hour
                    
                    if not existing:
                        self.local_db.add(stat)
        
        self.local_db.commit()
        print(f"统计数据汇总完成: {target_date}")
    
    def aggregate_org_hourly_stats(self, target_date: Optional[date] = None):
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())
        
        orgs = self.db.query(Organization).filter(
            Organization.deleted == 0
        ).all()
        
        for org in orgs:
            devices = self.db.query(Device).filter(
                Device.organization_id == org.id,
                Device.deleted == 0
            ).all()
            
            if not devices:
                continue
            
            device_ids = [d.id for d in devices]
            
            for hour in range(24):
                hour_start = start_time + timedelta(hours=hour)
                hour_end = hour_start + timedelta(hours=1)
                
                device_stats = self.db.query(
                    DeviceGpuMonitor.device_id,
                    func.avg(DeviceGpuMonitor.avg_gpu_utilization).label("device_avg_usage"),
                    func.avg(DeviceGpuMonitor.memory_usage_percent).label("avg_memory_usage"),
                    func.avg(DeviceGpuMonitor.avg_memory_utilization).label("avg_memory_utilization")
                ).filter(
                    DeviceGpuMonitor.device_id.in_(device_ids),
                    DeviceGpuMonitor.collection_timestamp >= hour_start,
                    DeviceGpuMonitor.collection_timestamp < hour_end
                ).group_by(
                    DeviceGpuMonitor.device_id
                ).all()
                
                device_count = len(device_stats)
                total_device_avg_usage = sum(float(d.device_avg_usage or 0) for d in device_stats)
                total_device_avg_memory = sum(float(d.avg_memory_usage or 0) for d in device_stats)
                total_device_avg_memory_utilization = sum(float(d.avg_memory_utilization or 0) for d in device_stats)
                avg_gpu_usage = round(total_device_avg_usage / device_count, 2) if device_count > 0 else 0
                avg_memory_usage = round(total_device_avg_memory / device_count, 2) if device_count > 0 else 0
                avg_memory_utilization = round(total_device_avg_memory_utilization / device_count, 2) if device_count > 0 else 0
                
                is_work_hour = 1 if self.work_hour_start <= hour < self.work_hour_end else 0
                
                if device_count > 0:
                    existing = self.local_db.query(LocalOrgHourlyStats).filter(
                        LocalOrgHourlyStats.organization_id3 == org.id,
                        LocalOrgHourlyStats.stat_date == start_time,
                        LocalOrgHourlyStats.stat_hour == hour
                    ).first()
                    
                    if existing:
                        stat = existing
                    else:
                        stat = LocalOrgHourlyStats(
                            organization_id3=org.id,
                            organization_name3=org.name or "",
                            stat_date=start_time,
                            stat_hour=hour
                        )
                    
                    stat.avg_gpu_usage_rate = avg_gpu_usage
                    stat.avg_memory_usage_rate = avg_memory_usage
                    stat.avg_memory_utilization = avg_memory_utilization
                    stat.device_count = device_count
                    stat.is_work_hour = is_work_hour
                    
                    if not existing:
                        self.local_db.add(stat)
        
        self.local_db.commit()
        print(f"组织小时数据汇总完成: {target_date}")
    
    def get_export_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        from app.local_models import LocalOrganization, LocalPurposeDict, LocalNetwork
        from app.models import Device
        from sqlalchemy import distinct, func as sql_func
        
        results = []
        
        try:
            logger.info(f"开始导出数据，日期范围: {start_date} 至 {end_date}")
            
            orgs = self.local_db.query(LocalOrganization).filter(
                LocalOrganization.deleted == 0
            ).all()
            
            purposes = self.local_db.query(LocalPurposeDict).filter(
                LocalPurposeDict.dict_type == "device_purpose",
                LocalPurposeDict.status == 1,
                LocalPurposeDict.deleted == 0
            ).order_by(LocalPurposeDict.dict_sort).all()
            
            purpose_dict = {p.dict_value: p.dict_label for p in purposes}
            
            networks = self.local_db.query(LocalNetwork).filter(
                LocalNetwork.deleted == 0
            ).all()
            network_names = [n.name for n in networks if n.name]
            
            devices = self.db.query(Device).filter(Device.deleted == 0).all()
            
            gpu_infos = {g.gpu_name: g for g in self.db.query(GpuCardInfo).filter(GpuCardInfo.deleted == 0).all()}
            
            org_devices = {}
            for device in devices:
                org_id = device.organization_id
                if org_id not in org_devices:
                    org_devices[org_id] = []
                org_devices[org_id].append(device)
            
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            for org in orgs:
                org_id = org.id
                org_name = org.name or ""
                
                org_device_list = org_devices.get(org_id, [])
                if not org_device_list:
                    continue
                
                device_ids = [d.id for d in org_device_list]
                
                all_summaries = self.local_db.query(LocalOrgGpuUsageSummary).filter(
                    LocalOrgGpuUsageSummary.organization_id3 == org_id,
                    LocalOrgGpuUsageSummary.summary_time >= start_datetime,
                    LocalOrgGpuUsageSummary.summary_time <= end_datetime
                ).order_by(LocalOrgGpuUsageSummary.summary_time).all()
                
                if not all_summaries:
                    continue
                
                summary_dates = [s.summary_time.date() if isinstance(s.summary_time, datetime) else s.summary_time for s in all_summaries]
                actual_start_date = min(summary_dates)
                actual_end_date = max(summary_dates)
                
                last_day_summary = None
                for summary in reversed(all_summaries):
                    summary_date = summary.summary_time.date() if isinstance(summary.summary_time, datetime) else summary.summary_time
                    if summary_date == actual_end_date:
                        last_day_summary = summary
                        break
                
                static_device_count = last_day_summary.device_count if last_day_summary else 0
                static_gpu_count = last_day_summary.gpu_count if last_day_summary else 0
                
                total_tflops = 0
                total_memory_gb = 0
                for device in org_device_list:
                    gpu_model = device.gpu_model or ""
                    gpu_count = device.gpu_count or 0
                    gpu_info = gpu_infos.get(gpu_model)
                    if gpu_info and gpu_info.tflops_fp16:
                        total_tflops += float(gpu_info.tflops_fp16) * gpu_count
                    if device.total_memory:
                        total_memory_gb += float(device.total_memory)
                
                purpose_network_combinations = []
                purpose_values = [None] + [p.dict_value for p in purposes]
                network_values = [None] + network_names
                time_types = ['all', 'work', 'nonwork']
                
                for purpose_val in purpose_values:
                    for network_val in network_values:
                        for time_type in time_types:
                            purpose_network_combinations.append((purpose_val, network_val, time_type))
                
                for purpose_val, network_val, time_type in purpose_network_combinations:
                    filtered_devices = org_device_list
                    if purpose_val is not None:
                        filtered_devices = [d for d in filtered_devices if d.purpose == purpose_val]
                    if network_val is not None:
                        filtered_devices = [d for d in filtered_devices if d.net_module_name == network_val]
                    
                    if not filtered_devices:
                        continue
                    
                    filtered_device_ids = [d.id for d in filtered_devices]
                    
                    summaries = all_summaries
                    
                    if not summaries:
                        continue
                    
                    gpu_usage_values = []
                    memory_usage_values = []
                    memory_utilization_values = []
                    
                    for summary in summaries:
                        if time_type == 'all':
                            gpu_usage = summary.avg_gpu_usage_rate
                        elif time_type == 'work':
                            gpu_usage = summary.avg_gpu_usage_rate_work
                        else:
                            gpu_usage = summary.avg_gpu_usage_rate_nonwork
                        
                        if gpu_usage is not None:
                            gpu_usage_values.append(float(gpu_usage))
                        if summary.avg_memory_usage_rate is not None:
                            memory_usage_values.append(float(summary.avg_memory_usage_rate))
                        if summary.avg_memory_utilization is not None:
                            memory_utilization_values.append(float(summary.avg_memory_utilization))
                    
                    avg_gpu_usage = round(sum(gpu_usage_values) / len(gpu_usage_values), 2) if gpu_usage_values else 0
                    avg_memory_usage = round(sum(memory_usage_values) / len(memory_usage_values), 2) if memory_usage_values else 0
                    avg_memory_utilization = round(sum(memory_utilization_values) / len(memory_utilization_values), 2) if memory_utilization_values else 0
                    
                    purpose_label = purpose_dict.get(purpose_val, "全部") if purpose_val is not None else "全部"
                    network_label = network_val if network_val is not None else "全部"
                    time_type_label = {'all': '全部', 'work': '工作时段', 'nonwork': '非工作时段'}.get(time_type, time_type)
                    
                    row = {
                        '起始日期': start_date.strftime('%Y-%m-%d'),
                        '结束日期': end_date.strftime('%Y-%m-%d'),
                        '实际起始日期': actual_start_date.strftime('%Y-%m-%d'),
                        '实际结束日期': actual_end_date.strftime('%Y-%m-%d'),
                        '组织机构名称': org_name,
                        '设备数': static_device_count,
                        'GPU数': static_gpu_count,
                        '总算力': round(total_tflops, 2),
                        '显存总量(GB)': round(total_memory_gb, 2),
                        '设备用途': purpose_label,
                        '运行网络': network_label,
                        '时间类型': time_type_label,
                        '平均GPU使用率(%)': avg_gpu_usage,
                        '平均显存使用率(%)': avg_memory_usage,
                        '平均显存利用率(%)': avg_memory_utilization
                    }
                    results.append(row)
            
            logger.info(f"导出数据完成，共 {len(results)} 条记录")
            return results
            
        except SQLAlchemyError as e:
            logger.error(f"数据库查询错误，日期范围: {start_date} 至 {end_date}, 错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"导出数据时发生未知错误，日期范围: {start_date} 至 {end_date}, 错误: {str(e)}")
            raise

    def run_all_aggregations(self, target_date: Optional[date] = None):
        print(f"开始执行数据聚合：{target_date or date.today() - timedelta(days=1)}")
        self.aggregate_daily_summary(target_date)
        self.aggregate_device_summary(target_date)
        self.aggregate_device_hourly_stats(target_date)
        self.aggregate_org_summary(target_date)
        self.aggregate_statistics_data(target_date)
        self.aggregate_org_hourly_stats(target_date)
        print("数据聚合完成")


def run_aggregation(days: int = 1):
    db = SessionLocal()
    local_db = LocalSessionLocal()
    try:
        aggregator = DataAggregator(db, local_db)
        
        for i in range(days):
            target_date = date.today() - timedelta(days=i+1)
            aggregator.run_all_aggregations(target_date)
    finally:
        db.close()
        local_db.close()


if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(f"聚合 {days} 天的数据...")
    run_aggregation(days)

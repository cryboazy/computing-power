from sqlalchemy import Column, BigInteger, Integer, String, Numeric, SmallInteger, DateTime, Text, Index
from datetime import datetime

from app.local_database import LocalBase


class LocalSystemConfig(LocalBase):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(String(500))
    description = Column(String(255))
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class LocalDailyGpuUsageSummary(LocalBase):
    __tablename__ = "daily_gpu_usage_summary"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    summary_date = Column(DateTime, nullable=False, unique=True)
    total_device_count = Column(Integer, default=0)
    total_gpu_count = Column(Integer, default=0)
    avg_gpu_usage_rate = Column(Numeric(5, 2), default=0.00)
    max_gpu_usage_rate = Column(Numeric(5, 2), default=0.00)
    min_gpu_usage_rate = Column(Numeric(5, 2), default=0.00)
    avg_memory_usage_rate = Column(Numeric(5, 2), default=0.00)
    max_memory_usage_rate = Column(Numeric(5, 2), default=0.00)
    min_memory_usage_rate = Column(Numeric(5, 2), default=0.00)
    avg_temperature = Column(Numeric(5, 2), default=0.00)
    max_temperature = Column(Numeric(5, 2), default=0.00)
    memory_total_gb = Column(Numeric(15, 2))
    compute_total_tflops = Column(Numeric(15, 2))
    total_sample_count = Column(BigInteger, default=0)
    total_gpu_rate_sum = Column(BigInteger, default=0)
    avg_gpu_usage_rate_work = Column(Numeric(5, 2), default=0.00)
    avg_gpu_usage_rate_nonwork = Column(Numeric(5, 2), default=0.00)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_daily_summary_date', 'summary_date'),
    )


class LocalDailyDeviceSummary(LocalBase):
    __tablename__ = "daily_device_summary"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(BigInteger, nullable=False)
    device_name = Column(String(255), default="")
    organization_id1 = Column(BigInteger)
    organization_name1 = Column(String(255), default="")
    organization_id2 = Column(BigInteger)
    organization_name2 = Column(String(255), default="")
    organization_id3 = Column(BigInteger)
    organization_name3 = Column(String(255), default="")
    province_code = Column(String(50), default="")
    province = Column(String(100), default="")
    avg_gpu_usage_rate = Column(Numeric(5, 2), default=0.00)
    avg_gpu_usage_rate_work = Column(Numeric(5, 2), default=0.00)
    avg_gpu_usage_rate_nonwork = Column(Numeric(5, 2), default=0.00)
    summary_date = Column(DateTime, nullable=False)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_device_summary_date', 'summary_date'),
        Index('idx_device_id_date', 'device_id', 'summary_date', unique=True),
        Index('idx_device_org_id3', 'organization_id3'),
    )


class LocalDeviceHourlyStats(LocalBase):
    __tablename__ = "device_hourly_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(BigInteger, nullable=False)
    device_name = Column(String(255), default="")
    organization_id3 = Column(BigInteger)
    organization_name3 = Column(String(255), default="")
    stat_date = Column(DateTime, nullable=False)
    stat_hour = Column(Integer, nullable=False)
    avg_gpu_usage_rate = Column(Numeric(5, 2), default=0.00)
    device_count = Column(Integer, default=0)
    is_work_hour = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_device_hourly_date_hour', 'stat_date', 'stat_hour'),
        Index('idx_device_id_date_hour', 'device_id', 'stat_date', 'stat_hour', unique=True),
    )


class LocalOrgGpuUsageSummary(LocalBase):
    __tablename__ = "org_gpu_usage_summary"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id1 = Column(BigInteger)
    organization_name1 = Column(String(200), default="")
    organization_id2 = Column(BigInteger)
    organization_name2 = Column(String(200), default="")
    organization_id3 = Column(BigInteger, nullable=False)
    organization_name3 = Column(String(200), nullable=False)
    organization_code3 = Column(String(100), default="")
    province_code = Column(String(20), default="")
    province = Column(String(50), default="")
    device_count = Column(Integer, default=0)
    gpu_count = Column(Integer, default=0)
    avg_gpu_usage_rate = Column(Numeric(5, 2), default=0.00)
    avg_memory_usage_rate = Column(Numeric(5, 2), default=0.00)
    max_gpu_usage_rate = Column(Numeric(5, 2), default=0.00)
    min_gpu_usage_rate = Column(Numeric(5, 2), default=0.00)
    latest_collection_time = Column(DateTime)
    summary_time = Column(DateTime, nullable=False)
    avg_gpu_usage_rate_work = Column(Numeric(5, 2), default=0.00)
    avg_gpu_usage_rate_nonwork = Column(Numeric(5, 2), default=0.00)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_org_summary_time', 'summary_time'),
        Index('idx_org_name3', 'organization_name3'),
        Index('idx_org_name3_time', 'organization_name3', 'summary_time'),
        Index('idx_org_id3_time', 'organization_id3', 'summary_time'),
    )


class LocalStatisticsData(LocalBase):
    __tablename__ = "statistics_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_time = Column(DateTime, nullable=False)
    stat_date = Column(DateTime, nullable=False)
    stat_hour = Column(SmallInteger, nullable=False)
    stat_minute = Column(SmallInteger)
    stat_type = Column(String(20), default='ALL')
    device_id = Column(BigInteger)
    device_code = Column(String(30))
    device_total = Column(Integer, default=0)
    memory_total_gb = Column(Numeric(15, 2), default=0.00)
    memory_used_gb = Column(Numeric(15, 2), default=0.00)
    memory_free_gb = Column(Numeric(15, 2), default=0.00)
    memory_usage_rate = Column(Numeric(5, 2), default=0.00)
    compute_total_tflops = Column(Numeric(15, 2), default=0.00)
    compute_used_tflops = Column(Numeric(15, 2), default=0.00)
    compute_free_tflops = Column(Numeric(15, 2), default=0.00)
    avg_gpu_utilization = Column(Numeric(5, 2), default=0.00)
    avg_temperature = Column(Numeric(5, 2))
    virtual_percent = Column(Numeric(5, 2))
    cpu_percent = Column(Numeric(5, 2))
    overall_usage_rate = Column(Numeric(5, 2), default=0.00)
    gpu_total_count = Column(Integer, default=0)
    task_running_count = Column(Integer, default=0)
    task_pending_count = Column(Integer, default=0)
    task_completed_count = Column(Integer, default=0)
    is_work_hour = Column(SmallInteger, default=1)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_stat_type_work', 'stat_type', 'is_work_hour'),
        Index('idx_stat_time', 'stat_time'),
        Index('idx_stat_type_time', 'stat_type', 'stat_time'),
    )


class LocalOrgHourlyStats(LocalBase):
    __tablename__ = "org_hourly_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id3 = Column(BigInteger, nullable=False)
    organization_name3 = Column(String(200), nullable=False)
    stat_date = Column(DateTime, nullable=False)
    stat_hour = Column(SmallInteger, nullable=False)
    avg_gpu_usage_rate = Column(Numeric(5, 2), default=0.00)
    device_count = Column(Integer, default=0)
    is_work_hour = Column(SmallInteger, default=1)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_org_hourly_org_date', 'organization_id3', 'stat_date'),
        Index('idx_org_hourly_org_date_hour', 'organization_id3', 'stat_date', 'stat_hour', unique=True),
    )


class LocalOrganization(LocalBase):
    __tablename__ = "cached_organization"
    
    id = Column(BigInteger, primary_key=True)
    parent_id = Column(BigInteger, default=0)
    name = Column(String(100), nullable=False)
    code = Column(String(50), default="")
    type = Column(SmallInteger, default=1)
    sort = Column(Integer, default=0)
    leader = Column(String(50), default="")
    phone = Column(String(20), default="")
    email = Column(String(100), default="")
    address = Column(String(255), default="")
    status = Column(SmallInteger, default=1)
    remark = Column(String(500), default="")
    province_code = Column(String(30), default="")
    province = Column(String(30), default="")
    deleted = Column(SmallInteger, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_cached_org_id', 'id'),
        Index('idx_cached_org_parent', 'parent_id'),
        Index('idx_cached_org_province', 'province'),
    )


class LocalDevice(LocalBase):
    __tablename__ = "cached_device"
    
    id = Column(BigInteger, primary_key=True)
    name = Column(String(100), default="")
    code = Column(String(50), nullable=False)
    organization_id = Column(BigInteger)
    organization_code = Column(String(50), default="")
    cpu_cores = Column(Integer, default=0)
    memory_size = Column(Numeric(10, 2), default=0)
    disk_size = Column(Numeric(10, 2), default=0)
    gpu_count = Column(Integer, default=0)
    gpu_model = Column(String(300), default="")
    total_memory = Column(Numeric(10, 2), default=0)
    operating_system = Column(String(100), default="")
    purpose = Column(SmallInteger, default=0)
    net_module_code = Column(String(50), default="")
    net_module_name = Column(String(50), default="")
    detail_info = Column(Text)
    deleted = Column(SmallInteger, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_cached_device_id', 'id'),
        Index('idx_cached_device_org', 'organization_id'),
        Index('idx_cached_device_net', 'net_module_code'),
        Index('idx_cached_device_gpu_model', 'gpu_model'),
    )


class LocalGpuCardInfo(LocalBase):
    __tablename__ = "cached_gpu_card_info"
    
    id = Column(BigInteger, primary_key=True)
    gpu_index = Column(Integer, nullable=False)
    gpu_name = Column(String(100), nullable=False)
    card_type = Column(Integer, default=0)
    cuda_cores = Column(Integer, default=0)
    base_clock_mhz = Column(Integer, default=0)
    boost_clock_mhz = Column(Integer, default=0)
    memory_total_mb = Column(Integer, default=0)
    memory_total_gb = Column(Numeric(10, 2), default=0)
    pcie_gen = Column(Integer, default=0)
    pcie_width = Column(Integer, default=0)
    tflops_fp32 = Column(Numeric(10, 2), default=0)
    tflops_fp16 = Column(Numeric(10, 2), default=0)
    tflops_fp64 = Column(Numeric(10, 2), default=0)
    tflops_int8 = Column(Numeric(10, 2), default=0)
    tdp_watts = Column(Integer, default=0)
    max_power_watts = Column(Integer, default=0)
    memory_type = Column(String(50), default="")
    memory_bus_width = Column(Integer, default=0)
    memory_bandwidth_gbps = Column(Numeric(10, 2), default=0)
    architecture = Column(String(50), default="")
    compute_capability = Column(String(20), default="")
    status = Column(SmallInteger, default=1)
    remark = Column(String(500), default="")
    deleted = Column(SmallInteger, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_cached_gpu_id', 'id'),
        Index('idx_cached_gpu_name', 'gpu_name'),
    )


class LocalNetwork(LocalBase):
    __tablename__ = "cached_network"
    
    id = Column(BigInteger, primary_key=True)
    code = Column(String(100), default="")
    parent_code = Column(String(100), default="")
    name = Column(String(100), default="")
    deleted = Column(SmallInteger, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_cached_network_id', 'id'),
        Index('idx_cached_network_code', 'code'),
    )


class LocalDeviceDistribution(LocalBase):
    __tablename__ = "device_distribution_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_type = Column(String(50), nullable=False)
    cache_key = Column(String(200), nullable=False)
    cache_data = Column(Text, nullable=False)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_device_dist_type_key', 'cache_type', 'cache_key', unique=True),
    )


class LocalCacheMetadata(LocalBase):
    __tablename__ = "cache_metadata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_name = Column(String(100), unique=True, nullable=False)
    last_sync_time = Column(DateTime)
    sync_interval_seconds = Column(Integer, default=3600)
    record_count = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    error_message = Column(Text)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class LocalPurposeDict(LocalBase):
    __tablename__ = "cached_purpose_dict"
    
    id = Column(BigInteger, primary_key=True)
    dict_type = Column(String(100), nullable=False)
    dict_label = Column(String(100), nullable=False)
    dict_value = Column(SmallInteger, nullable=False)
    dict_sort = Column(Integer, default=0)
    status = Column(SmallInteger, default=1)
    remark = Column(String(500), default="")
    deleted = Column(SmallInteger, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_cached_purpose_type', 'dict_type'),
        Index('idx_cached_purpose_value', 'dict_value'),
    )

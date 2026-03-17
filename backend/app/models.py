from sqlalchemy import Column, BigInteger, Integer, String, Numeric, SmallInteger, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Organization(Base):
    __tablename__ = "organization"
    
    id = Column(BigInteger, primary_key=True, index=True)
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
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now())
    create_by = Column(String(50), default="")
    update_by = Column(String(50), default="")
    deleted = Column(SmallInteger, default=0)
    version = Column(Integer, default=0)
    province_code = Column(String(30), default="")
    province = Column(String(30), default="")


class Device(Base):
    __tablename__ = "device"
    
    id = Column(BigInteger, primary_key=True, index=True)
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
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now())
    create_by = Column(String(50), default="")
    update_by = Column(String(50), default="")
    deleted = Column(SmallInteger, default=0)
    version = Column(Integer, default=0)
    online_status = Column(Integer, default=0)


class GpuCardInfo(Base):
    __tablename__ = "gpu_card_info"
    
    id = Column(BigInteger, primary_key=True, index=True)
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
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now())
    create_by = Column(String(50), default="")
    update_by = Column(String(50), default="")
    deleted = Column(SmallInteger, default=0)
    version = Column(Integer, default=0)


class DeviceGpuMonitor(Base):
    __tablename__ = "device_gpu_monitor"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False)
    msg_id = Column(String(64), default="")
    organization_id1 = Column(BigInteger)
    organization_name1 = Column(String(100), default="")
    organization_id2 = Column(BigInteger)
    organization_name2 = Column(String(100), default="")
    organization_id3 = Column(BigInteger)
    organization_name3 = Column(String(100), default="")
    gpu_count = Column(Integer, default=0)
    total_memory_mb = Column(Integer, default=0)
    used_memory_mb = Column(Integer, default=0)
    free_memory_mb = Column(Integer, default=0)
    memory_usage_percent = Column(Numeric(5, 2), default=0)
    avg_gpu_utilization = Column(Numeric(5, 2), default=0)
    avg_memory_utilization = Column(Numeric(5, 2), default=0)
    max_gpu_utilization = Column(Integer, default=0)
    min_gpu_utilization = Column(Integer, default=0)
    avg_temperature = Column(Numeric(5, 2), default=0)
    max_temperature = Column(Integer, default=0)
    total_power_draw = Column(Numeric(10, 2), default=0)
    total_power_limit = Column(Numeric(10, 2), default=0)
    power_usage_percent = Column(Numeric(5, 2), default=0)
    collection_timestamp = Column(DateTime, nullable=False)
    create_time = Column(DateTime, server_default=func.now())


class DeviceGpuMonitorDetail(Base):
    __tablename__ = "device_gpu_monitor_detail"
    
    id = Column(BigInteger, primary_key=True, index=True)
    device_gpu_monitor_id = Column(BigInteger, nullable=False)
    gpu_idx = Column(Integer, nullable=False)
    gpu_name = Column(String(100), default="")
    total_mb = Column(Numeric(10, 2), default=0)
    used_mb = Column(Numeric(10, 2), default=0)
    free_mb = Column(Numeric(10, 2), default=0)
    usage_percent = Column(Numeric(5, 2), default=0)
    gpu_utilization_percent = Column(Numeric(5, 2), default=0)
    memory_utilization_percent = Column(Numeric(5, 2), default=0)
    current_gpu_clock_mhz = Column(Integer, default=0)
    current_memory_clock_mhz = Column(Integer, default=0)
    temperature_celsius = Column(Numeric(5, 2), default=0)
    power_draw_watts = Column(Numeric(10, 2), default=0)
    power_limit_watts = Column(Numeric(10, 2), default=0)
    power_usage_percent = Column(Numeric(5, 2), default=0)
    collection_timestamp = Column(DateTime, nullable=False)
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now())


class Network(Base):
    __tablename__ = "network"
    
    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(String(100), default="")
    parent_code = Column(String(100), default="")
    name = Column(String(100), default="")
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now())
    create_by = Column(String(50), default="")
    update_by = Column(String(50), default="")
    deleted = Column(Integer, default=0)


class SysDictData(Base):
    __tablename__ = "sys_dict_data"
    
    id = Column(BigInteger, primary_key=True, index=True)
    dict_type = Column(String(100), nullable=False)
    dict_label = Column(String(100), nullable=False)
    dict_value = Column(Integer, nullable=False)
    dict_sort = Column(Integer, default=0)
    status = Column(SmallInteger, default=1)
    remark = Column(String(500), default="")
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now())
    create_by = Column(String(50), default="")
    update_by = Column(String(50), default="")
    deleted = Column(SmallInteger, default=0)

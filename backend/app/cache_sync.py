import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.database import SessionLocal
from app.local_database import LocalSessionLocal
from app.models import Device, Organization, GpuCardInfo, Network, SysDictData
from app.local_models import (
    LocalOrganization, LocalDevice, LocalGpuCardInfo, LocalNetwork,
    LocalDeviceDistribution, LocalCacheMetadata, LocalPurposeDict
)


class CacheSyncService:
    SYNC_INTERVALS = {
        'organization': 3600,
        'device': 1800,
        'gpu_card_info': 86400,
        'network': 86400,
        'distribution_stats': 600,
        'purpose_dict': 3600,
    }
    
    PURPOSE_DICT_TYPE = 'device_purpose'
    
    def __init__(self, db: Session, local_db: Session):
        self.db = db
        self.local_db = local_db
    
    def _get_or_create_metadata(self, cache_name: str) -> LocalCacheMetadata:
        metadata = self.local_db.query(LocalCacheMetadata).filter(
            LocalCacheMetadata.cache_name == cache_name
        ).first()
        
        if not metadata:
            metadata = LocalCacheMetadata(
                cache_name=cache_name,
                sync_interval_seconds=self.SYNC_INTERVALS.get(cache_name, 3600),
                status="pending"
            )
            self.local_db.add(metadata)
            self.local_db.commit()
        
        return metadata
    
    def _should_sync(self, cache_name: str) -> bool:
        metadata = self._get_or_create_metadata(cache_name)
        
        if metadata.status == "error":
            return True
        
        if not metadata.last_sync_time:
            return True
        
        interval = metadata.sync_interval_seconds
        elapsed = (datetime.now() - metadata.last_sync_time).total_seconds()
        
        return elapsed >= interval
    
    def _update_metadata(self, cache_name: str, status: str, record_count: int = 0, error_message: str = None):
        metadata = self._get_or_create_metadata(cache_name)
        metadata.last_sync_time = datetime.now()
        metadata.status = status
        metadata.record_count = record_count
        metadata.error_message = error_message
        self.local_db.commit()
    
    def sync_organizations(self, force: bool = False) -> int:
        if not force and not self._should_sync('organization'):
            return 0
        
        try:
            remote_orgs = self.db.query(Organization).filter(
                Organization.deleted == 0
            ).all()
            
            self.local_db.query(LocalOrganization).delete()
            
            for org in remote_orgs:
                local_org = LocalOrganization(
                    id=org.id,
                    parent_id=org.parent_id,
                    name=org.name,
                    code=org.code,
                    type=org.type,
                    sort=org.sort,
                    leader=org.leader,
                    phone=org.phone,
                    email=org.email,
                    address=org.address,
                    status=org.status,
                    remark=org.remark,
                    province_code=org.province_code,
                    province=org.province,
                    deleted=org.deleted
                )
                self.local_db.add(local_org)
            
            self.local_db.commit()
            self._update_metadata('organization', 'success', len(remote_orgs))
            return len(remote_orgs)
        except Exception as e:
            self.local_db.rollback()
            self._update_metadata('organization', 'error', 0, str(e))
            raise
    
    def sync_devices(self, force: bool = False) -> int:
        if not force and not self._should_sync('device'):
            return 0
        
        try:
            remote_devices = self.db.query(Device).filter(
                Device.deleted == 0
            ).all()
            
            self.local_db.query(LocalDevice).delete()
            
            for device in remote_devices:
                local_device = LocalDevice(
                    id=device.id,
                    name=device.name,
                    code=device.code,
                    organization_id=device.organization_id,
                    organization_code=device.organization_code,
                    cpu_cores=device.cpu_cores,
                    memory_size=device.memory_size,
                    disk_size=device.disk_size,
                    gpu_count=device.gpu_count,
                    gpu_model=device.gpu_model,
                    total_memory=device.total_memory,
                    operating_system=device.operating_system,
                    purpose=device.purpose,
                    net_module_code=device.net_module_code,
                    net_module_name=device.net_module_name,
                    detail_info=device.detail_info,
                    deleted=device.deleted
                )
                self.local_db.add(local_device)
            
            self.local_db.commit()
            self._update_metadata('device', 'success', len(remote_devices))
            return len(remote_devices)
        except Exception as e:
            self.local_db.rollback()
            self._update_metadata('device', 'error', 0, str(e))
            raise
    
    def sync_gpu_card_info(self, force: bool = False) -> int:
        if not force and not self._should_sync('gpu_card_info'):
            return 0
        
        try:
            remote_gpus = self.db.query(GpuCardInfo).filter(
                GpuCardInfo.deleted == 0
            ).all()
            
            self.local_db.query(LocalGpuCardInfo).delete()
            
            for gpu in remote_gpus:
                local_gpu = LocalGpuCardInfo(
                    id=gpu.id,
                    gpu_index=gpu.gpu_index,
                    gpu_name=gpu.gpu_name,
                    card_type=gpu.card_type,
                    cuda_cores=gpu.cuda_cores,
                    base_clock_mhz=gpu.base_clock_mhz,
                    boost_clock_mhz=gpu.boost_clock_mhz,
                    memory_total_mb=gpu.memory_total_mb,
                    memory_total_gb=gpu.memory_total_gb,
                    pcie_gen=gpu.pcie_gen,
                    pcie_width=gpu.pcie_width,
                    tflops_fp32=gpu.tflops_fp32,
                    tflops_fp16=gpu.tflops_fp16,
                    tflops_fp64=gpu.tflops_fp64,
                    tflops_int8=gpu.tflops_int8,
                    tdp_watts=gpu.tdp_watts,
                    max_power_watts=gpu.max_power_watts,
                    memory_type=gpu.memory_type,
                    memory_bus_width=gpu.memory_bus_width,
                    memory_bandwidth_gbps=gpu.memory_bandwidth_gbps,
                    architecture=gpu.architecture,
                    compute_capability=gpu.compute_capability,
                    status=gpu.status,
                    remark=gpu.remark,
                    deleted=gpu.deleted
                )
                self.local_db.add(local_gpu)
            
            self.local_db.commit()
            self._update_metadata('gpu_card_info', 'success', len(remote_gpus))
            return len(remote_gpus)
        except Exception as e:
            self.local_db.rollback()
            self._update_metadata('gpu_card_info', 'error', 0, str(e))
            raise
    
    def sync_networks(self, force: bool = False) -> int:
        if not force and not self._should_sync('network'):
            return 0
        
        try:
            remote_networks = self.db.query(Network).filter(
                Network.deleted == 0
            ).all()
            
            self.local_db.query(LocalNetwork).delete()
            
            for net in remote_networks:
                local_net = LocalNetwork(
                    id=net.id,
                    code=net.code,
                    parent_code=net.parent_code,
                    name=net.name,
                    deleted=net.deleted
                )
                self.local_db.add(local_net)
            
            self.local_db.commit()
            self._update_metadata('network', 'success', len(remote_networks))
            return len(remote_networks)
        except Exception as e:
            self.local_db.rollback()
            self._update_metadata('network', 'error', 0, str(e))
            raise
    
    def sync_purpose_dict(self, force: bool = False) -> int:
        if not force and not self._should_sync('purpose_dict'):
            return 0
        
        try:
            # 检查本地数据库是否已有字典数据
            existing_dicts = self.local_db.query(LocalPurposeDict).filter(
                LocalPurposeDict.dict_type == self.PURPOSE_DICT_TYPE,
                LocalPurposeDict.deleted == 0,
                LocalPurposeDict.status == 1
            ).count()
            
            # 如果本地数据库没有字典数据，初始化默认数据
            if existing_dicts == 0:
                default_dicts = [
                    {'id': 1, 'dict_label': '训练', 'dict_value': 1, 'dict_sort': 1},
                    {'id': 2, 'dict_label': '研发', 'dict_value': 2, 'dict_sort': 2},
                    {'id': 3, 'dict_label': '推理', 'dict_value': 3, 'dict_sort': 3}
                ]
                
                for d in default_dicts:
                    local_dict = LocalPurposeDict(
                        id=d['id'],
                        dict_type=self.PURPOSE_DICT_TYPE,
                        dict_label=d['dict_label'],
                        dict_value=d['dict_value'],
                        dict_sort=d['dict_sort'],
                        status=1,
                        remark=f'GPU设备用途-{d["dict_label"]}',
                        deleted=0
                    )
                    self.local_db.add(local_dict)
                
                self.local_db.commit()
                self._update_metadata('purpose_dict', 'success', len(default_dicts))
                return len(default_dicts)
            else:
                # 本地已有数据，直接更新元数据
                self._update_metadata('purpose_dict', 'success', existing_dicts)
                return existing_dicts
        except Exception as e:
            self.local_db.rollback()
            self._update_metadata('purpose_dict', 'error', 0, str(e))
            raise
    
    def get_purpose_map(self) -> Dict[int, str]:
        purpose_dicts = self.local_db.query(LocalPurposeDict).filter(
            LocalPurposeDict.dict_type == self.PURPOSE_DICT_TYPE,
            LocalPurposeDict.deleted == 0,
            LocalPurposeDict.status == 1
        ).all()
        
        if not purpose_dicts:
            return {1: "训练", 2: "研发", 3: "推理"}
        
        return {d.dict_value: d.dict_label for d in purpose_dicts}
    
    def sync_all_static_data(self, force: bool = False) -> Dict[str, int]:
        results = {}
        
        try:
            results['gpu_card_info'] = self.sync_gpu_card_info(force)
        except Exception as e:
            print(f"GPU卡信息同步失败: {e}")
            results['gpu_card_info'] = -1
        
        try:
            results['network'] = self.sync_networks(force)
        except Exception as e:
            print(f"网络信息同步失败: {e}")
            results['network'] = -1
        
        try:
            results['purpose_dict'] = self.sync_purpose_dict(force)
        except Exception as e:
            print(f"用途字典同步失败: {e}")
            results['purpose_dict'] = -1
        
        try:
            results['organization'] = self.sync_organizations(force)
        except Exception as e:
            print(f"组织信息同步失败: {e}")
            results['organization'] = -1
        
        try:
            results['device'] = self.sync_devices(force)
        except Exception as e:
            print(f"设备信息同步失败: {e}")
            results['device'] = -1
        
        return results
    
    def get_cached_organizations(self) -> List[LocalOrganization]:
        return self.local_db.query(LocalOrganization).filter(
            LocalOrganization.deleted == 0
        ).all()
    
    def get_cached_devices(self) -> List[LocalDevice]:
        return self.local_db.query(LocalDevice).filter(
            LocalDevice.deleted == 0
        ).all()
    
    def get_cached_gpu_infos(self) -> Dict[str, LocalGpuCardInfo]:
        gpus = self.local_db.query(LocalGpuCardInfo).filter(
            LocalGpuCardInfo.deleted == 0
        ).all()
        return {g.gpu_name: g for g in gpus}
    
    def get_cached_networks(self) -> Dict[str, LocalNetwork]:
        networks = self.local_db.query(LocalNetwork).filter(
            LocalNetwork.deleted == 0
        ).all()
        return {n.code: n for n in networks}
    
    def get_cache_status(self) -> List[Dict[str, Any]]:
        metadatas = self.local_db.query(LocalCacheMetadata).all()
        
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


def run_cache_sync():
    db = SessionLocal()
    local_db = LocalSessionLocal()
    try:
        service = CacheSyncService(db, local_db)
        results = service.sync_all_static_data(force=True)
        print(f"缓存同步完成: {results}")
        return results
    finally:
        db.close()
        local_db.close()


if __name__ == "__main__":
    run_cache_sync()

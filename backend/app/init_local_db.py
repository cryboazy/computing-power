import os
import sys
from sqlalchemy import text
from app.local_database import local_engine, LocalSessionLocal, LocalBase, upgrade_local_db_schema
from app.local_models import (
    LocalSystemConfig, LocalDailyGpuUsageSummary, LocalDailyDeviceSummary,
    LocalDeviceHourlyStats, LocalOrgGpuUsageSummary, LocalStatisticsData,
    LocalOrgHourlyStats, LocalOrganization, LocalDevice, LocalGpuCardInfo,
    LocalNetwork, LocalDeviceDistribution, LocalCacheMetadata, LocalPurposeDict,
    LocalGpuTierDict, LocalAggregationTask
)


def init_local_tables():
    LocalBase.metadata.create_all(bind=local_engine)
    print("本地数据库表创建完成")


def init_local_system_config(db):
    configs = [
        {"key": "work_hour_start", "value": "9", "description": "工作时段开始时间（小时）"},
        {"key": "work_hour_end", "value": "18", "description": "工作时段结束时间（小时）"},
        {"key": "high_usage_threshold", "value": "60", "description": "高使用率阈值（%）"},
        {"key": "low_usage_threshold", "value": "30", "description": "低使用率阈值（%）"},
    ]
    
    for cfg in configs:
        existing = db.query(LocalSystemConfig).filter(LocalSystemConfig.config_key == cfg["key"]).first()
        if not existing:
            config = LocalSystemConfig(
                config_key=cfg["key"],
                config_value=cfg["value"],
                description=cfg["description"]
            )
            db.add(config)
    
    db.commit()
    print("本地系统配置初始化完成")


def init_local_purpose_dict(db):
    purpose_dicts = [
        {"id": 1, "dict_label": "训练", "dict_value": 1, "dict_sort": 1},
        {"id": 2, "dict_label": "研发", "dict_value": 2, "dict_sort": 2},
        {"id": 3, "dict_label": "推理", "dict_value": 3, "dict_sort": 3}
    ]
    
    for d in purpose_dicts:
        existing = db.query(LocalPurposeDict).filter(
            LocalPurposeDict.dict_type == 'device_purpose',
            LocalPurposeDict.dict_value == d["dict_value"]
        ).first()
        if not existing:
            purpose_dict = LocalPurposeDict(
                id=d["id"],
                dict_type='device_purpose',
                dict_label=d["dict_label"],
                dict_value=d["dict_value"],
                dict_sort=d["dict_sort"],
                status=1,
                remark=f'GPU设备用途-{d["dict_label"]}',
                deleted=0
            )
            db.add(purpose_dict)
    
    db.commit()
    print("本地设备用途字典初始化完成")


def init_local_gpu_tier_dict(db):
    tier_dicts = [
        {"id": 1, "dict_label": "高端卡", "dict_value": 1, "dict_sort": 1},
        {"id": 2, "dict_label": "中端卡", "dict_value": 2, "dict_sort": 2},
        {"id": 3, "dict_label": "低端卡", "dict_value": 3, "dict_sort": 3}
    ]

    for d in tier_dicts:
        existing = db.query(LocalGpuTierDict).filter(
            LocalGpuTierDict.dict_type == 'gpu_tier',
            LocalGpuTierDict.dict_value == d["dict_value"]
        ).first()
        if not existing:
            tier_dict = LocalGpuTierDict(
                id=d["id"],
                dict_type='gpu_tier',
                dict_label=d["dict_label"],
                dict_value=d["dict_value"],
                dict_sort=d["dict_sort"],
                status=1,
                remark=f'GPU档次-{d["dict_label"]}',
                deleted=0
            )
            db.add(tier_dict)

    db.commit()
    print("本地GPU档次字典初始化完成")


def get_table_stats(db):
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    tables = [
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
        ("cached_purpose_dict", "用途字典"),
        ("cached_gpu_tier_dict", "GPU档次字典"),
        ("aggregation_task", "聚合任务")
    ]
    
    print("\n数据表统计:")
    print("-" * 50)
    for table_name, display_name in tables:
        try:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            print(f"  {display_name}: {count} 条")
        except Exception as e:
            print(f"  {display_name}: 查询失败 ({e})")
    print("-" * 50)


def init_local_database(upgrade=False):
    print("=" * 50)
    print("开始初始化本地数据库...")
    print("=" * 50)
    
    init_local_tables()
    
    if upgrade:
        print("\n检查数据库结构...")
        upgrade_local_db_schema()
    
    db = LocalSessionLocal()
    try:
        init_local_system_config(db)
        init_local_purpose_dict(db)
        init_local_gpu_tier_dict(db)

        print("\n本地数据库初始化完成！")
        get_table_stats(db)
    finally:
        db.close()
    
    print("=" * 50)


if __name__ == "__main__":
    upgrade = "--upgrade" in sys.argv or "-u" in sys.argv
    if upgrade:
        print("执行数据库升级模式...")
    init_local_database(upgrade=upgrade)

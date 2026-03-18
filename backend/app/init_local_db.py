from app.local_database import local_engine, LocalSessionLocal
from app.local_models import (
    LocalBase, LocalSystemConfig, LocalDailyGpuUsageSummary,
    LocalDailyDeviceSummary, LocalOrgGpuUsageSummary, LocalStatisticsData,
    LocalPurposeDict
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


def init_local_database():
    init_local_tables()
    
    db = LocalSessionLocal()
    try:
        init_local_system_config(db)
        init_local_purpose_dict(db)
        print("本地数据库初始化完成！")
    finally:
        db.close()


if __name__ == "__main__":
    init_local_database()

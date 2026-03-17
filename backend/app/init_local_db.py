from app.local_database import local_engine, LocalSessionLocal
from app.local_models import (
    LocalBase, LocalSystemConfig, LocalDailyGpuUsageSummary,
    LocalDailyDeviceSummary, LocalOrgGpuUsageSummary, LocalStatisticsData
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


def init_local_database():
    init_local_tables()
    
    db = LocalSessionLocal()
    try:
        init_local_system_config(db)
        print("本地数据库初始化完成！")
    finally:
        db.close()


if __name__ == "__main__":
    init_local_database()

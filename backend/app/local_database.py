import os
from sqlalchemy import create_engine, text, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

LOCAL_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "local.db")

os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)

LOCAL_DATABASE_URL = f"sqlite:///{LOCAL_DB_PATH}"


def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=268435456")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


local_engine = create_engine(
    LOCAL_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600
)

event.listen(local_engine, "connect", _set_sqlite_pragma)

LocalSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=local_engine)

LocalBase = declarative_base()


def migrate_add_columns():
    with local_engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE daily_gpu_usage_summary ADD COLUMN avg_gpu_usage_rate_work NUMERIC(5, 2) DEFAULT 0.00"))
        except Exception:
            pass
        
        try:
            conn.execute(text("ALTER TABLE daily_gpu_usage_summary ADD COLUMN avg_gpu_usage_rate_nonwork NUMERIC(5, 2) DEFAULT 0.00"))
        except Exception:
            pass
        
        try:
            conn.execute(text("ALTER TABLE org_gpu_usage_summary ADD COLUMN avg_gpu_usage_rate_work NUMERIC(5, 2) DEFAULT 0.00"))
        except Exception:
            pass
        
        try:
            conn.execute(text("ALTER TABLE org_gpu_usage_summary ADD COLUMN avg_gpu_usage_rate_nonwork NUMERIC(5, 2) DEFAULT 0.00"))
        except Exception:
            pass
        
        try:
            conn.execute(text("ALTER TABLE statistics_data ADD COLUMN is_work_hour SMALLINT DEFAULT 1"))
        except Exception:
            pass
        
        conn.commit()


def init_local_db():
    import hashlib
    from app.local_models import (
        LocalSystemConfig, LocalDailyGpuUsageSummary, LocalDailyDeviceSummary,
        LocalOrgGpuUsageSummary, LocalStatisticsData, LocalOrgHourlyStats,
        LocalOrganization, LocalDevice, LocalGpuCardInfo, LocalNetwork,
        LocalDeviceDistribution, LocalCacheMetadata, LocalPurposeDict
    )
    LocalBase.metadata.create_all(bind=local_engine)
    migrate_add_columns()
    print("本地数据库表创建完成")
    
    db = LocalSessionLocal()
    try:
        configs = [
            {"key": "work_hour_start", "value": "9", "description": "工作时段开始时间（小时）"},
            {"key": "work_hour_end", "value": "18", "description": "工作时段结束时间（小时）"},
            {"key": "high_usage_threshold", "value": "60", "description": "高使用率阈值（%）"},
            {"key": "low_usage_threshold", "value": "30", "description": "低使用率阈值（%）"},
            {"key": "admin_password", "value": hashlib.sha256("admin123".encode()).hexdigest(), "description": "管理员密码(SHA256加密)"},
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
        
        # 初始化设备用途字典数据
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
        print("系统配置和设备用途字典初始化完成")
    finally:
        db.close()


def get_local_db():
    db = LocalSessionLocal()
    try:
        yield db
    finally:
        db.close()

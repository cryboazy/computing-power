import os
import sys
from sqlalchemy import create_engine, event, text, inspect
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


def upgrade_local_db_schema():
    from app.local_models import (
        LocalSystemConfig, LocalDailyGpuUsageSummary, LocalDailyDeviceSummary,
        LocalDeviceHourlyStats, LocalOrgGpuUsageSummary, LocalStatisticsData,
        LocalOrgHourlyStats, LocalOrganization, LocalDevice, LocalGpuCardInfo,
        LocalNetwork, LocalDeviceDistribution, LocalCacheMetadata, LocalPurposeDict,
        LocalAggregationTask
    )
    
    db = LocalSessionLocal()
    try:
        inspector = inspect(db.bind)
        existing_tables = inspector.get_table_names()
        
        all_models = [
            LocalSystemConfig, LocalDailyGpuUsageSummary, LocalDailyDeviceSummary,
            LocalDeviceHourlyStats, LocalOrgGpuUsageSummary, LocalStatisticsData,
            LocalOrgHourlyStats, LocalOrganization, LocalDevice, LocalGpuCardInfo,
            LocalNetwork, LocalDeviceDistribution, LocalCacheMetadata, LocalPurposeDict,
            LocalAggregationTask
        ]
        
        changes_made = False
        
        for model in all_models:
            table_name = model.__tablename__
            
            if table_name not in existing_tables:
                continue
            
            existing_columns = {col["name"]: col for col in inspector.get_columns(table_name)}
            model_columns = {}
            
            for col_name, col_obj in model.__table__.columns.items():
                if hasattr(col_obj, 'default') and col_obj.default is not None:
                    default_val = str(col_obj.default.arg) if hasattr(col_obj.default, 'arg') else 'NULL'
                else:
                    default_val = 'NULL'
                
                col_type = str(col_obj.type)
                if 'NUMERIC' in col_type.upper():
                    col_type = col_type.replace('NUMERIC', 'DECIMAL')
                
                model_columns[col_name] = {
                    'type': col_type,
                    'nullable': col_obj.nullable,
                    'default': default_val
                }
            
            for col_name, col_info in model_columns.items():
                if col_name not in existing_columns:
                    try:
                        alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_info['type']}"
                        if not col_info['nullable']:
                            alter_stmt += f" DEFAULT {col_info['default']}"
                        db.execute(text(alter_stmt))
                        print(f"  已添加列 {table_name}.{col_name} ({col_info['type']})")
                        changes_made = True
                    except Exception as e:
                        print(f"  添加列 {table_name}.{col_name} 失败: {e}")
        
        if changes_made:
            db.commit()
            print("  数据库结构升级完成")
        else:
            print("  数据库结构已是最新，无需升级")
        
    finally:
        db.close()


def init_local_db(upgrade=False):
    import hashlib
    from app.local_models import (
        LocalSystemConfig, LocalDailyGpuUsageSummary, LocalDailyDeviceSummary,
        LocalOrgGpuUsageSummary, LocalStatisticsData, LocalOrgHourlyStats,
        LocalOrganization, LocalDevice, LocalGpuCardInfo, LocalNetwork,
        LocalDeviceDistribution, LocalCacheMetadata, LocalPurposeDict,
        LocalAggregationTask
    )
    LocalBase.metadata.create_all(bind=local_engine)
    print("本地数据库表创建完成")
    
    if upgrade:
        print("检查数据库结构...")
        upgrade_local_db_schema()
    
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

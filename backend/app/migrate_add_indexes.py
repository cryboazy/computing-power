"""
数据库索引迁移脚本
用于在现有数据库上添加索引以优化查询性能
"""
from sqlalchemy import text
from app.local_database import local_engine, LocalSessionLocal


def add_indexes():
    """添加索引到本地数据库表"""
    
    indexes_to_create = [
        # daily_gpu_usage_summary 表索引
        {
            'name': 'idx_daily_summary_date',
            'table': 'daily_gpu_usage_summary',
            'columns': 'summary_date',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON daily_gpu_usage_summary(summary_date)'
        },
        
        # daily_device_summary 表索引
        {
            'name': 'idx_device_summary_date',
            'table': 'daily_device_summary',
            'columns': 'summary_date',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_device_summary_date ON daily_device_summary(summary_date)'
        },
        {
            'name': 'idx_device_id_date',
            'table': 'daily_device_summary',
            'columns': 'device_id, summary_date',
            'sql': 'CREATE UNIQUE INDEX IF NOT EXISTS idx_device_id_date ON daily_device_summary(device_id, summary_date)'
        },
        {
            'name': 'idx_device_org_id3',
            'table': 'daily_device_summary',
            'columns': 'organization_id3',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_device_org_id3 ON daily_device_summary(organization_id3)'
        },
        
        # org_gpu_usage_summary 表索引
        {
            'name': 'idx_org_summary_time',
            'table': 'org_gpu_usage_summary',
            'columns': 'summary_time',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_org_summary_time ON org_gpu_usage_summary(summary_time)'
        },
        {
            'name': 'idx_org_name3',
            'table': 'org_gpu_usage_summary',
            'columns': 'organization_name3',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_org_name3 ON org_gpu_usage_summary(organization_name3)'
        },
        {
            'name': 'idx_org_name3_time',
            'table': 'org_gpu_usage_summary',
            'columns': 'organization_name3, summary_time',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_org_name3_time ON org_gpu_usage_summary(organization_name3, summary_time)'
        },
        {
            'name': 'idx_org_id3_time',
            'table': 'org_gpu_usage_summary',
            'columns': 'organization_id3, summary_time',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_org_id3_time ON org_gpu_usage_summary(organization_id3, summary_time)'
        },
        
        # statistics_data 表索引
        {
            'name': 'idx_stat_type_work',
            'table': 'statistics_data',
            'columns': 'stat_type, is_work_hour',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_stat_type_work ON statistics_data(stat_type, is_work_hour)'
        },
        {
            'name': 'idx_stat_time',
            'table': 'statistics_data',
            'columns': 'stat_time',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_stat_time ON statistics_data(stat_time)'
        },
        {
            'name': 'idx_stat_type_time',
            'table': 'statistics_data',
            'columns': 'stat_type, stat_time',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_stat_type_time ON statistics_data(stat_type, stat_time)'
        },
        {
            'name': 'idx_stat_date_hour_type',
            'table': 'statistics_data',
            'columns': 'stat_date, stat_hour, stat_type',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_stat_date_hour_type ON statistics_data(stat_date, stat_hour, stat_type)'
        },
    ]
    
    db = LocalSessionLocal()
    try:
        for idx in indexes_to_create:
            try:
                db.execute(text(idx['sql']))
                print(f"Created index: {idx['name']} on {idx['table']}({idx['columns']})")
            except Exception as e:
                if 'already exists' in str(e).lower():
                    print(f"Index already exists: {idx['name']}")
                else:
                    print(f"Error creating index {idx['name']}: {e}")
        
        db.commit()
        print("\nAll indexes created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
    finally:
        db.close()


def check_indexes():
    """检查现有索引"""
    db = LocalSessionLocal()
    try:
        tables = ['daily_gpu_usage_summary', 'daily_device_summary', 'org_gpu_usage_summary', 'statistics_data', 'org_hourly_stats']
        
        for table in tables:
            result = db.execute(text(f"PRAGMA index_list({table})"))
            indexes = result.fetchall()
            print(f"\n{table} indexes:")
            for idx in indexes:
                idx_name = idx[1]
                idx_info = db.execute(text(f"PRAGMA index_info({idx_name})"))
                columns = [col[2] for col in idx_info.fetchall()]
                print(f"  - {idx_name}: {', '.join(columns)}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Checking current indexes...")
    check_indexes()
    
    print("\n" + "="*50)
    print("Adding new indexes...")
    print("="*50 + "\n")
    
    add_indexes()
    
    print("\n" + "="*50)
    print("Verifying indexes after migration...")
    print("="*50)
    check_indexes()

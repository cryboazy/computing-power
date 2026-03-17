from datetime import date, timedelta
from sqlalchemy import text
from app.database import SessionLocal
from app.models import DeviceGpuMonitor, DailyGpuUsageSummary, DailyDeviceSummary, OrgGpuUsageSummary, StatisticsData
from app.aggregator import DataAggregator


def reset_and_regenerate():
    db = SessionLocal()
    try:
        print("=== 开始清空聚合数据 ===")
        
        db.query(DailyGpuUsageSummary).delete()
        db.query(DailyDeviceSummary).delete()
        db.query(OrgGpuUsageSummary).delete()
        db.query(StatisticsData).delete()
        db.commit()
        print("聚合数据已清空")
        
        print("\n=== 查询原始数据日期范围 ===")
        result = db.query(
            DeviceGpuMonitor.collection_timestamp
        ).order_by(DeviceGpuMonitor.collection_timestamp.asc()).first()
        
        if result:
            earliest = result.collection_timestamp.date()
            result = db.query(
                DeviceGpuMonitor.collection_timestamp
            ).order_by(DeviceGpuMonitor.collection_timestamp.desc()).first()
            latest = result.collection_timestamp.date()
            
            print(f"原始数据范围: {earliest} 到 {latest}")
            
            days_to_aggregate = (latest - earliest).days + 1
            print(f"需要聚合 {days_to_aggregate} 天的数据")
            
            print("\n=== 开始重新生成聚合数据 ===")
            aggregator = DataAggregator(db)
            
            current_date = earliest
            while current_date <= latest:
                print(f"\n处理日期: {current_date}")
                aggregator.run_all_aggregations(current_date)
                current_date += timedelta(days=1)
            
            print("\n=== 聚合数据重新生成完成 ===")
        else:
            print("没有找到原始监控数据")
            
    except Exception as e:
        print(f"错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_and_regenerate()

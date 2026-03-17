from datetime import date, timedelta
from app.database import SessionLocal
from app.aggregator import DataAggregator

db = SessionLocal()

try:
    aggregator = DataAggregator(db)
    
    for i in range(7):
        target_date = date.today() - timedelta(days=i)
        print(f"\n聚合 {target_date} 的数据...")
        aggregator.run_all_aggregations(target_date)
    
    print("\n所有数据聚合完成！")
    
finally:
    db.close()

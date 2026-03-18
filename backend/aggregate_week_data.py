from datetime import date, timedelta
from app.database import SessionLocal
from app.local_database import LocalSessionLocal
from app.aggregator import DataAggregator

db = SessionLocal()
local_db = LocalSessionLocal()

try:
    aggregator = DataAggregator(db, local_db)
    
    for i in range(7):
        target_date = date.today() - timedelta(days=i)
        print(f"\n聚合 {target_date} 的数据...")
        aggregator.run_all_aggregations(target_date)
    
    print("\n所有数据聚合完成！")
    
finally:
    db.close()
    local_db.close()

import sys
sys.path.insert(0, '.')

from app.aggregator import run_aggregation

days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
print(f"开始重新聚合 {days} 天的数据...")
run_aggregation(days)
print("数据聚合完成！")

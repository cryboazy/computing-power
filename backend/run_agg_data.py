import sys
sys.path.insert(0, '.')

from app.aggregator import run_aggregation

print("开始重新聚合数据...")
run_aggregation(3)
print("数据聚合完成！")

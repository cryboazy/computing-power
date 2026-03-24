from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date, timedelta

from app.api_cached import router as api_router
from app.admin import router as admin_router, set_aggregation_config_changed_callback
from app.aggregator import DataAggregator
from app.cache_sync import CacheSyncService
from app.database import SessionLocal
from app.local_database import init_local_db, LocalSessionLocal
from app.local_models import LocalSystemConfig


def get_auto_aggregation_config():
    local_db = LocalSessionLocal()
    try:
        configs = local_db.query(LocalSystemConfig).all()
        config_map = {c.config_key: c.config_value for c in configs}

        enabled = config_map.get("auto_aggregation_enabled", "true").lower() == "true"
        hour = int(config_map.get("auto_aggregation_hour", 1))
        minute = int(config_map.get("auto_aggregation_minute", 0))

        return enabled, hour, minute
    finally:
        local_db.close()


def scheduled_aggregation():
    db = SessionLocal()
    local_db = LocalSessionLocal()
    try:
        aggregator = DataAggregator(db, local_db)
        aggregator.run_all_aggregations(date.today() - timedelta(days=1))
    except Exception as e:
        print(f"定时聚合任务执行失败: {e}")
    finally:
        db.close()
        local_db.close()


def scheduled_cache_sync():
    db = SessionLocal()
    local_db = LocalSessionLocal()
    try:
        service = CacheSyncService(db, local_db)
        results = service.sync_all_static_data(force=False)
        print(f"定时缓存同步完成: {results}")
    except Exception as e:
        print(f"定时缓存同步失败: {e}")
    finally:
        db.close()
        local_db.close()


scheduler = BackgroundScheduler()


def setup_aggregation_job():
    try:
        enabled, hour, minute = get_auto_aggregation_config()
    except Exception as e:
        print(f"读取聚合配置失败，使用默认值: {e}")
        enabled, hour, minute = True, 1, 0

    for job in scheduler.get_jobs():
        if job.id == "auto_aggregation":
            scheduler.remove_job("auto_aggregation")

    if enabled:
        scheduler.add_job(scheduled_aggregation, 'cron', hour=hour, minute=minute, id="auto_aggregation")
        print(f"自动聚合任务已设置: 每天 {hour:02d}:{minute:02d}")
    else:
        print("自动聚合任务已禁用")


init_local_db()
setup_aggregation_job()
scheduler.add_job(scheduled_cache_sync, 'cron', hour='*', minute=5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_local_db(upgrade=True)
    print("初始化缓存数据...")
    db = SessionLocal()
    local_db = LocalSessionLocal()
    try:
        service = CacheSyncService(db, local_db)
        service.sync_all_static_data(force=True)
        print("缓存数据初始化完成")
    except Exception as e:
        print(f"缓存数据初始化失败: {e}")
    finally:
        db.close()
        local_db.close()
    print("智能算力监测平台API启动...")
    
    scheduler.start()
    
    yield
    
    scheduler.shutdown()
    print("智能算力监测平台API关闭...")


app = FastAPI(
    title="智能算力监测平台API",
    description="提供GPU使用情况监测数据接口",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 生产环境应考虑限制 CORS
# allow_origins=["https://your-domain.com"]

app.include_router(api_router, prefix="/api")
app.include_router(admin_router, prefix="/api/admin")


def on_aggregation_config_changed():
    setup_aggregation_job()


set_aggregation_config_changed_callback(on_aggregation_config_changed)


@app.get("/")
def root():
    return {
        "message": "智能算力监测平台API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

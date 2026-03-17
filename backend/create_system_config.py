import psycopg2
from app.config import settings

conn = psycopg2.connect(
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD
)

cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_config (
        id bigserial NOT NULL,
        config_key varchar(100) NOT NULL,
        config_value varchar(500),
        description varchar(255),
        create_time timestamp DEFAULT pg_systimestamp(),
        update_time timestamp DEFAULT pg_systimestamp(),
        CONSTRAINT system_config_pkey PRIMARY KEY (id),
        CONSTRAINT system_config_key_unique UNIQUE (config_key)
    );
    
    COMMENT ON TABLE system_config IS '系统配置表';
    COMMENT ON COLUMN system_config.id IS '主键ID';
    COMMENT ON COLUMN system_config.config_key IS '配置键';
    COMMENT ON COLUMN system_config.config_value IS '配置值';
    COMMENT ON COLUMN system_config.description IS '配置描述';
    COMMENT ON COLUMN system_config.create_time IS '创建时间';
    COMMENT ON COLUMN system_config.update_time IS '更新时间';
""")

conn.commit()
print("system_config 表创建成功！")

cursor.close()
conn.close()

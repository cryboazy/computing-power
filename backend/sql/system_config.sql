-- 系统配置表
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

-- 初始化系统配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('work_hour_start', '9', '工作时段开始时间（小时）'),
('work_hour_end', '18', '工作时段结束时间（小时）'),
('high_usage_threshold', '60', '高使用率阈值（%）'),
('low_usage_threshold', '30', '低使用率阈值（%）'),
('data_retention_days', '365', '数据保留天数'),
('summary_schedule', '0 1 * * *', '汇总任务执行时间（cron表达式）')
ON CONFLICT (config_key) DO NOTHING;

-- 字典数据表
CREATE TABLE IF NOT EXISTS sys_dict_data (
    id bigserial NOT NULL,
    dict_type varchar(100) NOT NULL,
    dict_label varchar(100) NOT NULL,
    dict_value integer NOT NULL,
    dict_sort integer DEFAULT 0,
    status smallint DEFAULT 1,
    remark varchar(500) DEFAULT '',
    create_time timestamp DEFAULT pg_systimestamp(),
    update_time timestamp DEFAULT pg_systimestamp(),
    create_by varchar(50) DEFAULT '',
    update_by varchar(50) DEFAULT '',
    deleted smallint DEFAULT 0,
    CONSTRAINT sys_dict_data_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_sys_dict_type ON sys_dict_data(dict_type);
CREATE INDEX IF NOT EXISTS idx_sys_dict_value ON sys_dict_data(dict_value);

COMMENT ON TABLE sys_dict_data IS '字典数据表';
COMMENT ON COLUMN sys_dict_data.id IS '主键ID';
COMMENT ON COLUMN sys_dict_data.dict_type IS '字典类型';
COMMENT ON COLUMN sys_dict_data.dict_label IS '字典标签';
COMMENT ON COLUMN sys_dict_data.dict_value IS '字典值';
COMMENT ON COLUMN sys_dict_data.dict_sort IS '排序';
COMMENT ON COLUMN sys_dict_data.status IS '状态(1正常 0停用)';
COMMENT ON COLUMN sys_dict_data.remark IS '备注';
COMMENT ON COLUMN sys_dict_data.create_time IS '创建时间';
COMMENT ON COLUMN sys_dict_data.update_time IS '更新时间';
COMMENT ON COLUMN sys_dict_data.create_by IS '创建者';
COMMENT ON COLUMN sys_dict_data.update_by IS '更新者';
COMMENT ON COLUMN sys_dict_data.deleted IS '删除标志(0未删除 1已删除)';

-- 初始化设备用途字典
INSERT INTO sys_dict_data (dict_type, dict_label, dict_value, dict_sort, status, remark) VALUES
('device_purpose', '训练', 1, 1, 1, 'GPU设备用途-训练'),
('device_purpose', '研发', 2, 2, 1, 'GPU设备用途-研发'),
('device_purpose', '推理', 3, 3, 1, 'GPU设备用途-推理')
ON CONFLICT DO NOTHING;

# ASIN数据推送工具 - 优化版本

## 📋 概述

这是对原始 `asin_to_redis.py` 代码的优化重构版本，将原来1583行的单文件代码拆分为多个模块化的文件，提高了代码的可维护性、可读性和可扩展性。

## 🔧 优化改进

### 1. 模块化架构
- **config_manager.py**: 统一的配置管理器
- **connection_manager.py**: 连接管理器（Redis、数据库、OSS）
- **asin_pusher.py**: ASIN数据推送器
- **result_verifier.py**: 结果验证器
- **asin_to_redis_optimized.py**: 主程序入口

### 2. 代码优化
- ✅ 从1583行减少到约500行（分布在多个文件中）
- ✅ 使用上下文管理器自动管理连接
- ✅ 单一职责原则，每个类专注于特定功能
- ✅ 统一的错误处理机制
- ✅ 更清晰的命令行接口

### 3. 功能改进
- ✅ 更简洁的命令行参数
- ✅ 更好的错误提示
- ✅ 自动资源清理
- ✅ 模块化配置管理
- ✅ 智能等待时间动态计算（30s × ASIN数量 + 20s）
- ✅ 验证成功后自动导出数据到JSON文件
- ✅ 支持手动导出ASIN完整数据
- ✅ 每个ASIN生成单独的JSON文件（便于管理和处理）
- ✅ 文件名包含站点信息（如：US-B08HBSRFK2.json）

## 📦 文件结构

```
├── config.ini                      # 配置文件
├── config_manager.py               # 配置管理器
├── connection_manager.py           # 连接管理器
├── asin_pusher.py                  # ASIN推送器
├── result_verifier.py              # 结果验证器
├── asin_to_redis_optimized.py      # 主程序（优化版）
├── test_optimized.py               # 功能测试脚本
├── check_dependencies.py           # 依赖检查脚本
├── requirements.txt                # 核心依赖文件
├── requirements-dev.txt            # 开发依赖文件
├── result/                         # 导出数据文件夹
│   ├── US-B08HBSRFK2.json         # 单个ASIN导出文件
│   └── UK-B0DW8MQFD7.json         # 单个ASIN导出文件
└── README_优化版本.md              # 使用说明
```

## 🚀 使用方法

### 基础推送
```bash
# 推送ASIN数据到Redis
python asin_to_redis_optimized.py push -f asin.txt

# 自动确认推送
python asin_to_redis_optimized.py push -f asin.txt -y
```

### 智能等待推送（推荐）
```bash
# 推送后等待爬虫完成（验证成功后自动导出数据）
python asin_to_redis_optimized.py push -f asin.txt --wait -y

# 自定义检查间隔（等待时间自动计算：30s × ASIN数量 + 20s）
python asin_to_redis_optimized.py push -f asin.txt --wait --check-interval 5
```

### 结果验证
```bash
# 验证ASIN处理结果
python asin_to_redis_optimized.py verify -f asin.txt

# 自定义超时时间
python asin_to_redis_optimized.py verify -f asin.txt --db-timeout 600 --oss-timeout 600
```

### 数据导出
```bash
# 手动导出ASIN数据到JSON文件
python asin_to_redis_optimized.py export -f asin.txt
```
- 导出文件保存在 `result/` 文件夹中
- **每个ASIN生成单独的JSON文件**
- 文件名格式：`{SITE}-{ASIN}.json`
  - 美国站：`US-B08HBSRFK2.json`
  - 英国站：`UK-B0DW8MQFD7.json`
  - 德国站：`DE-B08HBSRFK2.json`
- 包含完整的数据库ASIN信息
- 未找到的ASIN会显示错误信息但不会创建文件

### 连接测试
```bash
# 测试Redis连接
python asin_to_redis_optimized.py test
```

## ⚙️ 配置文件

使用现有的 `config.ini` 文件，格式保持不变：

```ini
[database]
type = mysql
host = your-db-host
port = 3306
user = your-username
password = your-password
database = your-database
status_table = amazon_asin_crawl_detail_ai
asin_field = asin
site_field = site
update_time_field = update_time
verification_method = existence

[database_ssh]
ssh_host = your-ssh-host
ssh_port = 22
ssh_username = root
ssh_private_key = /path/to/private/key.pem
remote_host = your-remote-db-host
remote_port = 3306

[oss]
type = aliyun
endpoint = oss-cn-beijing.aliyuncs.com
access_key_id = your-access-key-id
access_key_secret = your-access-key-secret
bucket = your-bucket-name
main_image_pattern = {asin}_{site}_first_img.png
sub_image_pattern = {asin}_{site}_images_{index}.png
sub_image_count = 6
image_verification_mode = main_only

[verification]
db_timeout = 300
oss_timeout = 300
check_interval = 30
max_retries = 3
```

## 📋 依赖要求

### 核心依赖
```
redis>=4.5.0,<6.0.0          # Redis连接
PyMySQL>=1.0.0,<2.0.0        # MySQL数据库连接
sshtunnel>=0.4.0,<1.0.0      # SSH隧道支持
oss2>=2.17.0,<3.0.0          # 阿里云OSS存储
cryptography>=40.0.0,<42.0.0 # 加密库支持
```

### 系统要求
- **Python版本**: >= 3.8
- **操作系统**: Windows 10+, macOS 10.15+, Linux (Ubuntu 18.04+)
- **Redis服务器**: >= 5.0
- **MySQL服务器**: >= 5.7

### 安装依赖

**基础安装**（生产环境）：
```bash
pip install -r requirements.txt
```

**开发安装**（包含测试和开发工具）：
```bash
pip install -r requirements-dev.txt
```

**快速安装**（仅核心功能）：
```bash
pip install redis PyMySQL sshtunnel oss2 cryptography
```

**国内镜像**（加速安装）：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

**依赖检查**（验证安装）：
```bash
python check_dependencies.py
```

## 🎯 核心功能

### 1. ASIN推送器 (ASINPusher)
- 读取ASIN文件（支持多种格式）
- 格式化为Redis格式（SITE@ASIN）
- 推送到Redis Set
- 自动去重和统计

### 2. 结果验证器 (ResultVerifier)
- 验证数据库处理状态
- 验证OSS文件状态
- 智能等待功能（动态时间计算）
- 综合验证报告
- 数据导出功能（JSON格式，每个ASIN单独文件）
- 验证成功后自动导出
- 支持多站点文件命名（US-、UK-、DE- 等）

### 3. 连接管理器 (ConnectionManager)
- 统一管理所有连接
- 自动SSH隧道创建
- 上下文管理器自动清理
- 连接重试机制

### 4. 配置管理器 (ConfigManager)
- 统一配置加载
- 配置验证
- 默认值处理

## 📊 对比原版本

| 特性 | 原版本 | 优化版本 |
|------|--------|----------|
| 代码行数 | 1583行 | ~500行（分布式） |
| 文件数量 | 1个 | 5个模块 |
| 命令行接口 | 复杂参数 | 清晰子命令 |
| 代码维护性 | 困难 | 简单 |
| 功能扩展性 | 困难 | 简单 |
| 错误处理 | 分散 | 统一 |
| 资源管理 | 手动 | 自动 |

## 🎉 推荐工作流

1. **测试连接**
   ```bash
   python asin_to_redis_optimized.py test
   ```

2. **推送并等待**（最推荐 - 自动导出数据）
   ```bash
   python asin_to_redis_optimized.py push -f your_asin_file.txt --wait -y
   ```
   - 自动计算智能等待时间
   - 验证成功后自动导出数据到JSON文件
   - 一站式完成所有任务

3. **手动验证**（如果需要）
   ```bash
   python asin_to_redis_optimized.py verify -f your_asin_file.txt
   ```

4. **手动导出数据**（如果需要）
   ```bash
   python asin_to_redis_optimized.py export -f your_asin_file.txt
   ```

## 🔍 故障排除

### 依赖安装问题
- **更新pip**: `python -m pip install --upgrade pip`
- **清理缓存**: `pip cache purge`
- **使用国内镜像**: `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`
- **Windows用户**: 可能需要安装Visual C++构建工具
- **权限问题**: 使用 `pip install --user` 或虚拟环境

### 连接问题
- 检查SSH私钥路径和权限
- 确认网络连接和防火墙设置
- 验证配置文件格式和参数
- 测试SSH隧道连接: `ssh -i your_key.pem user@host`

### 推送问题
- 检查ASIN文件路径和格式
- 确认Redis连接和密码
- 验证Redis服务状态: `redis-cli ping`
- 查看详细错误信息和日志

### 验证问题
- 确认数据库和OSS配置参数
- 检查访问权限和密钥设置
- 调整超时时间参数
- 验证表结构和字段名称

### 性能问题
- 大量ASIN时建议分批处理
- 调整检查间隔和超时时间
- 监控系统资源使用情况
- 考虑使用连接池优化

## 💡 最佳实践

1. **使用智能等待**：推荐使用 `--wait` 参数，可以自动监控完成状态并导出数据
2. **批量处理**：对于大量ASIN，建议分批处理
3. **配置验证**：推送前先运行 `test` 命令验证连接
4. **错误恢复**：如果等待超时，可以稍后手动运行 `verify` 命令
5. **数据导出**：
   - 使用 `--wait` 时会自动导出数据
   - 也可使用 `export` 命令手动导出
   - **每个ASIN生成单独的JSON文件**，便于管理
   - 文件名格式：`{SITE}-{ASIN}.json`（如：`US-B08HBSRFK2.json`）
   - 导出的JSON文件包含完整的数据库信息
   - 文件保存在 `result/` 文件夹中

## 📞 技术支持

如果遇到问题，请检查：
1. 配置文件是否正确
2. 依赖是否安装完整
3. 网络连接是否正常
4. 权限设置是否正确 

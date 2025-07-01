import configparser
import os


class ConfigManager:
    """配置管理器 - 统一管理所有配置信息"""
    
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
        
        config = configparser.ConfigParser()
        config.read(self.config_file, encoding='utf-8')
        
        # 数据库配置
        self.config['database'] = {
            'type': config.get('database', 'type', fallback='mysql'),
            'host': config.get('database', 'host'),
            'port': config.getint('database', 'port'),
            'user': config.get('database', 'user'),
            'password': config.get('database', 'password'),
            'database': config.get('database', 'database'),
            'status_table': config.get('database', 'status_table'),
            'asin_field': config.get('database', 'asin_field'),
            'site_field': config.get('database', 'site_field'),
            'update_time_field': config.get('database', 'update_time_field'),
            'verification_method': config.get('database', 'verification_method')
        }
        
        # SSH配置
        self.config['ssh'] = {
            'host': config.get('database_ssh', 'ssh_host'),
            'port': config.getint('database_ssh', 'ssh_port'),
            'username': config.get('database_ssh', 'ssh_username'),
            'private_key': config.get('database_ssh', 'ssh_private_key'),
            'remote_host': config.get('database_ssh', 'remote_host'),
            'remote_port': config.getint('database_ssh', 'remote_port')
        }
        
        # OSS配置
        self.config['oss'] = {
            'type': config.get('oss', 'type'),
            'endpoint': config.get('oss', 'endpoint'),
            'access_key_id': config.get('oss', 'access_key_id'),
            'access_key_secret': config.get('oss', 'access_key_secret'),
            'bucket': config.get('oss', 'bucket'),
            'main_image_pattern': config.get('oss', 'main_image_pattern'),
            'sub_image_pattern': config.get('oss', 'sub_image_pattern'),
            'sub_image_count': config.getint('oss', 'sub_image_count'),
            'image_verification_mode': config.get('oss', 'image_verification_mode')
        }
        
        # 验证配置
        self.config['verification'] = {
            'db_timeout': config.getint('verification', 'db_timeout'),
            'oss_timeout': config.getint('verification', 'oss_timeout'),
            'check_interval': config.getint('verification', 'check_interval'),
            'max_retries': config.getint('verification', 'max_retries')
        }
        
        # Redis配置（硬编码部分）
        self.config['redis'] = {
            'host': 'r-wz9zdyw0uvqn98nkry.redis.rds.aliyuncs.com',
            'port': 6379,
            'db': 15,
            'password': 'YPq1uMjJCQce',
            'key': 'amazon:asin_details_ai:crawl_task'
        }
    
    def get(self, section, key=None):
        """获取配置值"""
        if key is None:
            return self.config.get(section, {})
        return self.config.get(section, {}).get(key) 
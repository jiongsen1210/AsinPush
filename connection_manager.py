import redis
import time
from contextlib import contextmanager
from sshtunnel import SSHTunnelForwarder

# 可选依赖导入
try:
    import pymysql
    pymysql.install_as_MySQLdb()
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import oss2
    OSS_AVAILABLE = True
except ImportError:
    OSS_AVAILABLE = False


class ConnectionManager:
    """连接管理器 - 统一管理Redis、数据库和OSS连接"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self._redis_client = None
        self._db_client = None
        self._oss_client = None
        self._ssh_tunnel = None
        self._db_ssh_tunnel = None
        self._local_ports = {'redis': 16379, 'db': 13306}
    
    @contextmanager
    def redis_connection(self):
        """Redis连接上下文管理器"""
        try:
            self._connect_redis()
            yield self._redis_client
        finally:
            self._close_redis()
    
    @contextmanager
    def database_connection(self):
        """数据库连接上下文管理器"""
        try:
            self._connect_database()
            yield self._db_client
        finally:
            self._close_database()
    
    @contextmanager
    def oss_connection(self):
        """OSS连接上下文管理器"""
        try:
            self._connect_oss()
            yield self._oss_client
        finally:
            pass  # OSS不需要显式关闭
    
    def _connect_redis(self):
        """连接Redis"""
        if self._redis_client:
            return True
            
        try:
            ssh_config = self.config.get('ssh')
            redis_config = self.config.get('redis')
            
            # 创建SSH隧道
            self._ssh_tunnel = SSHTunnelForwarder(
                (ssh_config['host'], ssh_config['port']),
                ssh_username=ssh_config['username'],
                ssh_pkey=ssh_config['private_key'],
                remote_bind_address=(redis_config['host'], redis_config['port']),
                local_bind_address=('127.0.0.1', self._local_ports['redis'])
            )
            self._ssh_tunnel.start()
            
            # 连接Redis
            self._redis_client = redis.Redis(
                host='127.0.0.1',
                port=self._local_ports['redis'],
                db=redis_config['db'],
                password=redis_config['password'],
                decode_responses=True
            )
            
            # 测试连接
            self._redis_client.ping()
            print("✅ Redis连接成功")
            return True
            
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            self._close_redis()
            return False
    
    def _close_redis(self):
        """关闭Redis连接"""
        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None
        if self._ssh_tunnel:
            self._ssh_tunnel.close()
            self._ssh_tunnel = None
    
    def _connect_database(self):
        """连接数据库"""
        if self._db_client:
            return True
            
        if not MYSQL_AVAILABLE:
            print("❌ PyMySQL未安装")
            return False
            
        try:
            ssh_config = self.config.get('ssh')
            db_config = self.config.get('database')
            
            # 创建SSH隧道
            self._db_ssh_tunnel = SSHTunnelForwarder(
                (ssh_config['host'], ssh_config['port']),
                ssh_username=ssh_config['username'],
                ssh_pkey=ssh_config['private_key'],
                remote_bind_address=(ssh_config['remote_host'], ssh_config['remote_port']),
                local_bind_address=('127.0.0.1', self._local_ports['db'])
            )
            self._db_ssh_tunnel.start()
            
            # 连接数据库
            self._db_client = pymysql.connect(
                host='127.0.0.1',
                port=self._local_ports['db'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database'],
                charset='utf8mb4',
                autocommit=True
            )
            
            # 测试连接
            with self._db_client.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            print("✅ 数据库连接成功")
            return True
            
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            self._close_database()
            return False
    
    def _close_database(self):
        """关闭数据库连接"""
        if self._db_client:
            self._db_client.close()
            self._db_client = None
        if self._db_ssh_tunnel:
            self._db_ssh_tunnel.close()
            self._db_ssh_tunnel = None
    
    def _connect_oss(self):
        """连接OSS"""
        if self._oss_client:
            return True
            
        if not OSS_AVAILABLE:
            print("❌ oss2未安装")
            return False
            
        try:
            oss_config = self.config.get('oss')
            
            # 创建OSS客户端
            auth = oss2.Auth(oss_config['access_key_id'], oss_config['access_key_secret'])
            endpoint = oss_config['endpoint']
            if not endpoint.startswith('http'):
                endpoint = f"https://{endpoint}"
            
            self._oss_client = oss2.Bucket(auth, endpoint, oss_config['bucket'])
            
            # 测试连接
            self._oss_client.get_bucket_info()
            print("✅ OSS连接成功")
            return True
            
        except Exception as e:
            print(f"❌ OSS连接失败: {e}")
            return False 
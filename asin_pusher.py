import os
from config_manager import ConfigManager
from connection_manager import ConnectionManager


class ASINPusher:
    """ASIN数据推送器 - 专注于将ASIN数据推送到Redis"""
    
    def __init__(self, config_file='config.ini'):
        self.config = ConfigManager(config_file)
        self.connection = ConnectionManager(self.config)
    
    def read_asin_file(self, file_path):
        """读取ASIN文件并解析数据
        
        Args:
            file_path (str): ASIN文件路径
            
        Returns:
            list: 解析后的ASIN数据列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        asin_data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 解析ASIN和站点
                asin, site = self._parse_asin_line(line)
                if asin:
                    asin_data.append({'asin': asin, 'site': site})
        
        print(f"📊 从文件读取到 {len(asin_data)} 条ASIN数据")
        return asin_data
    
    def _parse_asin_line(self, line):
        """解析单行ASIN数据
        
        Args:
            line (str): 单行数据
            
        Returns:
            tuple: (asin, site)
        """
        # 如果已经是SITE@ASIN格式，直接解析
        if '@' in line:
            parts = line.split('@', 1)
            if len(parts) == 2:
                site = parts[0].strip().upper()
                asin = parts[1].strip()
                return asin, site
        
        # 支持其他分隔符：ASIN,SITE 或 ASIN SITE 或 ASIN\tSITE
        for separator in [',', '\t', ' ']:
            if separator in line:
                parts = line.split(separator, 1)
                asin = parts[0].strip()
                site = parts[1].strip().upper() if len(parts) > 1 else 'US'
                return asin, site
        
        # 只有ASIN，默认US站点
        return line.strip(), 'US'
    
    def format_asin_data(self, asin_data):
        """格式化ASIN数据为Redis格式
        
        Args:
            asin_data (list): ASIN数据列表
            
        Returns:
            list: 格式化后的数据列表
        """
        formatted_data = []
        
        for item in asin_data:
            formatted_asin = f"{item['site']}@{item['asin']}"
            formatted_data.append(formatted_asin)
        
        # 显示示例
        if formatted_data:
            print("📝 格式化示例:")
            for i, example in enumerate(formatted_data[:3]):
                print(f"   {i+1}. {example}")
            if len(formatted_data) > 3:
                print(f"   ... 还有 {len(formatted_data) - 3} 条数据")
        
        return formatted_data
    
    def push_to_redis(self, formatted_data):
        """推送数据到Redis
        
        Args:
            formatted_data (list): 格式化的ASIN数据
            
        Returns:
            dict: 推送结果
        """
        if not formatted_data:
            return {'success': False, 'message': '没有数据需要推送'}
        
        redis_key = self.config.get('redis', 'key')
        
        with self.connection.redis_connection() as redis_client:
            if not redis_client:
                return {'success': False, 'message': 'Redis连接失败'}
            
            # 获取推送前的数据量
            current_count = redis_client.scard(redis_key)
            
            # 批量推送
            added_count = redis_client.sadd(redis_key, *formatted_data)
            
            # 获取推送后的数据量
            new_count = redis_client.scard(redis_key)
            
            result = {
                'success': True,
                'pushed_count': len(formatted_data),
                'added_count': added_count,
                'duplicate_count': len(formatted_data) - added_count,
                'total_count': new_count,
                'message': f'推送完成，新增 {added_count} 条数据'
            }
            
            print(f"✅ 数据推送成功!")
            print(f"   推送数据: {result['pushed_count']} 条")
            print(f"   实际新增: {result['added_count']} 条")
            print(f"   重复数据: {result['duplicate_count']} 条")
            print(f"   总数据量: {result['total_count']} 条")
            
            return result
    
    def run(self, file_path):
        """运行完整的推送流程
        
        Args:
            file_path (str): ASIN文件路径
            
        Returns:
            dict: 运行结果
        """
        try:
            print("🚀 开始ASIN数据推送...")
            print(f"📄 文件路径: {file_path}")
            
            # 读取文件
            asin_data = self.read_asin_file(file_path)
            if not asin_data:
                return {'success': False, 'message': '没有找到有效的ASIN数据'}
            
            # 格式化数据
            formatted_data = self.format_asin_data(asin_data)
            
            # 推送到Redis
            result = self.push_to_redis(formatted_data)
            
            if result['success']:
                print("🎉 ASIN推送任务完成!")
            
            return result
            
        except Exception as e:
            error_msg = f"推送失败: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'message': error_msg}
    
    def test_connection(self):
        """测试Redis连接"""
        print("🔗 测试Redis连接...")
        
        with self.connection.redis_connection() as redis_client:
            if redis_client:
                redis_key = self.config.get('redis', 'key')
                count = redis_client.scard(redis_key)
                print(f"✅ 连接成功! 当前数据量: {count}")
                return True
            else:
                print("❌ 连接失败!")
                return False 
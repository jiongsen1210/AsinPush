import time
import json
import os
from datetime import datetime, timezone, date
from config_manager import ConfigManager
from connection_manager import ConnectionManager


class ResultVerifier:
    """结果验证器 - 专注于验证数据库和OSS处理结果"""
    
    def __init__(self, config_file='config.ini'):
        self.config = ConfigManager(config_file)
        self.connection = ConnectionManager(self.config)
    
    def verify_database(self, asin_list, timeout=300):
        """验证数据库处理状态
        
        Args:
            asin_list (list): ASIN列表 ["US@B0CXCPTW7G", ...]
            timeout (int): 超时时间
            
        Returns:
            dict: 验证结果
        """
        print("📊 验证数据库处理状态...")
        
        with self.connection.database_connection() as db_client:
            if not db_client:
                return {'success': False, 'message': '数据库连接失败'}
            
            db_config = self.config.get('database')
            verification_method = db_config['verification_method']
            
            processed_asins = []
            failed_asins = []
            pending_asins = []
            
            # 解析ASIN列表
            check_items = []
            for item in asin_list:
                if '@' in item:
                    site, asin = item.split('@', 1)
                else:
                    site, asin = 'US', item
                check_items.append({'site': site, 'asin': asin, 'full': item})
            
            # 分批检查
            batch_size = 100
            for i in range(0, len(check_items), batch_size):
                batch = check_items[i:i+batch_size]
                
                if verification_method == 'existence':
                    # 存在性检查
                    conditions = []
                    for item in batch:
                        conditions.append(
                            f"({db_config['asin_field']} = '{item['asin']}' "
                            f"AND {db_config['site_field']} = '{item['site']}')"
                        )
                    
                    where_clause = ' OR '.join(conditions)
                    sql = f"""
                    SELECT {db_config['asin_field']}, {db_config['site_field']},
                           {db_config['update_time_field']}
                    FROM {db_config['status_table']} 
                    WHERE {where_clause}
                    """
                    
                    with db_client.cursor() as cursor:
                        cursor.execute(sql)
                        results = cursor.fetchall()
                    
                    # 处理结果
                    found_items = {}
                    for row in results:
                        key = f"{row[1]}@{row[0]}"
                        found_items[key] = row[2] if len(row) > 2 else None
                    
                    for item in batch:
                        full_asin = item['full']
                        if full_asin in found_items:
                            processed_asins.append(full_asin)
                        else:
                            pending_asins.append(full_asin)
            
            result = {
                'success': len(pending_asins) == 0,
                'processed_count': len(processed_asins),
                'total_count': len(asin_list),
                'processed_asins': processed_asins,
                'pending_asins': pending_asins,
                'failed_asins': failed_asins
            }
            
            print(f"   总数: {result['total_count']}")
            print(f"   已处理: {result['processed_count']}")
            print(f"   待处理: {len(result['pending_asins'])}")
            
            return result
    
    def verify_oss(self, asin_list, timeout=300):
        """验证OSS文件状态
        
        Args:
            asin_list (list): ASIN列表
            timeout (int): 超时时间
            
        Returns:
            dict: 验证结果
        """
        print("☁️  验证OSS文件状态...")
        
        with self.connection.oss_connection() as oss_client:
            if not oss_client:
                return {'success': False, 'message': 'OSS连接失败'}
            
            oss_config = self.config.get('oss')
            verification_mode = oss_config['image_verification_mode']
            
            successful_asins = []
            failed_asins = []
            
            # 为每个ASIN生成文件列表
            for asin_item in asin_list:
                if '@' in asin_item:
                    site, asin = asin_item.split('@', 1)
                else:
                    site, asin = 'US', asin_item
                
                files_to_check = self._get_files_for_asin(asin, site, oss_config)
                
                # 检查文件存在性
                found_count = 0
                for file_path in files_to_check:
                    try:
                        if oss_client.object_exists(file_path):
                            found_count += 1
                    except Exception:
                        pass
                
                # 根据验证模式判断成功
                if self._is_verification_successful(found_count, len(files_to_check), verification_mode):
                    successful_asins.append(asin_item)
                else:
                    failed_asins.append(asin_item)
            
            result = {
                'success': len(failed_asins) == 0,
                'successful_asins': successful_asins,
                'failed_asins': failed_asins,
                'total_count': len(asin_list)
            }
            
            print(f"   总ASIN数: {result['total_count']}")
            print(f"   成功验证: {len(result['successful_asins'])}")
            print(f"   验证失败: {len(result['failed_asins'])}")
            
            return result
    
    def _get_files_for_asin(self, asin, site, oss_config):
        """获取ASIN对应的文件列表"""
        files = []
        verification_mode = oss_config['image_verification_mode']
        
        if verification_mode in ['main_only', 'all_images', 'any_image']:
            # 主图
            main_file = oss_config['main_image_pattern'].replace('{asin}', asin).replace('{site}', site)
            files.append(main_file)
        
        if verification_mode in ['all_images', 'any_image']:
            # 副图
            for i in range(oss_config['sub_image_count']):
                sub_file = (oss_config['sub_image_pattern']
                           .replace('{asin}', asin)
                           .replace('{site}', site)
                           .replace('{index}', str(i)))
                files.append(sub_file)
        
        return files
    
    def _is_verification_successful(self, found_count, total_count, verification_mode):
        """判断验证是否成功"""
        if verification_mode == 'main_only':
            return found_count > 0  # 主图存在即可
        elif verification_mode == 'all_images':
            return found_count == total_count  # 所有文件都存在
        elif verification_mode == 'any_image':
            return found_count > 0  # 任意文件存在即可
        return False
    
    def verify_all(self, asin_list, db_timeout=300, oss_timeout=300):
        """综合验证
        
        Args:
            asin_list (list): ASIN列表
            db_timeout (int): 数据库超时时间
            oss_timeout (int): OSS超时时间
            
        Returns:
            dict: 综合验证结果
        """
        print("🔍 开始综合验证...")
        
        start_time = time.time()
        
        # 验证数据库
        db_result = self.verify_database(asin_list, db_timeout)
        
        # 验证OSS
        oss_result = self.verify_oss(asin_list, oss_timeout)
        
        # 综合结果
        overall_success = db_result.get('success', False) and oss_result.get('success', False)
        
        result = {
            'success': overall_success,
            'database': db_result,
            'oss': oss_result,
            'duration': time.time() - start_time,
            'asin_count': len(asin_list)
        }
        
        print(f"\n📊 综合验证结果:")
        print(f"   整体状态: {'✅ 成功' if overall_success else '❌ 失败'}")
        print(f"   数据库: {'✅ 成功' if db_result.get('success') else '❌ 失败'}")
        print(f"   OSS: {'✅ 成功' if oss_result.get('success') else '❌ 失败'}")
        print(f"   验证耗时: {result['duration']:.2f} 秒")
        
        return result
    
    def export_asin_data(self, asin_list):
        """导出ASIN的完整数据到JSON文件
        
        Args:
            asin_list (list): ASIN列表
            
        Returns:
            dict: 导出结果
        """
        print("📥 开始导出ASIN数据...")
        
        try:
            # 创建result文件夹
            result_dir = 'result'
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)
                print(f"📁 创建文件夹: {result_dir}")
            
            # 获取完整的ASIN数据
            asin_data = self._fetch_full_asin_data(asin_list)
            
            if not asin_data:
                return {'success': False, 'message': '未找到任何ASIN数据'}
            
            # 按ASIN分组数据
            asin_data_map = {}
            for data_item in asin_data:
                full_asin = data_item.get('full_asin', '')
                if full_asin:
                    asin_data_map[full_asin] = data_item
            
            # 为每个ASIN创建单独的JSON文件
            exported_files = []
            total_file_size = 0
            found_count = 0
            
            for asin_item in asin_list:
                # 解析ASIN格式
                if '@' in asin_item:
                    site, pure_asin = asin_item.split('@', 1)
                else:
                    site, pure_asin = 'US', asin_item
                
                # 生成文件名：SITE-ASIN.json
                filename = f"{site}-{pure_asin}.json"
                filepath = os.path.join(result_dir, filename)
                
                # 查找对应的数据
                if asin_item in asin_data_map:
                    data_item = asin_data_map[asin_item]
                    found_count += 1
                    
                    # 准备单个ASIN的导出数据
                    export_data = {
                        'export_info': {
                            'timestamp': datetime.now().isoformat(),
                            'asin': asin_item,
                            'site': site,
                            'pure_asin': pure_asin
                        },
                        'data': data_item
                    }
                    
                    # 写入JSON文件
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2, default=self._json_serializer)
                    
                    file_size = os.path.getsize(filepath)
                    total_file_size += file_size
                    exported_files.append({
                        'filepath': filepath,
                        'filename': filename,
                        'asin': asin_item,
                        'size': file_size
                    })
                    
                    print(f"   ✅ {filename} ({file_size/1024:.1f} KB)")
                else:
                    print(f"   ❌ {filename} (数据库中未找到)")
            
            total_size_mb = total_file_size / (1024 * 1024)
            
            print(f"✅ 数据导出完成!")
            print(f"   总ASIN数: {len(asin_list)}")
            print(f"   成功导出: {found_count} 个文件")
            print(f"   总文件大小: {total_size_mb:.2f} MB")
            
            return {
                'success': True,
                'exported_files': exported_files,
                'total_asins': len(asin_list),
                'found_asins': found_count,
                'total_file_size': total_file_size
            }
            
        except Exception as e:
            print(f"❌ 导出失败: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def _fetch_full_asin_data(self, asin_list):
        """获取ASIN的完整数据
        
        Args:
            asin_list (list): ASIN列表
            
        Returns:
            list: ASIN完整数据列表
        """
        with self.connection.database_connection() as db_client:
            if not db_client:
                return []
            
            db_config = self.config.get('database')
            
            # 解析ASIN列表
            check_items = []
            for item in asin_list:
                if '@' in item:
                    site, asin = item.split('@', 1)
                else:
                    site, asin = 'US', item
                check_items.append({'site': site, 'asin': asin, 'full': item})
            
            all_data = []
            
            # 分批查询
            batch_size = 100
            for i in range(0, len(check_items), batch_size):
                batch = check_items[i:i+batch_size]
                
                # 构建查询条件
                conditions = []
                for item in batch:
                    conditions.append(
                        f"({db_config['asin_field']} = '{item['asin']}' "
                        f"AND {db_config['site_field']} = '{item['site']}')"
                    )
                
                where_clause = ' OR '.join(conditions)
                
                # 查询所有字段的数据
                sql = f"""
                SELECT * FROM {db_config['status_table']} 
                WHERE {where_clause}
                ORDER BY {db_config['site_field']}, {db_config['asin_field']}
                """
                
                try:
                    with db_client.cursor() as cursor:
                        cursor.execute(sql)
                        columns = [desc[0] for desc in cursor.description]
                        results = cursor.fetchall()
                        
                        # 转换为字典格式
                        for row in results:
                            row_dict = dict(zip(columns, row))
                            # 添加组合的ASIN标识
                            row_dict['full_asin'] = f"{row_dict.get(db_config['site_field'], 'US')}@{row_dict.get(db_config['asin_field'], '')}"
                            all_data.append(row_dict)
                            
                except Exception as e:
                    print(f"⚠️  查询批次 {i//batch_size + 1} 时出错: {str(e)}")
                    continue
            
            return all_data
    
    def _json_serializer(self, obj):
        """JSON序列化辅助方法，处理特殊类型"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    def wait_for_completion(self, asin_list, check_interval=3):
        """智能等待处理完成
        
        Args:
            asin_list (list): ASIN列表
            check_interval (int): 检查间隔
            
        Returns:
            dict: 等待结果
        """
        # 动态计算等待时间：30s * ASIN数量 + 20s
        asin_count = len(asin_list)
        max_wait = 30 * asin_count + 20
        
        print(f"⏳ 智能等待处理完成")
        print(f"   ASIN数量: {asin_count}")
        print(f"   计算等待时间: 30s × {asin_count} + 20s = {max_wait}秒")
        print(f"   检查间隔: {check_interval}秒")
        
        start_time = time.time()
        check_count = 0
        
        while time.time() - start_time < max_wait:
            check_count += 1
            print(f"\n🔍 第{check_count}次检查...")
            
            # 检查状态
            result = self.verify_all(asin_list, db_timeout=30, oss_timeout=30)
            
            if result['success']:
                elapsed = time.time() - start_time
                print(f"🎉 处理完成! 耗时: {elapsed:.1f}秒")
                
                # 自动导出ASIN数据
                print(f"\n📤 开始自动导出数据...")
                export_result = self.export_asin_data(asin_list)
                
                return {
                    'success': True,
                    'completed': True,
                    'duration': elapsed,
                    'checks': check_count,
                    'result': result,
                    'export': export_result
                }
            
            # 等待下次检查
            remaining = max_wait - (time.time() - start_time)
            if remaining > check_interval:
                print(f"⏱️  {check_interval}秒后再次检查...")
                time.sleep(check_interval)
            else:
                break
        
        elapsed = time.time() - start_time
        print(f"⏰ 等待超时 ({elapsed:.1f}秒)")
        return {
            'success': False,
            'completed': False,
            'duration': elapsed,
            'checks': check_count,
            'message': '等待超时'
        } 
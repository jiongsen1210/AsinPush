#!/usr/bin/env python3
"""
ASIN数据推送到Redis工具 - 优化版本

功能：
1. 将ASIN数据文件推送到Redis
2. 支持结果验证
3. 支持智能等待爬虫完成
4. 支持数据验证成功后自动导出到JSON文件
5. 支持手动导出ASIN数据到JSON文件

使用方法：
    python asin_to_redis_optimized.py push -f <文件路径>           # 基础推送
    python asin_to_redis_optimized.py push -f <文件路径> --wait   # 推送并智能等待完成(时间自动计算+自动导出)  
    python asin_to_redis_optimized.py verify -f <文件路径>        # 验证结果
    python asin_to_redis_optimized.py export -f <文件路径>        # 导出ASIN数据到JSON
    python asin_to_redis_optimized.py test                        # 测试连接

作者：优化版本
"""

import argparse
import sys
import os
from asin_pusher import ASINPusher
from result_verifier import ResultVerifier


def cmd_push(args):
    """推送命令"""
    print("🚀 ASIN数据推送任务")
    print("=" * 50)
    
    # 验证文件路径
    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        return False
    
    # 确认推送
    if not args.yes:
        confirm = input(f"确认推送文件 {args.file} 到Redis？(y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("❌ 用户取消操作")
            return False
    
    try:
        # 执行推送
        pusher = ASINPusher()
        result = pusher.run(args.file)
        
        if not result['success']:
            print(f"❌ 推送失败: {result['message']}")
            return False
        
        # 如果需要等待验证
        if args.wait:
            print("\n" + "⏳ 开始智能等待...")
            print("💡 爬虫通常需要20秒完成，程序将实时监控")
            
            # 从推送结果中提取ASIN数据
            asin_data = pusher.read_asin_file(args.file)
            asin_list = [f"{item['site']}@{item['asin']}" for item in asin_data]
            
            # 智能等待
            verifier = ResultVerifier()
            wait_result = verifier.wait_for_completion(
                asin_list, 
                check_interval=args.check_interval
            )
            
            if wait_result['completed']:
                print("\n🎉 任务完全完成!")
                return True
            else:
                print(f"\n⚠️  等待超时，但爬虫可能仍在运行")
                print(f"💡 建议稍后运行: python {sys.argv[0]} verify -f {args.file}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 推送过程出错: {e}")
        return False


def cmd_verify(args):
    """验证命令"""
    print("🔍 ASIN处理结果验证")
    print("=" * 50)
    
    # 验证文件路径
    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        return False
    
    try:
        # 读取ASIN数据
        pusher = ASINPusher()
        asin_data = pusher.read_asin_file(args.file)
        asin_list = [f"{item['site']}@{item['asin']}" for item in asin_data]
        
        # 执行验证
        verifier = ResultVerifier()
        result = verifier.verify_all(
            asin_list,
            db_timeout=args.db_timeout,
            oss_timeout=args.oss_timeout
        )
        
        if result['success']:
            print("\n🎉 所有ASIN验证成功!")
            return True
        else:
            print("\n⚠️  部分ASIN验证失败")
            return False
            
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        return False


def cmd_test(args):
    """测试连接命令"""
    print("🧪 连接测试")
    print("=" * 30)
    
    try:
        pusher = ASINPusher()
        success = pusher.test_connection()
        
        if success:
            print("✅ 所有连接正常!")
            return True
        else:
            print("❌ 连接测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        return False


def cmd_export(args):
    """导出ASIN数据命令"""
    print("📥 ASIN数据导出任务")
    print("=" * 50)
    
    # 验证文件路径
    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        return False
    
    try:
        # 读取ASIN数据
        pusher = ASINPusher()
        asin_data = pusher.read_asin_file(args.file)
        asin_list = [f"{item['site']}@{item['asin']}" for item in asin_data]
        
        # 导出数据
        verifier = ResultVerifier()
        export_result = verifier.export_asin_data(asin_list)
        
        if export_result['success']:
            print(f"\n🎯 导出任务完成!")
            return True
        else:
            print(f"\n❌ 导出失败: {export_result.get('message', '未知错误')}")
            return False
        
    except Exception as e:
        print(f"❌ 导出过程出错: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='ASIN数据推送到Redis工具 - 优化版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s push -f asin.txt                    # 基础推送
  %(prog)s push -f asin.txt --wait -y          # 推送并智能等待完成(时间自动计算+自动导出)
  %(prog)s push -f asin.txt --wait --check-interval 5  # 自定义检查间隔
  %(prog)s verify -f asin.txt                  # 验证结果
  %(prog)s export -f asin.txt                  # 手动导出ASIN数据到JSON
  %(prog)s test                                # 测试连接
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 推送命令
    push_parser = subparsers.add_parser('push', help='推送ASIN数据到Redis')
    push_parser.add_argument('-f', '--file', required=True, help='ASIN文件路径')
    push_parser.add_argument('-y', '--yes', action='store_true', help='自动确认')
    push_parser.add_argument('--wait', action='store_true', help='推送后智能等待完成(等待时间自动计算: 30s×ASIN数量+20s)')
    push_parser.add_argument('--check-interval', type=int, default=3, help='检查间隔(秒)')
    
    # 验证命令
    verify_parser = subparsers.add_parser('verify', help='验证ASIN处理结果')
    verify_parser.add_argument('-f', '--file', required=True, help='ASIN文件路径')
    verify_parser.add_argument('--db-timeout', type=int, default=300, help='数据库超时(秒)')
    verify_parser.add_argument('--oss-timeout', type=int, default=300, help='OSS超时(秒)')
    
    # 导出命令
    export_parser = subparsers.add_parser('export', help='导出ASIN数据到JSON文件')
    export_parser.add_argument('-f', '--file', required=True, help='ASIN文件路径')
    
    # 测试命令
    test_parser = subparsers.add_parser('test', help='测试连接')
    
    # 解析参数
    args = parser.parse_args()
    
    # 检查是否提供了命令
    if not args.command:
        parser.print_help()
        return
    
    # 执行对应命令
    if args.command == 'push':
        success = cmd_push(args)
    elif args.command == 'verify':
        success = cmd_verify(args)
    elif args.command == 'export':
        success = cmd_export(args)
    elif args.command == 'test':
        success = cmd_test(args)
    else:
        parser.print_help()
        return
    
    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 
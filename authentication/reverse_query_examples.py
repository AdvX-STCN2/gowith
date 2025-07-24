# 反向查询和地址去重示例
# 展示如何查询某个地方的所有人，以及如何避免重复地址存储

from django.contrib.auth import get_user_model
from authentication.models import Address, UserProfile
from django.db.models import Count, Q

User = get_user_model()

def create_users_with_optimized_address():
    """创建用户时避免重复地址存储的示例"""
    
    # 创建用户
    user1 = User.objects.create_user(username='user1', email='user1@example.com')
    user2 = User.objects.create_user(username='user2', email='user2@example.com')
    user3 = User.objects.create_user(username='user3', email='user3@example.com')
    
    # 地址数据
    beijing_chaoyang = {
        'country': '中国',
        'province': '北京市',
        'city': '北京市',
        'district': '朝阳区',
        'latitude': 39.9042,
        'longitude': 116.4074
    }
    
    # 使用create_with_address方法创建用户档案
    # 这会自动处理地址去重
    profile1, address1, created1 = UserProfile.create_with_address(
        user=user1,
        address_data=beijing_chaoyang,
        mbti='ENFP',
        name='张三',
        birthday='1990-01-01',
        sex='男',
        phone='13800138001',
        email='zhangsan@example.com'
    )
    
    # 第二个用户使用相同地址（会复用已存在的地址）
    profile2, address2, created2 = UserProfile.create_with_address(
        user=user2,
        address_data=beijing_chaoyang,  # 相同的地址数据
        mbti='INFJ',
        name='李四',
        birthday='1992-05-15',
        sex='女',
        phone='13800138002',
        email='lisi@example.com'
    )
    
    # 第三个用户使用不同地址
    shanghai_pudong = {
        'country': '中国',
        'province': '上海市',
        'city': '上海市',
        'district': '浦东新区'
    }
    
    profile3, address3, created3 = UserProfile.create_with_address(
        user=user3,
        address_data=shanghai_pudong,
        mbti='INTJ',
        name='王五',
        birthday='1988-12-20',
        sex='男',
        phone='13800138003',
        email='wangwu@example.com'
    )
    
    print(f"地址1创建状态: {created1}, 地址2创建状态: {created2}, 地址3创建状态: {created3}")
    print(f"地址1和地址2是否相同: {address1.id == address2.id}")  # 应该是True
    print(f"数据库中的地址总数: {Address.objects.count()}")
    
    return profile1, profile2, profile3

def reverse_query_examples():
    """反向查询示例：查询某个地方的所有人"""
    
    print("=== 反向查询示例 ===")
    
    # 方法1: 通过Address模型的反向查询
    beijing_addresses = Address.objects.filter(
        province='北京市',
        city='北京市'
    )
    
    for address in beijing_addresses:
        users = address.get_users_in_this_location()
        print(f"地址: {address.get_location_display()}")
        print(f"用户数量: {address.get_users_count()}")
        for user_profile in users:
            print(f"  - {user_profile.name} ({user_profile.phone})")
        print()
    
    # 方法2: 使用Address类方法直接查询
    beijing_users = Address.get_users_by_location(
        country='中国',
        province='北京市',
        city='北京市'
    )
    
    print(f"北京市所有用户 ({beijing_users.count()}人):")
    for user_profile in beijing_users:
        print(f"  - {user_profile.name} - {user_profile.get_location_display()}")
    
    # 方法3: 使用UserProfile的便捷方法
    chaoyang_users = UserProfile.get_users_by_location(
        province='北京市',
        city='北京市',
        district='朝阳区'
    )
    
    print(f"\n朝阳区用户 ({chaoyang_users.count()}人):")
    for user_profile in chaoyang_users:
        print(f"  - {user_profile.name}")

def location_statistics_examples():
    """地点统计示例"""
    
    print("\n=== 地点统计示例 ===")
    
    # 获取所有地点的用户统计
    location_stats = Address.get_location_statistics()
    
    print("所有地点用户统计（按用户数量排序）:")
    for address in location_stats:
        print(f"  {address.get_location_display()}: {address.user_count}人")
    
    # 获取特定省份的统计
    beijing_stats = Address.get_location_statistics(province='北京市')
    
    print("\n北京市各区用户统计:")
    for address in beijing_stats:
        print(f"  {address.district or '未指定区'}: {address.user_count}人")

def advanced_query_examples():
    """高级查询示例"""
    
    print("\n=== 高级查询示例 ===")
    
    # 查询有坐标信息的地址
    addresses_with_coords = Address.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    print(f"有坐标信息的地址数量: {addresses_with_coords.count()}")
    
    # 查询用户数量最多的地址
    most_popular_address = Address.objects.annotate(
        user_count=Count('user_profiles')
    ).order_by('-user_count').first()
    
    if most_popular_address:
        print(f"用户最多的地址: {most_popular_address.get_location_display()} ({most_popular_address.user_count}人)")
    
    # 查询没有用户的地址（可能需要清理）
    empty_addresses = Address.objects.annotate(
        user_count=Count('user_profiles')
    ).filter(user_count=0)
    
    print(f"没有用户的地址数量: {empty_addresses.count()}")
    
    # 查询特定城市的用户，按区分组
    from django.db.models import Count
    
    beijing_by_district = UserProfile.objects.filter(
        address__province='北京市',
        address__city='北京市'
    ).values(
        'address__district'
    ).annotate(
        user_count=Count('id')
    ).order_by('-user_count')
    
    print("\n北京市各区用户分布:")
    for item in beijing_by_district:
        district = item['address__district'] or '未指定区'
        count = item['user_count']
        print(f"  {district}: {count}人")

def cleanup_duplicate_addresses():
    """清理重复地址的示例（谨慎使用）"""
    
    print("\n=== 地址清理示例 ===")
    
    # 查找可能重复的地址（基于位置信息）
    from django.db.models import Count
    
    duplicate_candidates = Address.objects.values(
        'country', 'province', 'city', 'district'
    ).annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    print(f"发现 {duplicate_candidates.count()} 组可能重复的地址")
    
    for candidate in duplicate_candidates:
        addresses = Address.objects.filter(
            country=candidate['country'],
            province=candidate['province'],
            city=candidate['city'],
            district=candidate['district']
        )
        
        print(f"位置: {candidate['province']} {candidate['city']} {candidate['district']}")
        print(f"  重复地址数量: {addresses.count()}")
        
        # 注意：实际清理需要谨慎处理用户关联
        # 这里只是展示如何识别重复

if __name__ == '__main__':
    # 注意：这些示例需要在Django环境中运行
    # 可以通过 pdm run python3 manage.py shell 进入Django shell后导入使用
    
    print("反向查询和地址去重示例")
    print("请在Django shell中运行以下函数:")
    print("1. create_users_with_optimized_address() - 创建用户避免重复地址")
    print("2. reverse_query_examples() - 反向查询示例")
    print("3. location_statistics_examples() - 地点统计")
    print("4. advanced_query_examples() - 高级查询")
    print("5. cleanup_duplicate_addresses() - 清理重复地址")
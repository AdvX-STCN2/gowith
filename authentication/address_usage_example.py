# 地址模型使用示例
# 这个文件展示了如何使用封装后的Address模型

from django.contrib.auth import get_user_model
from authentication.models import Address, UserProfile

User = get_user_model()

def create_user_with_address_example():
    """创建用户和地址的示例"""
    
    # 1. 创建地址对象
    address = Address.objects.create(
        country='中国',
        province='北京市',
        city='北京市',
        district='朝阳区',
        detailed_address='三里屯街道某某小区1号楼101室',
        latitude=39.9042,  # 北京纬度
        longitude=116.4074  # 北京经度
    )
    
    # 2. 创建用户
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com'
    )
    
    # 3. 创建用户档案并关联地址
    profile = UserProfile.objects.create(
        user=user,
        mbti='ENFP',
        name='张三',
        birthday='1990-01-01',
        sex='男',
        phone='13800138000',
        email='zhangsan@example.com',
        address=address
    )
    
    return profile

def find_same_city_users_example():
    """查找同城用户的示例"""
    
    # 假设我们有一个用户档案
    user_profile = UserProfile.objects.first()
    
    if user_profile and user_profile.address:
        # 查找同城用户
        same_city_users = UserProfile.get_same_city_users(user_profile)
        print(f"找到 {same_city_users.count()} 个同城用户")
        
        # 查找同区用户
        same_district_users = UserProfile.get_same_district_users(user_profile)
        print(f"找到 {same_district_users.count()} 个同区用户")
        
        # 显示用户位置信息
        print(f"当前用户位置: {user_profile.get_location_display()}")
        
        # 检查两个用户是否同城
        if same_city_users.exists():
            other_user = same_city_users.first()
            is_same_city = user_profile.is_same_city(other_user)
            print(f"与 {other_user.name} 是否同城: {is_same_city}")

def address_methods_example():
    """地址模型方法使用示例"""
    
    # 创建两个地址
    address1 = Address(
        country='中国',
        province='北京市',
        city='北京市',
        district='朝阳区'
    )
    
    address2 = Address(
        country='中国',
        province='北京市',
        city='北京市',
        district='海淀区'
    )
    
    # 测试地址方法
    print(f"地址1完整显示: {address1.get_full_address()}")
    print(f"地址1位置显示: {address1.get_location_display()}")
    
    print(f"两个地址是否同城: {address1.is_same_city(address2)}")
    print(f"两个地址是否同区: {address1.is_same_district(address2)}")

def query_optimization_example():
    """查询优化示例 - 利用数据库索引"""
    
    # 这些查询会利用我们在Address模型中定义的索引
    
    # 按城市查询 - 使用city索引
    beijing_addresses = Address.objects.filter(city='北京市')
    
    # 按省份和城市查询 - 使用province+city复合索引
    beijing_in_beijing = Address.objects.filter(
        province='北京市',
        city='北京市'
    )
    
    # 按城市和区查询 - 使用city+district复合索引
    chaoyang_in_beijing = Address.objects.filter(
        city='北京市',
        district='朝阳区'
    )
    
    # 查找同城用户档案 - 利用外键关联和索引
    beijing_users = UserProfile.objects.filter(
        address__province='北京市',
        address__city='北京市'
    ).select_related('address')  # 使用select_related优化查询
    
    print(f"北京用户数量: {beijing_users.count()}")

if __name__ == '__main__':
    # 注意：这些示例需要在Django环境中运行
    # 可以通过 pdm run python3 manage.py shell 进入Django shell后导入使用
    pass
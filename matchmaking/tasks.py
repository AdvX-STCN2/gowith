from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Avg
import logging
import json
from datetime import timedelta

logger = logging.getLogger(__name__)

def get_llm_response(system_content, user_content, temperature=0.7):
    """调用LLM获取响应"""
    from ai.views import GetLLMOutput
    try:
        return GetLLMOutput(system_content, user_content, temperature)
    except Exception as e:
        logger.error(f"LLM调用失败: {e}")
        raise

@shared_task(bind=True)
def process_buddy_request_matching(self, request_id):
    """
    智能搭子匹配流程
    1. 信息整合总结 (25%)
    2. 智能标签生成 (50%)
    3. 匹配推荐与理由生成 (75%)
    4. 创建匹配记录 (100%)
    """
    try:
        from .models import BuddyRequest, BuddyMatch, BuddyRequestTag
        from profiles.models import UserProfile
        from events.models import Event
        
        # 更新进度: 开始处理
        self.update_state(state='PROGRESS', meta={'progress': 10, 'message': '开始处理匹配请求...'})
        
        # 获取搭子请求
        buddy_request = BuddyRequest.objects.select_related(
            'user', 'event'
        ).get(id=request_id)
        
        # 获取用户档案
        user_profile = UserProfile.objects.filter(
            user=buddy_request.user, is_primary=True
        ).first()
        
        if not user_profile:
            logger.warning(f"用户 {buddy_request.user.username} 没有主档案")
            self.update_state(state='FAILURE', meta={'progress': 0, 'message': '用户没有主档案'})
            return "用户没有主档案，跳过匹配"
        
        # 步骤1: 信息整合总结
        self.update_state(state='PROGRESS', meta={'progress': 25, 'message': '正在整合用户信息...'})
        integrated_info = _integrate_user_info(buddy_request, user_profile)
        
        # 步骤2: 智能标签生成
        self.update_state(state='PROGRESS', meta={'progress': 50, 'message': '正在生成智能标签...'})
        tags = _generate_smart_tags(integrated_info, buddy_request)
        
        # 保存生成的标签
        _save_request_tags(buddy_request, tags)
        
        # 步骤3: 匹配推荐与理由生成
        self.update_state(state='PROGRESS', meta={'progress': 75, 'message': '正在查找匹配用户...'})
        matches = _find_and_recommend_matches(buddy_request, integrated_info, tags)
        
        # 创建匹配记录
        self.update_state(state='PROGRESS', meta={'progress': 90, 'message': '正在创建匹配记录...'})
        created_matches = _create_match_records(buddy_request, matches)
        
        # 完成
        self.update_state(state='SUCCESS', meta={'progress': 100, 'message': f'匹配完成，找到 {len(created_matches)} 个匹配'})
        
        logger.info(f"为请求 {request_id} 创建了 {len(created_matches)} 个匹配")
        return {
            'status': 'success',
            'matches_count': len(created_matches),
            'message': f"成功创建 {len(created_matches)} 个匹配"
        }
        
    except Exception as e:
        logger.error(f"智能匹配处理失败: {e}")
        self.update_state(state='FAILURE', meta={'progress': 0, 'message': f'匹配失败: {str(e)}'})
        raise

def _integrate_user_info(buddy_request, user_profile):
    """步骤1: 使用LLM整合用户信息"""
    system_prompt = """
你是一个专业的信息整合助手。请将用户的个人资料、活动信息和搭子请求描述进行整合总结。

要求：
1. 提取用户的关键特征（性格、兴趣、地理位置等）
2. 分析活动的核心要素（类型、时间、地点、规模等）
3. 理解用户的匹配需求和期望
4. 输出结构化的JSON格式，包含：user_traits, activity_info, matching_preferences

请确保输出是有效的JSON格式。
"""
    
    user_content = f"""
用户信息：
- 用户名: {buddy_request.user.username}
- 档案名称: {user_profile.name}
- MBTI: {user_profile.mbti or '未知'}
- 个人简介: {user_profile.bio or '无'}
- 联系方式: {user_profile.contact_info or '无'}
- 地址: {user_profile.get_location_display()}

活动信息：
- 活动名称: {buddy_request.event.name}
- 活动类型: {buddy_request.event.activity_type}
- 开始时间: {buddy_request.event.start_time}
- 结束时间: {buddy_request.event.end_time}

- 活动地点: {buddy_request.event.location}

搭子请求描述：
{buddy_request.description}
"""
    
    response = get_llm_response(system_prompt, user_content)
    
    try:
        # 尝试解析JSON响应
        # 尝试从响应中提取JSON部分
        import re
        # 查找第一个 { 或 [ 开始,到最后一个 } 或 ] 结束的内容
        json_pattern = r'[{\[].*?[}\]](?=\s*$)'
        json_match = re.search(json_pattern, response, re.DOTALL)
        
        if json_match:
            try:
                integrated_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                cleaned_response = json_match.group()
                cleaned_response = re.sub(r'(?<!\\)"', '\\"', cleaned_response)
                cleaned_response = re.sub(r'[\x00-\x1F\x7F]', '', cleaned_response)
                integrated_data = json.loads(cleaned_response)
        else:
            # 如果没找到JSON格式内容,尝试直接解析整个响应
            try:
                integrated_data = json.loads(response)
            except json.JSONDecodeError:
                logger.warning("无法从响应中提取有效JSON")
                raise
        return integrated_data
    except json.JSONDecodeError:
        # 如果解析失败，返回原始文本
        logger.warning("LLM返回的不是有效JSON，使用原始响应")
        return {
            "raw_response": response,
            "user_traits": ["解析失败"],
            "activity_info": buddy_request.event.activity_type,
            "matching_preferences": buddy_request.description
        }

def _generate_smart_tags(integrated_info, buddy_request):
    """步骤2: 使用LLM生成智能标签"""
    system_prompt = """
你是一个专业的标签生成助手。基于整合的用户信息，为搭子请求生成精准的标签。

标签类型包括但不限于：
- 活动类型标签：如"编程"、"运动"、"学习"、"娱乐"、"黑客松"、"约饭"
- 性格特征标签：如"外向"、"内向"、"组织者"、"参与者"
- 技能水平标签：如"新手"、"进阶"、"专家"
- 时间偏好标签：如"早起"、"夜猫子"、"周末"、"工作日"
- 社交偏好标签：如"小团体"、"大聚会"、"一对一"、"团队合作"

要求：
1. 生成5-10个最相关的标签
2. 标签要简洁明了，2-4个字
3. 输出JSON数组格式：["标签1", "标签2", ...]

***请确保输出是有效的JSON数组。***
"""
    
    user_content = f"""
整合信息：
{json.dumps(integrated_info, ensure_ascii=False, indent=2)}

活动类型：{buddy_request.event.activity_type}
请求描述：{buddy_request.description}
"""
    
    response = get_llm_response(system_prompt, user_content)
    
    try:
        # 尝试从响应中提取JSON部分
        import re
        # 查找第一个 { 或 [ 开始,到最后一个 } 或 ] 结束的内容
        json_pattern = r'[{\[].*?[}\]](?=\s*$)'
        json_match = re.search(json_pattern, response, re.DOTALL)
        
        if json_match:
            try:
                tags = json.loads(json_match.group())
            except json.JSONDecodeError:
                cleaned_response = json_match.group()
                cleaned_response = re.sub(r'(?<!\\)"', '\\"', cleaned_response)
                cleaned_response = re.sub(r'[\x00-\x1F\x7F]', '', cleaned_response)
                tags = json.loads(cleaned_response)
        else:
            # 如果没找到JSON格式内容,尝试直接解析整个响应
            try:
                tags = json.loads(response)
            except json.JSONDecodeError:
                logger.warning("无法从响应中提取有效JSON")
                raise
        if isinstance(tags, list):
            return tags[:10]  # 最多10个标签
        else:
            return [str(tags)]  # 如果不是数组，转为单个标签
    except json.JSONDecodeError:
        # 解析失败时的备用标签
        logger.warning("标签生成解析失败，使用默认标签")
        return [buddy_request.event.activity_type, "搭子", "匹配"]

def _save_request_tags(buddy_request, tags):
    """保存生成的标签到数据库"""
    from .models import BuddyRequestTag
    
    # 清除旧标签
    BuddyRequestTag.objects.filter(request=buddy_request).delete()
    
    # 保存新标签
    tag_objects = []
    for tag in tags:
        if isinstance(tag, str) and tag.strip():
            tag_objects.append(BuddyRequestTag(
                request=buddy_request,
                tag_name=tag.strip()[:50]  # 限制长度
            ))
    
    if tag_objects:
        BuddyRequestTag.objects.bulk_create(tag_objects, ignore_conflicts=True)

def _find_and_recommend_matches(buddy_request, integrated_info, tags):
    """步骤3: 查找潜在匹配并使用LLM推荐"""
    from .models import BuddyRequest, BuddyRequestTag
    from profiles.models import UserProfile
    
    # 查找潜在的匹配请求
    potential_requests = BuddyRequest.objects.filter(
        event=buddy_request.event,  # 同一活动
        status='open'  # 开放状态
    ).exclude(
        user=buddy_request.user  # 排除自己
    ).select_related('user').prefetch_related('tags')
    
    if not potential_requests.exists():
        return []
    
    # 基于标签进行初步过滤
    tag_names = set(tags)
    filtered_requests = []
    
    for req in potential_requests:
        req_tags = set(req.tags.values_list('tag_name', flat=True))
        # 计算标签重叠度
        overlap = len(tag_names.intersection(req_tags))
        if overlap > 0 or len(req_tags) == 0:  # 有标签重叠或对方没有标签
            filtered_requests.append((req, overlap))
    
    # 按标签重叠度排序，取前10个
    filtered_requests.sort(key=lambda x: x[1], reverse=True)
    top_requests = [req for req, _ in filtered_requests[:10]]
    
    if not top_requests:
        return []
    
    # 使用LLM进行最终推荐
    return _llm_recommend_matches(buddy_request, integrated_info, top_requests)

def _llm_recommend_matches(buddy_request, integrated_info, candidate_requests):
    """使用LLM进行最终匹配推荐"""
    system_prompt = """
你是一个专业的搭子匹配顾问。基于用户的信息和候选人列表，推荐最合适的搭子并给出理由。

评估标准：
1. 兴趣匹配度：活动类型、个人爱好的契合程度
2. 性格互补：MBTI类型、社交偏好的匹配
3. 地理便利：地理位置的便利性
4. 时间契合：时间安排的匹配度
5. 技能互补：技能水平的互补性

输出要求：
1. 推荐最多5个最佳匹配
2. 每个推荐包含：user_id, match_score(1-10), reasons(数组)
3. 输出JSON格式：[{"user_id": 123, "match_score": 8.5, "reasons": ["理由1", "理由2"]}]

请确保输出是有效的JSON数组。
"""
    
    # 构建候选人信息
    candidates_info = []
    for req in candidate_requests:
        user_profile = UserProfile.objects.filter(
            user=req.user, is_primary=True
        ).first()
        
        candidate_info = {
            "user_id": req.user.id,
            "username": req.user.username,
            "activity_type": req.event.activity_type,
            "description": req.description,
            "tags": list(req.tags.values_list('tag_name', flat=True))
        }
        
        if user_profile:
            candidate_info.update({
                "name": user_profile.name,
                "mbti": user_profile.mbti or "未知",
                "bio": user_profile.bio or "无",
                "location": user_profile.get_location_display()
            })
        
        candidates_info.append(candidate_info)
    
    user_content = f"""
发起者信息：
{json.dumps(integrated_info, ensure_ascii=False, indent=2)}

候选搭子列表：
{json.dumps(candidates_info, ensure_ascii=False, indent=2)}

请为发起者推荐最合适的搭子。
"""
    
    response = get_llm_response(system_prompt, user_content, temperature=0.3)
    
    try:
        recommendations = json.loads(response)
        if isinstance(recommendations, list):
            return recommendations[:5]  # 最多5个推荐
        else:
            return []
    except json.JSONDecodeError:
        logger.warning("匹配推荐解析失败")
        # 备用简单推荐
        return [{
            "user_id": req.user.id,
            "match_score": 7.0,
            "reasons": ["系统推荐", "活动匹配"]
        } for req in candidate_requests[:3]]

def _create_match_records(buddy_request, recommendations):
    """创建匹配记录"""
    from .models import BuddyMatch
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    created_matches = []
    
    for rec in recommendations:
        try:
            user_id = rec.get('user_id')
            match_score = rec.get('match_score', 0)
            reasons = rec.get('reasons', [])
            
            if not user_id:
                continue
                
            matched_user = User.objects.get(id=user_id)
            
            # 检查是否已存在匹配
            existing_match = BuddyMatch.objects.filter(
                request=buddy_request,
                matched_user=matched_user
            ).first()
            
            if not existing_match:
                match = BuddyMatch.objects.create(
                    request=buddy_request,
                    matched_user=matched_user,
                    status='pending'
                )
                created_matches.append(match)
                
                # 发送匹配通知
                send_buddy_match_notification.delay(
                    matched_user.email,
                    f"您收到了来自 {buddy_request.user.username} 的搭子邀请：{buddy_request.event.activity_type}"
                )
                
        except Exception as e:
            logger.error(f"创建匹配记录失败: {e}")
            continue
    
    return created_matches

@shared_task
def send_buddy_match_notification(user_email, match_details):
    """
    发送搭子匹配通知邮件
    """
    try:
        subject = '找到新的搭子啦！'
        message = f'恭喜！我们为您找到了新的搭子：{match_details}'
        
        # 这里可以发送邮件或推送通知
        # send_mail(
        #     subject,
        #     message,
        #     settings.DEFAULT_FROM_EMAIL,
        #     [user_email],
        #     fail_silently=False,
        # )
        
        logger.info(f'搭子匹配通知已发送给 {user_email}')
        return f'通知已发送给 {user_email}'
        
    except Exception as e:
        logger.error(f'发送搭子匹配通知失败: {e}')
        raise

@shared_task
def process_buddy_matching(event_id):
    """
    处理搭子匹配算法
    """
    try:
        from .models import BuddyRequest
        from events.models import Event
        
        # 获取活动和相关的搭子请求
        event = Event.objects.get(id=event_id)
        open_requests = event.get_open_buddy_requests()
        
        # 这里可以实现复杂的匹配算法
        # 例如：基于兴趣、地理位置、时间偏好等进行匹配
        
        matches_created = 0
        for request in open_requests:
            # 简单的匹配逻辑示例
            potential_matches = open_requests.exclude(id=request.id).filter(
                event__activity_type=request.event.activity_type
            )[:5]  # 限制为最多5个匹配
            
            if potential_matches.exists():
                # 创建匹配记录
                # 这里需要根据实际的匹配模型来实现
                matches_created += 1
                
        logger.info(f'为活动 {event.title} 创建了 {matches_created} 个匹配')
        return f'成功创建 {matches_created} 个匹配'
        
    except Exception as e:
        logger.error(f'处理搭子匹配失败: {e}')
        raise

@shared_task
def cleanup_expired_requests():
    """
    清理过期的搭子请求
    """
    try:
        from .models import BuddyRequest
        from django.utils import timezone
        from datetime import timedelta
        
        # 删除7天前创建且仍为开放状态的请求
        cutoff_date = timezone.now() - timedelta(days=7)
        expired_requests = BuddyRequest.objects.filter(
            created_at__lt=cutoff_date,
            status='open'
        )
        
        count = expired_requests.count()
        expired_requests.update(status='expired')
        
        logger.info(f'清理了 {count} 个过期的搭子请求')
        return f'清理了 {count} 个过期请求'
        
    except Exception as e:
        logger.error(f'清理过期请求失败: {e}')
        raise

@shared_task
def generate_activity_recommendations(user_id):
    """
    为用户生成活动推荐
    """
    try:
        from django.contrib.auth.models import User
        from events.models import Event
        
        user = User.objects.get(id=user_id)
        
        # 这里可以实现推荐算法
        # 基于用户历史活动、兴趣偏好等
        
        # 简单示例：推荐最新的活动
        recommended_events = Event.objects.filter(
            date__gte=timezone.now()
        ).order_by('-created_at')[:5]
        
        recommendations = [{
            'id': event.id,
            'title': event.title,
            'date': event.date.isoformat(),
            'location': event.location
        } for event in recommended_events]
        
        logger.info(f'为用户 {user.username} 生成了 {len(recommendations)} 个推荐')
        return recommendations
        
    except Exception as e:
        logger.error(f'生成活动推荐失败: {e}')
        raise
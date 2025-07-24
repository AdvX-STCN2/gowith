from django.test import TestCase
from ai.views import GetLLMOutput
import time
from unittest.mock import patch, MagicMock

# Create your tests here.

class GetLLMOutputTest(TestCase):
    
    def test_get_llm_output_basic(self):
        """测试基本的LLM输出功能"""
        start_time = time.time()
        system_content = "你是一个专业的翻译员，你只需要将用户给出的任何文字，翻译成中文，不需要任何解释"
        user_content = "你好，我是张三"
        output = GetLLMOutput(system_content, user_content)
        print(output)
        end_time = time.time()
        print(f"耗时：{end_time - start_time}秒")
        
        # 断言输出不为空
        self.assertIsNotNone(output)
        self.assertIsInstance(output, str)
        self.assertGreater(len(output), 0)
    
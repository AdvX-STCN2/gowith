from django.test import TestCase
from .views import GetLLMOutput

# Create your tests here.

class GetLLMOutputTest(TestCase):
    def test_get_llm_output(self):
        system_content = "你是一个专业的翻译员"
        user_content = "你好"
        output = GetLLMOutput(system_content,user_content)
        self.assertIsNotNone(output)


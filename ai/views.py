import time
from django.shortcuts import render
from openai import OpenAI
from decouple import config

# Create your views here.


def GetLLMOutput(system_content,user_content,temperature=1):
    """
    获取LLM输出
    :param system_content: 系统提示词
    :param user_content: 用户输入
    :param temperature: 温度
    :return: LLM输出
    """
    client = OpenAI(
        base_url="https://api.ppinfra.com/v3/openai",
        api_key=config("PIPO_TOKEN"),
    )
    result = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        temperature=temperature,
    )
    return result.choices[0].message.content

if __name__ == '__main__':
    start_time=time.time()
    system_content = "你是一个专业的翻译员，你只需要将用户给出的任何文字，翻译成中文，不需要任何解释"
    user_content = "你好，我是张三"
    output = GetLLMOutput(system_content,user_content)
    print(output)
    end_time=time.time()
    print("耗时：",end_time-start_time)
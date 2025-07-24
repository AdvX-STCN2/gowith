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


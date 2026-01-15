"""
LLM客户端模块
使用Azure OpenAI接口调用GPT-4o
"""

import os
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """GPT-4o客户端"""

    def __init__(self):
        self.base_url = os.getenv("AZURE_OPENAI_ENDPOINT", "https://search-va.byteintl.net/gpt/openapi/online/v2/crawl")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-03-01-preview")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "AZURE_OPENAI_API_KEY environment variable is not set. "
                "Please set it or create a .env file with your API key."
            )

        self.model_name = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-2024-11-20")
        self.max_tokens = int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "4096"))
        
        self.client = openai.AzureOpenAI(
            azure_endpoint=self.base_url,
            api_version=self.api_version,
            api_key=self.api_key,
        )
        
    @retry(wait=wait_random_exponential(min=1, max=5), stop=stop_after_attempt(3))
    def call(self, prompt: str, temperature: float = 0) -> str:
        """
        调用GPT-4o API
        
        Args:
            prompt: 输入提示词
            temperature: 温度参数，默认0
            
        Returns:
            模型返回的文本内容
        """
        try:
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=temperature,
                extra_headers={"X-TT-LOGID": "${your_logid}"},
            )
            
            content = completion.choices[0].message.content or ""
            logger.info(f"LLM调用成功，返回长度: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            raise


# 提供便捷的调用函数
@retry(wait=wait_random_exponential(min=1, max=5), stop=stop_after_attempt(3))
def call_gpt4o_text(prompt: str) -> str:
    """
    便捷的GPT-4o调用函数

    Args:
        prompt: 输入提示词

    Returns:
        模型返回的文本内容
    """
    base_url = os.getenv("AZURE_OPENAI_ENDPOINT", "https://search-va.byteintl.net/gpt/openapi/online/v2/crawl")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-03-01-preview")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "AZURE_OPENAI_API_KEY environment variable is not set. "
            "Please set it or create a .env file with your API key."
        )

    model_name = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-2024-11-20")
    max_tokens = int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "4096"))

    client = openai.AzureOpenAI(
        azure_endpoint=base_url,
        api_version=api_version,
        api_key=api_key,
    )
    
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0,
        extra_headers={"X-TT-LOGID": "${your_logid}"},
    )
    
    resp = completion
    content = resp.choices[0].message.content or ""
    return content




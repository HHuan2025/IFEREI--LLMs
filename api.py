
import json
import re
from openai import OpenAI
from config import logger, API_CONFIG, CURRENT_API, OPENAI_API_KEY, OPENAI_API_BASE



def configure_api():
    """配置 API"""
    if CURRENT_API == 'openai':
        if not OPENAI_API_KEY:
            logger.error("未设置OPENAI_API_KEY环境变量")
            return None

        # 使用新版本 SDK 的配置方式，移除 model 参数
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
        return client
    else:
        raise ValueError(f"不支持的API类型: {CURRENT_API}")


def fix_json_format(text):
    """修复和验证JSON格式
    
    Args:
        text (str): 需要修复的文本
        
    Returns:
        str: 修复后的JSON字符串
    """
    try:
        # 尝试直接解析
        json.loads(text)
        return text
    except json.JSONDecodeError:
        # 如果解析失败，尝试修复
        try:
            # 1. 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                json_str = json_match.group(0)
            else:
                return None

            # 2. 修复常见的格式问题
            # 修复单引号
            json_str = json_str.replace("'", '"')
            
            # 修复缺少引号的键
            json_str = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str)
            
            # 修复多余的逗号
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            # 3. 验证修复后的JSON
            json.loads(json_str)
            return json_str
        except Exception as e:
            logger.error(f"JSON格式修复失败: {str(e)}")
            return None

def call_openai_api(prompt):
    """调用 API"""
    try:
        client = configure_api()
        if not client:
            return None

        if CURRENT_API == 'openai':
            # 使用新的API格式调用
            response = client.chat.completions.create(
                model="GLM-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的实体关系抽取助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4096,
                stream=False
            )
            response_text = response.choices[0].message.content.strip()
        else:
            raise ValueError(f"不支持的API类型: {CURRENT_API}")
        
        # 修复和验证JSON格式
        fixed_json = fix_json_format(response_text)
        if fixed_json:
            return fixed_json
        else:
            logger.error("API返回结果无法转换为有效的JSON格式")
            return None
    except Exception as e:
        logger.error(f"API 调用失败: {str(e)}")
        return None 
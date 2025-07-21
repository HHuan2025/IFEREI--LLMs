import json
from config import logger


def build_simple_extraction_prompt(text):
    """构建简单的实体和关系抽取的 Prompt，不包含类型更新

    Args:
        text (str): 需要处理的文本

    Returns:
        str: 构建的 prompt
    """
    prompt = f"""你是一名数据标注专家，擅长从药用植物文本中识别规范化的实体与其之间的语义关系。
请对以下文本进行处理，并只返回符合上述格式的JSON结果：
{text}

重要：你必须严格按照以下示例JSON格式输出，不要添加任何其他内容，不要有任何解释性文字：
{{
  "entities": [
    {{"entity": "一叶萩", "type": "药用植物"}},
    {{"entity": "大戟科", "type": "科"}}
  ],
  "relationships": [
    {{"head": "一叶萩", "predicate": "属于科", "tail": "大戟科"}},
    {{"head": "一叶萩", "predicate": "属于属", "tail": "黑面神属"}}
  ]
}}"""
    return prompt


def build_extraction_prompt(text, entity_file, relation_file):
    """
    构建实体和关系抽取的 Prompt，包含类型更新

    Args:
        text (str): 需要处理的文本
        entity_file (str): 实体类型文件路径
        relation_file (str): 关系类型文件路径

    Returns:
        str: 构建的 prompt
    """
    try:
        with open(entity_file, 'r', encoding='utf-8') as f:
            entity_types = [line.strip() for line in f if line.strip()]
        with open(relation_file, 'r', encoding='utf-8') as f:
            relation_types = [line.strip() for line in f if line.strip()]

        entity_type_str = "、".join(entity_types)
        relation_type_str = "、".join(relation_types)

        prompt = f"""你是药用植物领域和自然语言处理的专家，擅长从药用植物文本中提取实体及其关系。
你的任务分为两个阶段，请依次执行：
阶段1：从文本中识别出所有语义明确的实体，并标注其对应的实体类型。实体类型可参考但不限于以下列表：{entity_type_str}。
阶段2：在阶段1提取的实体对中，识别其间存在的语义关系，关系类型可参考但不限于以下列表：{relation_type_str}。
请对以下文本进行处理，并只返回符合上述格式的JSON结果：
请严格按照以下 JSON 格式输出，不能有任何额外解释性文字：
{{
  "entities": [
    {{"entity": "一叶萩", "type": "药用植物"}},
    {{"entity": "大戟科", "type": "科"}}
  ],
  "relationships": [
    {{"head": "一叶萩", "predicate": "属于科", "tail": "大戟科"}},
    {{"head": "一叶萩", "predicate": "属于属", "tail": "黑面神属"}}
  ]
}}

输入文本：
{text}"""
        return prompt
    except Exception as e:
        logger.error(f"构建抽取 Prompt 失败: {str(e)}")
        return None


def build_validation_prompt(text, extracted_json, entity_file, relation_file):
    """构建验证 Prompt
    Args:
        text (str): 原始文本
        extracted_json (dict): 抽取结果
        entity_file (str): 实体类型文件路径
        relation_file (str): 关系类型文件路径

    Returns:
        str: 构建的 prompt
    """
    try:
        with open(entity_file, 'r', encoding='utf-8') as f:
            entity_types = [line.strip() for line in f if line.strip()]
        with open(relation_file, 'r', encoding='utf-8') as f:
            relation_types = [line.strip() for line in f if line.strip()]

        entity_type_str = "、".join(entity_types)
        relation_type_str = "、".join(relation_types)

        prompt = f"""你是一名数据标注专家，擅长校对与审阅不恰当的标注结果。
你的任务为三个阶段，请依次执行：阶段1：实体类型归一—对比抽取结果中的实体类型与提供的 {entity_type_str}，识别语义重复或粒度不一致的类型，进行归一化映射；
阶段2：关系类型归—对比抽取结果中的关系类型与提供的 {relation_type_str}，识别语义重复或模糊的关系标签，进行归一化映射。
阶段3：输出优化后的标准实体关系类型集合和被合并的实体关系类型映射。
如果没有要消歧的实体关系，则返回空字符串。
请严格按照以下 JSON 格式输出，不能有任何额外解释性文字：
{{
  "standard entity type list": ["type a", "type b", ...],
  "standard relation type list": ["relation 1", "relation 2", ...],
  "merged entity type mapping": {"original type 1": "standard type a", "original type 2": "standard type a", ... },
  "merged relation mapping": {"original relation 1": "standard relation 1", "original relation 2": "standard relation 1", ... }
}}
当前抽取结果：
{json.dumps(extracted_json, ensure_ascii=False, indent=2)}
"""
        return prompt
    except Exception as e:
        logger.error(f"构建验证 Prompt 失败: {str(e)}")
        return None


def build_strict_extraction_prompt(text, entity_file, relation_file):
    """构建严格模式下的抽取 Prompt，只允许使用已收敛的实体和关系类型

    Args:
        text (str): 需要处理的文本
        entity_file (str): 实体类型文件路径
        relation_file (str): 关系类型文件路径

    Returns:
        str: 构建的 prompt
    """
    try:
        with open(entity_file, 'r', encoding='utf-8') as f:
            entity_types = [line.strip() for line in f if line.strip()]
        with open(relation_file, 'r', encoding='utf-8') as f:
            relation_types = [line.strip() for line in f if line.strip()]

        entity_type_str = "、".join(entity_types)
        relation_type_str = "、".join(relation_types)

        prompt = f"""你是一名数据标注专家，擅长从药用植物文本中识别规范化的实体与其之间的语义关系。
你的分为两个阶段，请依次执行：阶段1：提取文本中的所有实体，实体类型仅限于以下列表：
分为两个阶段，请依次执行：阶段1：提取文本中的所有实体，实体类型仅限于以下列表：{entity_type_str},每个实体需包含其文本内容及对应类型。
阶段2：在阶段一提取的实体中，识别其间存在的语义关系，关系类型仅限于以下列表：{relation_type_str}。
请对以下文本进行处理，并只返回符合上述格式的JSON结果：
请严格按照以下 JSON 格式输出，不能有任何额外解释性文字：{{
  "entities": [
    {"entity": "XXX", "type": "XXX" },
    ...
  ],
  "relations": [
    {"head": "XXX", "relation": "XXX" ,"tail": "XXX", },
    ...
  ]
}}
输入文本：
{text}
"""
        return prompt
    except Exception as e:
        logger.error(f"构建严格模式 Prompt 失败: {str(e)}")
        return None 
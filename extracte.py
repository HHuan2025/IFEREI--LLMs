import os

import json
from datetime import datetime
import logging
from collections import deque

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置 Gemini API
genai.configure(
    api_key='sk-Q3DNDI46zCqi4ry1lsUH8Ow0m1WkahiGLlPpJg3Rta4VJVcY',
    transport="rest",
    client_options={"api_endpoint": "https://api.openai-proxy.org/google"},
)

# Jaccard 系数收敛参数
JACCARD_THRESHOLD = 0.95  # Jaccard 系数阈值
CONVERGENCE_ROUNDS = 3  # 连续收敛轮数
entity_jaccard_history = deque(maxlen=CONVERGENCE_ROUNDS)
relation_jaccard_history = deque(maxlen=CONVERGENCE_ROUNDS)


def call_openai_api(prompt):
    """调用 Gemini API"""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"API 调用失败: {str(e)}")
        return None


def build_extraction_prompt(text, entity_file, relation_file):
    """构建实体和关系抽取的 Prompt"""
    try:
        with open(entity_file, 'r', encoding='utf-8') as f:
            entity_types = [line.strip() for line in f if line.strip()]
        with open(relation_file, 'r', encoding='utf-8') as f:
            relation_types = [line.strip() for line in f if line.strip()]

        entity_type_str = "、".join(entity_types)
        relation_type_str = "、".join(relation_types)

        prompt = f"""你是药用植物领域和自然语言处理的专家，擅长从药用植物文本中提取实体及其关系。请根据下列要求完成任务：

1. 实体提取：从给定文本中提取所有实体，并标注实体类型。实体类型包括但不限于：{entity_type_str}。
2. 关系抽取：抽取这些实体之间的语义关系，常见关系类型包括：{relation_type_str}。
3. 输出格式参考如下（JSON 格式）：
{{
  "entities": [
    {{
      "entity": "一叶萩",
      "type": "药用植物"
    }}
  ],
  "relationships": [
    {{
      "head": "一叶萩",
      "predicate": "主治症状",
      "tail": "风湿腰痛"
    }}
  ]
}}

请对以下文本进行处理并返回符合上述格式的 JSON 结果：
文本：{text}
"""
        return prompt
    except Exception as e:
        logger.error(f"构建抽取 Prompt 失败: {str(e)}")
        return None


def build_validation_prompt(text, extracted_result, entity_file, relation_file):
    """构建验证实体和关系的 Prompt，包含实体类型和关系类型的参考"""
    try:
        with open(entity_file, 'r', encoding='utf-8') as f:
            entity_types = [line.strip() for line in f if line.strip()]
        with open(relation_file, 'r', encoding='utf-8') as f:
            relation_types = [line.strip() for line in f if line.strip()]

        entity_type_str = "、".join(entity_types)
        relation_type_str = "、".join(relation_types)

        prompt = f"""你是一名专业的数据标注员，负责校对实体和关系的标注结果。请仔细检查以下标注结果是否存在不恰当或错误的地方，并返回修正后的 JSON 结果。如果结果正确，请保持不变。

输入文本：
{text}

实体关系信息：
{json.dumps(extracted_result, ensure_ascii=False, indent=2)}

参考信息：
1. 允许的实体类型：{entity_type_str}
2. 允许的关系类型：{relation_type_str}

要求：
1. 确保实体类型与文本内容、上下文以及参考的实体类型列表一致
2. 验证关系中的 head 和 tail 必须是已识别的实体
3. 检查关系的 predicate 是否合理且在参考的关系类型列表中
4. 返回修正后的 JSON 格式结果，与原始格式保持一致

返回格式：
{{
  "entities": [
    {{
      "entity": "",
      "type": ""
    }}
  ],
  "relationships": [
    {{
      "head": "",
      "predicate": "",
      "tail": ""
    }}
  ]
}}
"""
        return prompt
    except Exception as e:
        logger.error(f"构建验证 Prompt 失败: {str(e)}")
        return None


def calculate_jaccard(set1, set2):
    """计算两个集合的 Jaccard 系数"""
    if not set1 and not set2:
        return 1.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def update_type_files(validated_json, entity_file, relation_file):
    """从验证结果中提取实体类型和关系类型，更新类型文件并计算 Jaccard 系数"""
    try:
        # 读取现有类型
        existing_entity_types = set()
        existing_relation_types = set()

        if os.path.exists(entity_file):
            with open(entity_file, 'r', encoding='utf-8') as f:
                existing_entity_types = set(line.strip() for line in f if line.strip())

        if os.path.exists(relation_file):
            with open(relation_file, 'r', encoding='utf-8') as f:
                existing_relation_types = set(line.strip() for line in f if line.strip())

        # 提取当前抽取的类型
        current_entity_types = {entity["type"] for entity in validated_json.get("entities", [])}
        current_relation_types = {relation["predicate"] for relation in validated_json.get("relationships", [])}

        # 记录当前抽取的类型
        logger.info(f"当前抽取的实体类型: {current_entity_types}")
        logger.info(f"当前抽取的关系类型: {current_relation_types}")

        # 计算 Jaccard 系数
        entity_jaccard = calculate_jaccard(current_entity_types, existing_entity_types)
        relation_jaccard = calculate_jaccard(current_relation_types, existing_relation_types)
        logger.info(f"实体类型 Jaccard 系数: {entity_jaccard:.4f}")
        logger.info(f"关系类型 Jaccard 系数: {relation_jaccard:.4f}")

        # 更新 Jaccard 历史
        entity_jaccard_history.append(entity_jaccard)
        relation_jaccard_history.append(relation_jaccard)

        # 合并类型
        updated_entity_types = existing_entity_types | current_entity_types
        updated_relation_types = existing_relation_types | current_relation_types

        # 更新实体类型文件
        with open(entity_file, 'w', encoding='utf-8') as f:
            for entity_type in sorted(updated_entity_types):
                f.write(f"{entity_type}\n")
        logger.info(f"更新实体类型文件: {entity_file}")

        # 更新关系类型文件
        with open(relation_file, 'w', encoding='utf-8') as f:
            for relation_type in sorted(updated_relation_types):
                f.write(f"{relation_type}\n")
        logger.info(f"更新关系类型文件: {relation_file}")

        return entity_jaccard, relation_jaccard
    except Exception as e:
        logger.error(f"更新类型文件失败: {str(e)}")
        return None, None


def save_results(result, input_file, output_dir, timestamp):
    """保存处理结果到专用文件夹"""
    try:
        result_dir = os.path.join(output_dir, f"results_{timestamp}")
        os.makedirs(result_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(result_dir, f"{base_name}_result.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"结果保存至: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"保存结果失败: {str(e)}")
        return None


def save_conversation_log(prompt, response, output_dir, timestamp, filename, stage):
    """保存每次对话的 Prompt 和 Response"""
    try:
        log_dir = os.path.join(output_dir, f"conversation_logs_{timestamp}")
        os.makedirs(log_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(filename))[0]
        log_file = os.path.join(log_dir, f"{base_name}_{stage}_conversation.json")

        conversation = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input_file": filename,
            "stage": stage,  # 区分抽取和验证
            "prompt": prompt,
            "response": response
        }

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(conversation, f, ensure_ascii=False, indent=2)
        logger.info(f"对话日志保存至: {log_file}")
    except Exception as e:
        logger.error(f"保存对话日志失败: {str(e)}")


def check_convergence():
    """检查 Jaccard 系数是否连续 X 轮达到阈值"""
    if len(entity_jaccard_history) < CONVERGENCE_ROUNDS or len(relation_jaccard_history) < CONVERGENCE_ROUNDS:
        return False
    return all(j >= JACCARD_THRESHOLD for j in entity_jaccard_history) and \
        all(j >= JACCARD_THRESHOLD for j in relation_jaccard_history)


def process_directory(input_dir, entity_file, relation_file, output_dir):
    """处理输入目录中的所有 txt 文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not os.path.exists(input_dir):
        logger.error(f"输入目录 {input_dir} 不存在")
        return

    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(input_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read().strip()

                logger.info(f"正在处理文件: {filename}")

                # 抽取步骤
                extraction_prompt = build_extraction_prompt(text, entity_file, relation_file)
                if not extraction_prompt:
                    continue

                extracted_result = call_openai_api(extraction_prompt)
                if not extracted_result:
                    continue

                try:
                    extracted_json = json.loads(extracted_result)
                except json.JSONDecodeError:
                    logger.error(f"{filename} 的抽取结果 JSON 格式错误")
                    continue

                # 保存抽取对话日志
                save_conversation_log(extraction_prompt, extracted_result, output_dir, timestamp, filename,
                                      "extraction")

                # 检查是否需要验证
                if check_convergence():
                    logger.info(f"类型文件已收敛，跳过验证步骤: {filename}")
                    validated_json = extracted_json
                else:
                    # 验证步骤
                    validation_prompt = build_validation_prompt(text, extracted_json, entity_file, relation_file)
                    if not validation_prompt:
                        continue

                    validated_result = call_openai_api(validation_prompt)
                    if not validated_result:
                        continue

                    try:
                        validated_json = json.loads(validated_result)
                    except json.JSONDecodeError:
                        logger.error(f"{filename} 的验证结果 JSON 格式错误")
                        continue

                    # 保存验证对话日志
                    save_conversation_log(validation_prompt, validated_result, output_dir, timestamp, filename,
                                          "validation")

                # 更新实体类型和关系类型文件，并计算 Jaccard 系数
                entity_jaccard, relation_jaccard = update_type_files(validated_json, entity_file, relation_file)
                if entity_jaccard is None or relation_jaccard is None:
                    continue

                # 保存结果
                save_results(validated_json, file_path, output_dir, timestamp)

            except Exception as e:
                logger.error(f"处理文件 {filename} 出错: {str(e)}")


if __name__ == "__main__":
    input_dir = "input_texts"  # 包含输入 txt 文件的目录
    entity_file = "entity_types.txt"  # 实体类型文件
    relation_file = "relation_types.txt"  # 关系类型文件
    output_dir = "output_results"  # 输出结果目录

    process_directory(input_dir, entity_file, relation_file, output_dir)
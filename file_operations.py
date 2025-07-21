import os
import json
from datetime import datetime
from config import logger, entity_jaccard_history, relation_jaccard_history
from utils import calculate_jaccard

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
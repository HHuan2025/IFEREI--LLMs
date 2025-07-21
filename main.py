import os
import json
from datetime import datetime
import sys
import os
from sympy import false
from config import logger
from api import configure_api, call_openai_api
from prompt import build_extraction_prompt, build_validation_prompt, build_simple_extraction_prompt, \
    build_strict_extraction_prompt
from utils import check_convergence
from file_operations import update_type_files, save_results, save_conversation_log
from excel_utils import CSVRecorder


def process_simple_extraction(input_dir, output_dir, start_index=None, end_index=None):
    """简单抽取处理，不进行验证和类型更新

    Args:
        input_dir (str): 输入目录路径
        output_dir (str): 输出目录路径
        start_index (int, optional): 开始处理的文件索引（从0开始）. Defaults to None.
        end_index (int, optional): 结束处理的文件索引（不包含）. Defaults to None.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not os.path.exists(input_dir):
        logger.error(f"输入目录 {input_dir} 不存在")
        return

    os.makedirs(output_dir, exist_ok=True)

    # 获取所有txt文件
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]

    # 如果指定了范围，则只处理指定范围内的文件
    if start_index is not None or end_index is not None:
        start_idx = start_index if start_index is not None else 0
        end_idx = end_index if end_index is not None else len(txt_files)

        # 验证索引范围
        if start_idx < 0 or end_idx > len(txt_files) or start_idx >= end_idx:
            logger.error(f"无效的文件索引范围: start_index={start_idx}, end_index={end_idx}, 总文件数={len(txt_files)}")
            return

        txt_files = txt_files[start_idx:end_idx]
        logger.info(f"将处理从第 {start_idx + 1} 到第 {end_idx} 个文件，共 {len(txt_files)} 个文件")

    for filename in txt_files:
        file_path = os.path.join(input_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()

            logger.info(f"正在处理文件: {filename}")

            # 使用严格模式的prompt
            extraction_prompt = build_strict_extraction_prompt(text, CONFIG['entity_file'], CONFIG['relation_file'])
            if not extraction_prompt:
                continue

            extracted_result = call_openai_api(extraction_prompt)
            if not extracted_result:
                logger.error(f"{filename} API调用失败或返回结果无效")
                continue

            try:
                extracted_json = json.loads(extracted_result)
                logger.info(f"{filename} 成功解析JSON结果")
            except json.JSONDecodeError as e:
                logger.error(f"{filename} 的抽取结果 JSON 格式错误: {str(e)}")
                logger.error(f"原始结果: {extracted_result}")
                continue

            # 保存抽取对话日志
            save_conversation_log(extraction_prompt, extracted_result, output_dir, timestamp, filename,
                                  "extraction")

            # 保存结果
            save_results(extracted_json, file_path, output_dir, timestamp)

        except Exception as e:
            logger.error(f"处理文件 {filename} 出错: {str(e)}")


def process_directory(input_dir, entity_file, relation_file, output_dir, start_index=None, end_index=None,
                      enable_validation=True):
    """处理输入目录中的所有 txt 文件

    Args:
        input_dir (str): 输入目录路径
        entity_file (str): 实体类型文件路径
        relation_file (str): 关系类型文件路径
        output_dir (str): 输出目录路径
        start_index (int, optional): 开始处理的文件索引（从0开始）. Defaults to None.
        end_index (int, optional): 结束处理的文件索引（不包含）. Defaults to None.
        enable_validation (bool, optional): 是否启用验证步骤. Defaults to True.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 初始化CSV记录器
    csv_recorder = CSVRecorder()

    if not os.path.exists(input_dir):
        logger.error(f"输入目录 {input_dir} 不存在")
        return

    os.makedirs(output_dir, exist_ok=True)

    # 获取所有txt文件
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]

    # 如果指定了范围，则只处理指定范围内的文件
    if start_index is not None or end_index is not None:
        start_idx = start_index if start_index is not None else 0
        end_idx = end_index if end_index is not None else len(txt_files)

        # 验证索引范围
        if start_idx < 0 or end_idx > len(txt_files) or start_idx >= end_idx:
            logger.error(f"无效的文件索引范围: start_index={start_idx}, end_index={end_idx}, 总文件数={len(txt_files)}")
            return

        txt_files = txt_files[start_idx:end_idx]
        logger.info(f"将处理从第 {start_idx + 1} 到第 {end_idx} 个文件，共 {len(txt_files)} 个文件")

    for filename in txt_files:
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
                logger.error(f"{filename} API调用失败或返回结果无效")
                continue

            try:
                extracted_json = json.loads(extracted_result)
                logger.info(f"{filename} 成功解析JSON结果")
            except json.JSONDecodeError as e:
                logger.error(f"{filename} 的抽取结果 JSON 格式错误: {str(e)}")
                logger.error(f"原始结果: {extracted_result}")
                continue

            # 保存抽取对话日志
            save_conversation_log(extraction_prompt, extracted_result, output_dir, timestamp, filename,
                                  "extraction")

            # 检查是否需要验证
            if not enable_validation or check_convergence():
                logger.info(f"跳过验证步骤: {filename}")
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

            # 记录到CSV
            current_entity_types = {entity["type"] for entity in validated_json.get("entities", [])}
            current_relation_types = {relation["predicate"] for relation in validated_json.get("relationships", [])}

            csv_recorder.record_types(filename, current_entity_types, entity_jaccard,
                                      current_relation_types, relation_jaccard)

            # 保存结果
            save_results(validated_json, file_path, output_dir, timestamp)

        except Exception as e:
            logger.error(f"处理文件 {filename} 出错: {str(e)}")

    # 保存CSV记录
    csv_recorder.save()


def process_single_file(file_path, entity_file, relation_file, output_dir):
    """处理单个文件

    Args:
        file_path (str): 输入文件路径
        entity_file (str): 实体类型文件路径
        relation_file (str): 关系类型文件路径
        output_dir (str): 输出目录路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not os.path.exists(file_path):
        logger.error(f"输入文件 {file_path} 不存在")
        return

    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()

        filename = os.path.basename(file_path)
        logger.info(f"正在处理文件: {filename}")

        # 抽取步骤
        extraction_prompt = build_extraction_prompt(text, entity_file, relation_file)
        if not extraction_prompt:
            return

        extracted_result = call_openai_api(extraction_prompt)
        if not extracted_result:
            logger.error(f"{filename} API调用失败或返回结果无效")
            return

        try:
            extracted_json = json.loads(extracted_result)
            logger.info(f"{filename} 成功解析JSON结果")
        except json.JSONDecodeError as e:
            logger.error(f"{filename} 的抽取结果 JSON 格式错误: {str(e)}")
            logger.error(f"原始结果: {extracted_result}")
            return

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
                return

            validated_result = call_openai_api(validation_prompt)
            if not validated_result:
                return

            try:
                validated_json = json.loads(validated_result)
            except json.JSONDecodeError:
                logger.error(f"{filename} 的验证结果 JSON 格式错误")
                return

            # 保存验证对话日志
            save_conversation_log(validation_prompt, validated_result, output_dir, timestamp, filename,
                                  "validation")

        # 更新实体类型和关系类型文件，并计算 Jaccard 系数
        entity_jaccard, relation_jaccard = update_type_files(validated_json, entity_file, relation_file)
        if entity_jaccard is None or relation_jaccard is None:
            return

        # 保存结果
        save_results(validated_json, file_path, output_dir, timestamp)

    except Exception as e:
        logger.error(f"处理文件 {filename} 出错: {str(e)}")


# 配置参数
CONFIG = {
    'input_dir': "Data_llm",  # 输入目录路径
    'entity_file': "entity_types.txt",  # 实体类型文件路径
    'relation_file': "relation_types.txt",  # 关系类型文件路径
    'output_dir': "output_results",  # 输出目录路径
    'start_index': 0,  # 开始处理的文件索引（从0开始）
    'end_index': 107,  # 结束处理的文件索引（不包含）
    'single_file': None,  # 处理单个文件（如果指定，则忽略其他参数）
    'mode': 'normal',  # 处理模式：'normal' 或 'strict'
    'disable_validation': True  # 禁用验证步骤
}

# 在启动前判断收敛条件，若收敛则自动切换为严格模式
if __name__ == "__main__":

    # 配置API
    configure_api()

    # 检查收敛条件并设置模式
    if check_convergence():
        CONFIG['mode'] = 'strict'
        CONFIG['disable_validation'] = True
        print("收敛条件已满足，自动切换为严格模式（关闭验证，严格使用已收敛类型）")
    else:
        print("使用普通模式（包含验证步骤）")

    if CONFIG['single_file']:
        if CONFIG['mode'] == 'strict':
            process_simple_extraction(CONFIG['single_file'], CONFIG['output_dir'])
        else:
            process_directory(CONFIG['single_file'], CONFIG['entity_file'], CONFIG['relation_file'],
                              CONFIG['output_dir'],
                              enable_validation=not CONFIG['disable_validation'])
    else:
        if CONFIG['mode'] == 'strict':
            process_simple_extraction(CONFIG['input_dir'], CONFIG['output_dir'], CONFIG['start_index'],
                                      CONFIG['end_index'])
        else:
            process_directory(CONFIG['input_dir'], CONFIG['entity_file'], CONFIG['relation_file'], CONFIG['output_dir'],
                              CONFIG['start_index'], CONFIG['end_index'],
                              enable_validation=not CONFIG['disable_validation'])
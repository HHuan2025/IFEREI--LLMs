import pandas as pd
from datetime import datetime
import os
from config import EXCEL_OUTPUT_DIR, logger

class CSVRecorder:
    def __init__(self):
        """初始化CSV记录器"""
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.csv_file = os.path.join(EXCEL_OUTPUT_DIR, f'extraction_results_{self.timestamp}.csv')
        
        # 创建DataFrame
        self.df = pd.DataFrame(columns=[
            '文件名', 
            '时间戳', 
            '实体类型', 
            '实体类型Jaccard系数',
            '关系类型',
            '关系类型Jaccard系数'
        ])
        
    def record_types(self, filename, entity_types, entity_jaccard, relation_types, relation_jaccard):
        """记录实体类型、关系类型和Jaccard系数
        
        Args:
            filename (str): 处理的文件名
            entity_types (set): 实体类型集合
            entity_jaccard (float): 实体类型Jaccard系数
            relation_types (set): 关系类型集合
            relation_jaccard (float): 关系类型Jaccard系数
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 将集合转换为字符串
        entity_types_str = '、'.join(sorted(entity_types))
        relation_types_str = '、'.join(sorted(relation_types))
        
        # 添加新记录
        new_record = pd.DataFrame([{
            '文件名': filename,
            '时间戳': timestamp,
            '实体类型': entity_types_str,
            '实体类型Jaccard系数': entity_jaccard,
            '关系类型': relation_types_str,
            '关系类型Jaccard系数': relation_jaccard
        }])
        
        self.df = pd.concat([self.df, new_record], ignore_index=True)
            
    def save(self):
        """保存CSV文件"""
        try:
            # 保存CSV文件
            self.df.to_csv(self.csv_file, index=False, encoding='utf-8-sig')
            logger.info(f"CSV记录已保存至: {self.csv_file}")
        except Exception as e:
            logger.error(f"保存CSV文件失败: {str(e)}") 
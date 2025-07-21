from config import logger, entity_jaccard_history, relation_jaccard_history, JACCARD_THRESHOLD, CONVERGENCE_ROUNDS

def calculate_jaccard(set1, set2):
    """计算两个集合的 Jaccard 系数"""
    if not set1 and not set2:
        return 1.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

def check_convergence():
    """检查 Jaccard 系数是否连续 X 轮达到阈值"""
    if len(entity_jaccard_history) < CONVERGENCE_ROUNDS or len(relation_jaccard_history) < CONVERGENCE_ROUNDS:
        return False
    return all(j >= JACCARD_THRESHOLD for j in entity_jaccard_history) and \
        all(j >= JACCARD_THRESHOLD for j in relation_jaccard_history) 
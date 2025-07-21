import logging
from collections import deque
import os

# 创建logs目录
logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'app.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Excel 文件的默认输出目录（你可以根据实际路径调整）
EXCEL_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'excel_outputs')

# 如果目录不存在，则自动创建
os.makedirs(EXCEL_OUTPUT_DIR, exist_ok=True)



# Jaccard 系数收敛参数
JACCARD_THRESHOLD = 0.9  # Jaccard 系数阈值
CONVERGENCE_ROUNDS = 10  # 连续收敛轮数

# 全局变量
entity_jaccard_history = deque(maxlen=CONVERGENCE_ROUNDS)
relation_jaccard_history = deque(maxlen=CONVERGENCE_ROUNDS)

# 定义统一的 API 配置字典
API_CONFIG = {
    'openai': {



    }
}
CURRENT_API = 'openai'
# 便捷访问当前 API 的关键信息
OPENAI_API_KEY = API_CONFIG['openai']['api_key']
OPENAI_API_BASE = API_CONFIG['openai']['base_url']


"""pytest 配置。

将项目根目录加入 sys.path，确保测试代码能够导入 maze 包。
"""

import sys
from pathlib import Path

# 项目根目录（tests 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

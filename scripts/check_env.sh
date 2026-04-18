#!/bin/bash
# Movie Fetch 环境检查
# 用法: ./check_env.sh [needs_data]
#   无参数      - 检查基础环境
#   needs_data  - 额外检查 movies.json 是否存在

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
errors=0

echo "=== Movie Fetch 环境检查 ==="
echo ""

# 1. Python3
if command -v python3 &> /dev/null; then
    echo "[OK] python3: $(python3 --version 2>&1)"
else
    echo "[FAIL] python3 未安装"
    errors=$((errors + 1))
fi

# 2. 依赖包
for pkg in requests beautifulsoup4 pyyaml; do
    module=$(echo "$pkg" | tr '-' '_')
    if python3 -c "import $module" 2>/dev/null; then
        echo "[OK] $pkg"
    else
        echo "[FAIL] $pkg 未安装 → pip3 install $pkg"
        errors=$((errors + 1))
    fi
done

# 3. 配置文件
if [ -f "$SCRIPT_DIR/config.yaml" ]; then
    echo "[OK] config.yaml"
else
    echo "[FAIL] config.yaml 未找到"
    errors=$((errors + 1))
fi

# 4. movies.json（仅 needs_data 模式）
if [ "$1" = "needs_data" ]; then
    MOVIES_JSON=$(python3 -c "
import yaml, os
with open('$SCRIPT_DIR/config.yaml') as f:
    c = yaml.safe_load(f)
print(os.path.join('$SCRIPT_DIR', c['output']['movies_json']))
" 2>/dev/null)

    if [ -f "$MOVIES_JSON" ]; then
        count=$(python3 -c "import json; print(len(json.load(open('$MOVIES_JSON'))))" 2>/dev/null || echo "?")
        echo "[OK] movies.json ($count 部电影)"
    else
        echo "[FAIL] movies.json 未找到 ($MOVIES_JSON)"
        echo "       请先运行: python3 $SCRIPT_DIR/fetch_movies.py --top <N> --cookie '...'"
        errors=$((errors + 1))
    fi
fi

echo ""
if [ $errors -eq 0 ]; then
    echo "=== 全部通过 ==="
    exit 0
else
    echo "=== $errors 项未通过 ==="
    exit 1
fi

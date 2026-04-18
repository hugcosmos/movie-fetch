#!/bin/bash
# Movie Fetch - 安装脚本
# 将 skill 注册到 Claude Code

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
COMMANDS_DIR="$HOME/.claude/commands"
SKILL_NAME="movie-fetch"

echo "=== Movie Fetch 安装 ==="
echo ""
echo "仓库路径: $REPO_DIR"
echo ""

# 1. 确保 ~/.claude/commands/ 存在
mkdir -p "$COMMANDS_DIR"

# 2. 替换 command.md 中的路径占位符，写入 ~/.claude/commands/
sed "s|__MOVIE_FETCH_DIR__|$REPO_DIR|g" \
    "$REPO_DIR/command.md" \
    > "$COMMANDS_DIR/$SKILL_NAME.md"

echo "[OK] Skill 已安装: $COMMANDS_DIR/$SKILL_NAME.md"

# 3. 检查 Python 依赖
echo ""
echo "检查依赖..."
MISSING=0
for pkg in requests beautifulsoup4 pyyaml; do
    module=$(echo "$pkg" | tr '-' '_')
    if ! python3 -c "import $module" 2>/dev/null; then
        echo "[MISS] $pkg"
        MISSING=1
    else
        echo "[OK]  $pkg"
    fi
done

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "安装缺失依赖..."
    pip3 install -r "$REPO_DIR/scripts/requirements.txt"
fi

# 4. 创建数据目录
mkdir -p "$REPO_DIR/data/posters"
mkdir -p "$REPO_DIR/js"

echo ""
echo "=== 安装完成 ==="
echo ""
echo "用法:"
echo "  Claude Code 中输入 /movie-fetch"
echo ""
echo "更新:"
echo "  git pull && ./install.sh"
echo ""

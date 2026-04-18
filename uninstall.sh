#!/bin/bash
# Movie Fetch - 卸载脚本

COMMANDS_DIR="$HOME/.claude/commands"
SKILL_NAME="movie-fetch"

echo "=== Movie Fetch 卸载 ==="

if [ -f "$COMMANDS_DIR/$SKILL_NAME.md" ]; then
    rm "$COMMANDS_DIR/$SKILL_NAME.md"
    echo "[OK] 已移除 $COMMANDS_DIR/$SKILL_NAME.md"
else
    echo "[SKIP] 未找到 skill 文件"
fi

echo ""
echo "卸载完成。仓库目录未删除，如需删除请手动操作。"

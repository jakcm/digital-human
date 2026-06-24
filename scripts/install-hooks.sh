#!/bin/bash
# 安装 git hooks：每次 git push 自动升级版本号
# 用法: bash scripts/install-hooks.sh

HOOKS_DIR="$(git rev-parse --show-toplevel)/.git/hooks"
SCRIPT_DIR="$(dirname "$0")"

echo "🔧 安装 pre-push hook..."
cp "$SCRIPT_DIR/pre-push" "$HOOKS_DIR/pre-push"
chmod +x "$HOOKS_DIR/pre-push"
echo "✅ pre-push hook 安装完成！"
echo "   以后每次 git push 都会自动更新版本号 → 时间戳"

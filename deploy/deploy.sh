#!/usr/bin/env bash
#
# 手动部署脚本（本地构建 + rsync 同步）
#
# 用法：
#   cp deploy/deploy.env.example deploy/deploy.env   # 填服务器信息
#   ./deploy/deploy.sh
#
# 如果已经配好了 GitHub Actions，一般不需要手动跑这个。

set -euo pipefail

cd "$(dirname "$0")/.."

ENV_FILE="deploy/deploy.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "✗ 缺少 $ENV_FILE"
  echo "  先执行：cp deploy/deploy.env.example deploy/deploy.env 然后填上服务器信息"
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

: "${SSH_HOST:?deploy.env 里缺少 SSH_HOST}"
: "${SSH_USER:?deploy.env 里缺少 SSH_USER}"
: "${DEPLOY_PATH:?deploy.env 里缺少 DEPLOY_PATH}"

SSH_PORT="${SSH_PORT:-22}"
SSH_KEY="${SSH_KEY:-}"
REMOTE="${SSH_USER}@${SSH_HOST}"
SSH_OPTS=(-p "$SSH_PORT" -o StrictHostKeyChecking=accept-new)
[[ -n "$SSH_KEY" ]] && SSH_OPTS+=(-i "$SSH_KEY")

echo "▸ 构建中…"
npm run build

echo "▸ 同步到 ${REMOTE}:${DEPLOY_PATH}"
rsync -avz --delete \
  -e "ssh ${SSH_OPTS[*]}" \
  .vitepress/dist/ \
  "${REMOTE}:${DEPLOY_PATH}"

echo "✓ 部署完成 → https://${SSH_HOST}"

#!/bin/bash
# Speaking 项目一键部署脚本
# 使用方法：在服务器上执行 bash deploy-oneclick.sh
#
# 安全说明（2026-09-19 review 修复）：
# - 绝不把任何密钥/密码写进仓库历史。首次部署时本脚本现场生成随机值并落本地 .env。
# - 已存在 .env 时绝不覆盖；只补齐缺失项。
# - 变量名与 docker-compose.prod.yml 严格一致：DB_USER / DB_PASSWORD / DB_NAME /
#   JWT_SECRET（旧版误用 POSTGRES_USER / SECRET_KEY，compose 根本读不到，且把
#   生产密码明文提交进了 git）。
#
# ⚠️ 已失效（2026-09-20）：本脚本假定在服务器上 `git clone/pull` + 就地构建镜像。
# 实际的 /opt/speaking 是源码副本（无 .git），且生产机规格（2C/1.6GB）不足以
# 就地构建（会打满内存、冻结宿主机）。首次装机的 [1/6] 工具安装、[3/6] .env
# 生成仍可参照；构建与启动部分改用 knowledge/operations/RUNBOOK.md §1.1。

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/speaking}"
REPO_URL="https://github.com/CandideEgo/Speaking.git"
# 服务器公网地址（NEXT_PUBLIC_SITE_URL 用）。内测期先用 http；上 HTTPS 后改这里。
PUBLIC_URL="${PUBLIC_URL:-http://47.122.109.52}"

echo "========================================="
echo "  Speaking 项目一键部署"
echo "  项目目录: $PROJECT_DIR"
echo "========================================="

# 1. 安装必要工具
echo ""
echo "[1/6] 检查并安装必要工具..."
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    curl -fsSL https://get.docker.com | bash
    systemctl start docker
    systemctl enable docker
fi

if ! command -v docker-compose &> /dev/null; then
    echo "安装 Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

if ! command -v git &> /dev/null; then
    echo "安装 Git..."
    apt-get update && apt-get install -y git || yum install -y git
fi

echo "✓ Docker: $(docker --version)"
echo "✓ Docker Compose: $(docker-compose --version)"
echo "✓ Git: $(git --version)"

# 2. 克隆或更新代码
echo ""
echo "[2/6] 获取项目代码..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

if [ -d ".git" ]; then
    echo "更新现有代码..."
    git pull origin master
else
    echo "克隆新代码..."
    git clone "$REPO_URL" .
fi

echo "✓ 代码已就绪: $(git rev-parse --short HEAD)"

# 3. 配置环境变量（已存在 .env 绝不覆盖；缺失项现场生成）
echo ""
echo "[3/6] 配置环境变量..."

if [ ! -f ".env" ]; then
    echo "首次部署，生成 .env（随机密码 / 随机 JWT_SECRET）..."
    DB_PASSWORD="$(openssl rand -hex 16)"
    JWT_SECRET="$(openssl rand -hex 32)"
    CALLBACK_SECRET="$(openssl rand -hex 32)"
    cat > .env << EOF
# 由 deploy-oneclick.sh 于 $(date -Iseconds) 生成。请勿提交到 git。
DB_USER=speaking
DB_NAME=speaking
DB_PASSWORD=${DB_PASSWORD}
JWT_SECRET=${JWT_SECRET}
TRANSCRIPTION_CALLBACK_SECRET=${CALLBACK_SECRET}
ENV=production
# 前端访问地址（构建期常量；浏览器与 API 同源）
NEXT_PUBLIC_SITE_URL=${PUBLIC_URL}
# ── 以下一项必须手动填入后再 up（后端在 production 下会强制校验）──
# OPENAI_API_KEY=sk-...
EOF
    chmod 600 .env
    echo ""
    echo "⚠️  已生成 .env 但还缺 OPENAI_API_KEY。"
    echo "   执行: nano $PROJECT_DIR/.env  填入后重跑本脚本。"
    exit 1
else
    echo ".env 已存在，跳过生成（不覆盖）。"
    # 防御性检查：compose 必需的变量是否齐。
    missing=0
    for v in DB_USER DB_PASSWORD DB_NAME JWT_SECRET; do
        grep -q "^${v}=" .env || { echo "⚠️  .env 缺少 $v"; missing=1; }
    done
    [ "$missing" -eq 1 ] && { echo "请补全 .env 后重试。"; exit 1; }
fi

# 4. 构建镜像
echo ""
echo "[4/6] 构建 Docker 镜像..."
docker-compose -f docker-compose.prod.yml build

echo "✓ 镜像构建完成"

# 5. 启动服务
echo ""
echo "[5/6] 启动服务..."
docker-compose -f docker-compose.prod.yml down || true
docker-compose -f docker-compose.prod.yml up -d

echo "✓ 服务已启动"

# 6. 等待并检查状态
echo ""
echo "[6/6] 检查服务状态..."
sleep 15

echo ""
echo "容器状态:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "最近日志:"
docker-compose -f docker-compose.prod.yml logs --tail=20

echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo "🌐 访问地址: ${PUBLIC_URL}"
echo "📋 实时日志: docker-compose -f docker-compose.prod.yml logs -f"

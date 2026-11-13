#!/bin/bash
# Speaking 项目部署脚本
# 使用方法：在服务器上执行 bash deploy.sh
#
# ⚠️ 已失效（2026-09-20）：本脚本假定在服务器上 `git pull` + 就地构建镜像。
# 实际的 /opt/speaking 是源码副本（无 .git），且生产机规格（2C/1.6GB）不足以
# 就地构建（会打满内存、冻结宿主机）。现行标准流程见
# knowledge/operations/RUNBOOK.md §1.1「异地构建 + 传镜像」。

set -e

echo "========================================="
echo "  Speaking 项目部署脚本"
echo "========================================="

# 配置变量
PROJECT_DIR="${PROJECT_DIR:-/opt/speaking}"
REPO_URL="https://github.com/CandideEgo/Speaking.git"  # 修改为你的实际仓库地址
BRANCH="master"

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
    apt-get update && apt-get install -y git
fi

# 2. 克隆或更新代码
echo ""
echo "[2/6] 获取项目代码..."
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "更新现有代码..."
    cd $PROJECT_DIR
    git pull origin $BRANCH
else
    echo "克隆新代码..."
    mkdir -p $PROJECT_DIR
    git clone -b $BRANCH $REPO_URL $PROJECT_DIR
    cd $PROJECT_DIR
fi

# 3. 配置环境变量
echo ""
echo "[3/6] 配置环境变量..."
if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    # 变量名必须与 docker-compose.prod.yml 一致：DB_USER / DB_PASSWORD / DB_NAME /
    # JWT_SECRET（compose 不读 POSTGRES_USER / SECRET_KEY）。
    cat > .env << 'EOF'
# 数据库配置（compose 据此拼 DATABASE_URL）
DB_USER=speaking
DB_NAME=speaking
DB_PASSWORD=change-me-strong-random-password

# 后端必须（production 启动时强制校验）
JWT_SECRET=change-me-openssl-rand-hex-32
TRANSCRIPTION_CALLBACK_SECRET=change-me-random-hex-32
OPENAI_API_KEY=sk-your-key-here
ENV=production

# 前端公示信息（构建期常量；域名由 NEXT_PUBLIC_SITE_URL 决定，不是 API URL——
# 浏览器与 API 同源，没有独立的 API 地址）
NEXT_PUBLIC_SITE_URL=https://seeword.top

# GPU 转录不在这台机器上：模型与 WHISPER_* 配置属于 gpu-worker/，
# 见 gpu-worker/.env.gpu-worker.example，不要写进云端 .env。
EOF
    chmod 600 .env
    echo "⚠️  请编辑 .env 文件，填入正确的配置信息"
    echo "   执行: nano .env"
    read -p "按回车继续..."
fi

# 4. 构建镜像
echo ""
echo "[4/6] 构建 Docker 镜像..."
docker-compose -f docker-compose.prod.yml build --no-cache

# 5. 启动服务
echo ""
echo "[5/6] 启动服务..."
docker-compose -f docker-compose.prod.yml down || true
docker-compose -f docker-compose.prod.yml up -d

# 6. 检查服务状态
echo ""
echo "[6/6] 检查服务状态..."
sleep 10
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo "查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "停止服务: docker-compose -f docker-compose.prod.yml down"
echo "重启服务: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "访问地址: http://47.122.109.52"

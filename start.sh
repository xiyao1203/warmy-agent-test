#!/usr/bin/env bash
# ==============================================================================
# AgentTest 本地一键启动脚本
# ==============================================================================
# 用法:   ./start.sh                    # 默认启动（自动检测/安装依赖）
#         ./start.sh --no-install       # 跳过依赖安装
#         ./start.sh --help             # 显示帮助
#
# 前端: http://localhost:5175        (局域网: http://<你的IP>:5175)
# 后端: http://localhost:8181/api/v1 (局域网: http://<你的IP>:8181/api/v1)
# ==============================================================================

set -euo pipefail

# ── 常量 ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_PORT=5175
BACKEND_PORT=8181

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 依赖版本要求
MIN_NODE_MAJOR=18
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=12

# PID 文件（用于清理）
PID_BACKEND=""
PID_FRONTEND=""

NO_INSTALL=false

# ── 工具函数 ──────────────────────────────────────────────────────────────────

log()    { echo -e "  ${NC}$1${NC}"; }
info()   { echo -e "${BLUE}ℹ${NC} $1"; }
ok()     { echo -e "${GREEN}✓${NC} $1"; }
warn()   { echo -e "${YELLOW}⚠${NC} $1"; }
fail()   { echo -e "${RED}✗ $1${NC}"; exit 1; }
header() { echo -e "\n${BOLD}${CYAN}═══ $1 ═══${NC}\n"; }

# Ctrl+C / 退出时清理
cleanup() {
    echo ""
    header "正在关闭服务..."
    if [ -n "$PID_BACKEND" ] && kill -0 "$PID_BACKEND" 2>/dev/null; then
        kill "$PID_BACKEND" 2>/dev/null || true
        wait "$PID_BACKEND" 2>/dev/null || true
        ok "后端已关闭 (PID $PID_BACKEND)"
    fi
    if [ -n "$PID_FRONTEND" ] && kill -0 "$PID_FRONTEND" 2>/dev/null; then
        kill "$PID_FRONTEND" 2>/dev/null || true
        wait "$PID_FRONTEND" 2>/dev/null || true
        ok "前端已关闭 (PID $PID_FRONTEND)"
    fi
    echo ""
    info "👋 再见！"
    exit 0
}
trap cleanup INT TERM

# 获取局域网 IP
get_lan_ip() {
    # macOS
    if command -v ifconfig &>/dev/null; then
        ifconfig 2>/dev/null | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1
    # Linux
    elif command -v hostname &>/dev/null; then
        hostname -I 2>/dev/null | awk '{print $1}'
    else
        echo ""
    fi
}

# ── 依赖检测与安装 ───────────────────────────────────────────────────────────

check_node() {
    info "检测 Node.js..."
    
    # 检查常见安装位置
    local node_paths=(
        "$HOME/.local/node-v20.18.0/bin/node"
        "$HOME/.local/node-v22.15.0/bin/node"
        "$HOME/.local/share/fnm/node-versions/v20.18.0/installation/bin/node"
        "$HOME/.local/share/fnm/node-versions/v22.15.0/installation/bin/node"
        "/usr/local/bin/node"
        "/opt/homebrew/bin/node"
    )
    
    # 如果 node 不在 PATH 中，尝试查找
    if ! command -v node &>/dev/null; then
        for node_path in "${node_paths[@]}"; do
            if [ -x "$node_path" ]; then
                # 添加到 PATH
                export PATH="$(dirname "$node_path"):$PATH"
                ok "Node.js 已找到: $node_path"
                ok "Node.js $(node --version)"
                return
            fi
        done
        
        warn "Node.js 未安装或不在 PATH 中"
        if [ "$NO_INSTALL" = true ]; then
            fail "请先安装 Node.js >= ${MIN_NODE_MAJOR} (https://nodejs.org)"
        fi
        install_node
        return
    fi
    
    local ver
    ver=$(node --version | sed 's/v//' | cut -d. -f1)
    if [ "$ver" -lt "$MIN_NODE_MAJOR" ]; then
        warn "Node.js 版本过低 (v$(node --version)), 需要 >= v${MIN_NODE_MAJOR}"
        if [ "$NO_INSTALL" = true ]; then
            fail "请升级 Node.js"
        fi
        install_node
        return
    fi
    ok "Node.js $(node --version)"
}

install_node() {
    info "正在安装 Node.js (通过 fnm)..."
    export PATH="$HOME/.local/share/fnm:$PATH"
    if ! command -v fnm &>/dev/null; then
        curl -fsSL https://fnm.vercel.app/install | bash 2>/dev/null || \
            fail "fnm 安装失败，请手动安装 Node.js: https://nodejs.org"
        # shellcheck disable=SC1090
        [ -f "$HOME/.local/share/fnm/env" ] && source "$HOME/.local/share/fnm/env"
        [ -f "$HOME/.bashrc" ] && source "$HOME/.bashrc"
    fi
    if command -v fnm &>/dev/null; then
        fnm install --lts 2>/dev/null || fnm install 20
        fnm use lts-latest 2>/dev/null || fnm use 20
        eval "$(fnm env)"
        ok "Node.js 安装完成: $(node --version)"
    else
        fail "Node.js 自动安装失败，请手动安装"
    fi
}

check_pnpm() {
    info "检测 pnpm..."
    if ! command -v pnpm &>/dev/null; then
        warn "pnpm 未安装"
        if [ "$NO_INSTALL" = true ]; then
            fail "请先安装 pnpm: npm install -g pnpm"
        fi
        install_pnpm
        return
    fi
    ok "pnpm $(pnpm --version)"
}

install_pnpm() {
    info "正在安装 pnpm..."
    if command -v npm &>/dev/null; then
        npm install -g pnpm 2>/dev/null || \
            fail "pnpm 安装失败，请手动安装: npm install -g pnpm"
    elif command -v corepack &>/dev/null; then
        corepack enable pnpm
        corepack prepare pnpm@latest --activate
    else
        curl -fsSL https://get.pnpm.io/install.sh | sh - 2>/dev/null || \
            fail "pnpm 安装失败"
        export PNPM_HOME="$HOME/.local/share/pnpm"
        export PATH="$PNPM_HOME:$PATH"
    fi
    ok "pnpm 安装完成: $(pnpm --version 2>/dev/null || echo '请重新打开终端')"
}

check_python() {
    info "检测 Python 环境..."
    # 优先使用 uv 管理的 Python
    if command -v uv &>/dev/null; then
        if uv run python --version &>/dev/null 2>&1; then
            local py_ver
            py_ver=$(uv run python --version 2>&1 | awk '{print $2}')
            ok "Python $py_ver (via uv)"
            return
        fi
    fi
    # 回退到系统 Python
    if command -v python3 &>/dev/null; then
        local major minor
        major=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1)
        minor=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f2)
        if [ "$major" -ge "$MIN_PYTHON_MAJOR" ] && [ "$minor" -ge "$MIN_PYTHON_MINOR" ]; then
            ok "Python $(python3 --version 2>&1 | awk '{print $2}')"
            return
        fi
    fi
    fail "需要 Python >= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}，请使用 uv 或手动安装"
}

check_uv() {
    info "检测 uv (Python 包管理器)..."
    if ! command -v uv &>/dev/null; then
        info "正在安装 uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null || \
            fail "uv 安装失败"
        export PATH="$HOME/.local/bin:$PATH"
    fi
    ok "uv $(uv --version 2>/dev/null || echo 'ok')"
}

check_db_choice() {
    info "检测数据库..."
    # 优先检测 Docker 容器中的 PostgreSQL
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "postgresql"; then
        ok "检测到 PostgreSQL Docker 容器运行中，将使用 PostgreSQL"
        export AGENTTEST_DATABASE_URL="postgresql+asyncpg://agenttest:agenttest-local@localhost:5432/agenttest"
    elif pg_isready -q 2>/dev/null; then
        ok "检测到 PostgreSQL 运行中，将使用 PostgreSQL"
        export AGENTTEST_DATABASE_URL="postgresql+asyncpg://agenttest:agenttest-local@localhost:5432/agenttest"
    elif lsof -i :5432 -sTCP:LISTEN &>/dev/null 2>&1; then
        ok "检测到端口 5432 监听中，将使用 PostgreSQL"
        export AGENTTEST_DATABASE_URL="postgresql+asyncpg://agenttest:agenttest-local@localhost:5432/agenttest"
    else
        warn "PostgreSQL 未运行，将使用本地 SQLite (data/local.db)"
        mkdir -p data
        export AGENTTEST_DATABASE_URL="sqlite+aiosqlite:///data/local.db"
    fi
}

# ── 依赖安装 ──────────────────────────────────────────────────────────────────

install_deps() {
    if [ "$NO_INSTALL" = true ]; then
        info "跳过依赖安装 (--no-install)"
        return
    fi

    header "安装项目依赖"

    info "安装 Python 依赖..."
    (cd "$SCRIPT_DIR" && uv sync --all-packages) 2>&1 | tail -3
    ok "Python 依赖就绪"

    info "安装 Node.js 依赖..."
    (cd "$SCRIPT_DIR" && pnpm install --frozen-lockfile 2>/dev/null || pnpm install) 2>&1 | tail -3
    ok "Node.js 依赖就绪"
}

# ── 数据库初始化 ──────────────────────────────────────────────────────────────

ensure_local_env() {
    header "初始化本地环境配置"
    local root_env="$SCRIPT_DIR/.env"
    local api_env="$SCRIPT_DIR/apps/control-api/.env"

    # 运行 ensure_local_env.py 生成根目录 .env
    if [ ! -f "$root_env" ]; then
        info "生成本地环境配置..."
        (cd "$SCRIPT_DIR" && uv run python scripts/ensure_local_env.py "$root_env")
        ok "本地环境配置已生成"
    else
        ok "本地环境配置已存在"
    fi

    # 确保后端目录也有 .env（Pydantic Settings 使用相对路径）
    if [ ! -f "$api_env" ]; then
        cp "$root_env" "$api_env"
        chmod 600 "$api_env"
        ok "后端环境配置已同步"
    fi
}

init_database() {
    header "初始化数据库"
    if echo "$AGENTTEST_DATABASE_URL" | grep -q "sqlite"; then
        # SQLite: 只需确保目录存在，Alembic 会自动创建数据库文件
        mkdir -p data
        ok "SQLite 数据库路径已就绪 (data/local.db)"
    fi
    # 无论何种数据库，都运行迁移确保表结构最新
    info "运行数据库迁移..."
    (cd "$SCRIPT_DIR" && uv run alembic -c apps/control-api/alembic.ini upgrade head) 2>&1 | tail -3
    ok "数据库迁移完成"
}

# ── 端口检测 ──────────────────────────────────────────────────────────────────

check_port() {
    local port=$1
    if lsof -i ":$port" -sTCP:LISTEN &>/dev/null 2>&1; then
        warn "端口 $port 已被占用"
        local pid
        pid=$(lsof -ti ":$port" -sTCP:LISTEN 2>/dev/null)
        if [ -n "$pid" ]; then
            info "正在终止占用进程 (PID $pid)..."
            kill -9 "$pid" 2>/dev/null || true
            sleep 1
            ok "端口 $port 已释放"
        fi
    fi
}

# ── 启动服务 ──────────────────────────────────────────────────────────────────

start_backend() {
    header "启动后端服务 (端口 $BACKEND_PORT)"
    check_port "$BACKEND_PORT"
    cd "$SCRIPT_DIR/apps/control-api"

    uv run uvicorn agenttest.main:app \
        --host 0.0.0.0 \
        --port "$BACKEND_PORT" \
        --log-level info \
        --reload &
    PID_BACKEND=$!

    # 等待后端就绪
    info "等待后端启动..."
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://localhost:$BACKEND_PORT/api/v1/health" > /dev/null 2>&1; then
            ok "后端已就绪 (PID $PID_BACKEND)"
            return
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    fail "后端启动超时，请检查日志"
}

start_frontend() {
    header "启动前端服务 (端口 $FRONTEND_PORT)"
    check_port "$FRONTEND_PORT"
    cd "$SCRIPT_DIR/apps/web"

    NEXT_PUBLIC_CONTROL_API_URL="http://localhost:$BACKEND_PORT" \
    pnpm dev \
        --port "$FRONTEND_PORT" \
        --hostname 0.0.0.0 &
    PID_FRONTEND=$!

    # 等待前端就绪
    info "等待前端编译..."
    local max_attempts=60
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$FRONTEND_PORT" 2>/dev/null | grep -q "200\|304\|302"; then
            ok "前端已就绪 (PID $PID_FRONTEND)"
            return
        fi
        attempt=$((attempt + 1))
        sleep 2
        # 每 10 次尝试输出一个点
        if [ $((attempt % 5)) -eq 0 ]; then
            echo -n "."
        fi
    done
    echo ""
    fail "前端启动超时 (${max_attempts}次尝试)，请检查日志"
}

show_info() {
    local lan_ip
    lan_ip=$(get_lan_ip)

    echo ""
    echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║         🚀 AgentTest 已启动！                            ║${NC}"
    echo -e "${BOLD}${GREEN}╠══════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BOLD}${GREEN}║${NC}                                                          "
    echo -e "${BOLD}${GREEN}║${NC}  ${BOLD}前端应用:${NC}"
    echo -e "${BOLD}${GREEN}║${NC}    ${BLUE}本地:${NC}  ${CYAN}http://localhost:${FRONTEND_PORT}${NC}"
    if [ -n "$lan_ip" ]; then
        echo -e "${BOLD}${GREEN}║${NC}    ${YELLOW}局域网:${NC} ${CYAN}http://${lan_ip}:${FRONTEND_PORT}${NC}"
    fi
    echo -e "${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}║${NC}  ${BOLD}后端 API:${NC}"
    echo -e "${BOLD}${GREEN}║${NC}    ${BLUE}本地:${NC}  ${CYAN}http://localhost:${BACKEND_PORT}/api/v1${NC}"
    if [ -n "$lan_ip" ]; then
        echo -e "${BOLD}${GREEN}║${NC}    ${YELLOW}局域网:${NC} ${CYAN}http://${lan_ip}:${BACKEND_PORT}/api/v1${NC}"
    fi
    echo -e "${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}║${NC}  ${BOLD}健康检查:${NC}"
    echo -e "${BOLD}${GREEN}║${NC}    ${CYAN}http://localhost:${BACKEND_PORT}/api/v1/health${NC}"
    echo -e "${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}║${NC}  ${BOLD}API 文档:${NC}"
    echo -e "${BOLD}${GREEN}║${NC}    ${CYAN}http://localhost:${BACKEND_PORT}/docs${NC}"
    echo -e "${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}║${NC}  按 ${RED}Ctrl+C${NC} 停止所有服务"
    echo -e "${BOLD}${GREEN}║${NC}                                                          "
    echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ── 帮助 ──────────────────────────────────────────────────────────────────────

show_help() {
    echo "AgentTest 本地一键启动脚本"
    echo ""
    echo "  用法:  ./start.sh [选项]"
    echo ""
    echo "  选项:"
    echo "    --no-install   跳过依赖自动安装"
    echo "    --help         显示此帮助信息"
    echo ""
    echo "  端口:"
    echo "    前端: $FRONTEND_PORT"
    echo "    后端: $BACKEND_PORT"
    echo ""
    echo "  示例:"
    echo "    ./start.sh                  # 自动检测+安装+启动"
    echo "    ./start.sh --no-install     # 快速启动（已安装依赖）"
}

# ── 主流程 ────────────────────────────────────────────────────────────────────

main() {
    # 解析参数
    while [ $# -gt 0 ]; do
        case "$1" in
            --no-install) NO_INSTALL=true; shift ;;
            --help|-h)    show_help; exit 0 ;;
            *)            warn "未知参数: $1"; show_help; exit 1 ;;
        esac
    done

    # 确保在项目根目录
    cd "$SCRIPT_DIR"

    echo ""
    echo -e "${BOLD}${CYAN}  ╔═══════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}  ║     AgentTest 本地开发环境启动器          ║${NC}"
    echo -e "${BOLD}${CYAN}  ╚═══════════════════════════════════════════╝${NC}"

    # 1. 检查依赖
    header "Step 1/6  检查运行环境"
    check_node
    check_pnpm
    check_uv
    check_python

    # 2. 安装依赖
    header "Step 2/6  安装项目依赖"
    install_deps

    # 3. 初始化本地环境配置
    header "Step 3/6  初始化环境配置"
    ensure_local_env

    # 4. 检测数据库
    header "Step 4/6  配置数据库"
    check_db_choice

    # 5. 初始化数据库
    init_database

    # 6. 启动服务
    header "Step 5/6  启动服务"
    start_backend
    start_frontend

    # 显示信息
    header "Step 6/6  就绪"
    show_info

    # 保持运行
    wait
}

main "$@"

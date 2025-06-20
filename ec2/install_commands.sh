#!/bin/bash
# Trae Commands Installer
# 安裝Trae指令到系統PATH

set -e

echo "🚀 安裝Trae指令工具..."

# 指令文件路徑
COMMANDS_DIR="/home/alexchuang/aiengine/trae/ec2"
INSTALL_DIR="/usr/local/bin"

# 檢查是否有sudo權限
if [ "$EUID" -ne 0 ]; then
    echo "❌ 請使用sudo運行此腳本"
    exit 1
fi

# 安裝依賴
echo "📦 檢查並安裝依賴..."

# 檢查sshpass
if ! command -v sshpass &> /dev/null; then
    echo "安裝sshpass..."
    apt-get update
    apt-get install -y sshpass
fi

# 檢查Python3
if ! command -v python3 &> /dev/null; then
    echo "安裝Python3..."
    apt-get install -y python3 python3-pip
fi

# 創建符號鏈接
echo "🔗 創建指令鏈接..."

for cmd in trae-history trae-sync trae-send; do
    if [ -f "$COMMANDS_DIR/$cmd" ]; then
        ln -sf "$COMMANDS_DIR/$cmd" "$INSTALL_DIR/$cmd"
        echo "✅ 已安裝: $cmd"
    else
        echo "❌ 文件不存在: $COMMANDS_DIR/$cmd"
    fi
done

# 設置權限
chmod +x "$COMMANDS_DIR"/trae-*

echo ""
echo "🎉 Trae指令工具安裝完成!"
echo ""
echo "📋 可用指令:"
echo "   trae-history <倉庫名>     # 提取對話歷史"
echo "   trae-sync <倉庫名>        # 同步倉庫源碼"
echo "   trae-send <倉庫名> <消息>  # 發送消息到Trae"
echo ""
echo "🔧 使用示例:"
echo "   trae-history --list                    # 列出可用倉庫"
echo "   trae-history powerauto.ai_0.53        # 提取指定倉庫歷史"
echo "   trae-sync --all                       # 同步所有倉庫"
echo "   trae-send powerauto.ai_0.53 '你好'     # 發送消息"
echo ""
echo "📝 更多選項請使用 --help 查看"


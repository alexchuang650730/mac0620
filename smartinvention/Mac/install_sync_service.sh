#!/bin/bash
# Trae MCP Git Sync Service Installer (Mac端)
# 安裝和配置Trae MCP自動同步服務

set -e

echo "🚀 安裝Trae MCP Git自動同步服務 (Mac端)..."

# 配置變量
SERVICE_NAME="trae-mcp-sync"
SCRIPT_PATH="/home/alexchuang/aiengine/trae/mac/trae_mcp_sync.py"
SERVICE_PATH="/Library/LaunchDaemons/com.trae.mcp.sync.plist"
LOG_PATH="/tmp/trae_mcp_sync_mac.log"

# 檢查是否為macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ 此腳本僅支持macOS系統"
    exit 1
fi

# 檢查Python3是否安裝
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安裝，請先安裝Python3"
    exit 1
fi

# 檢查psutil模塊
if ! python3 -c "import psutil" &> /dev/null; then
    echo "📦 安裝psutil模塊..."
    pip3 install psutil
fi

# 確保腳本可執行
chmod +x "$SCRIPT_PATH"

# 創建LaunchDaemon配置文件
echo "📝 創建LaunchDaemon配置..."
sudo tee "$SERVICE_PATH" > /dev/null << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trae.mcp.sync</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$SCRIPT_PATH</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>$LOG_PATH</string>
    
    <key>StandardErrorPath</key>
    <string>$LOG_PATH</string>
    
    <key>WorkingDirectory</key>
    <string>/home/alexchuang/aiengine/trae/mac</string>
    
    <key>UserName</key>
    <string>alexchuang</string>
    
    <key>GroupName</key>
    <string>staff</string>
    
    <key>ThrottleInterval</key>
    <integer>30</integer>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

# 設置正確的權限
sudo chown root:wheel "$SERVICE_PATH"
sudo chmod 644 "$SERVICE_PATH"

# 加載服務
echo "🔄 加載LaunchDaemon服務..."
sudo launchctl load "$SERVICE_PATH"

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
if sudo launchctl list | grep -q "com.trae.mcp.sync"; then
    echo "✅ 服務已成功加載並運行"
else
    echo "❌ 服務加載失敗"
    exit 1
fi

echo ""
echo "🎉 Trae MCP Git自動同步服務安裝完成 (Mac端)！"
echo ""
echo "📋 服務信息:"
echo "   服務名稱: $SERVICE_NAME"
echo "   配置文件: $SERVICE_PATH"
echo "   日誌文件: $LOG_PATH"
echo "   腳本路徑: $SCRIPT_PATH"
echo ""
echo "🔧 管理命令:"
echo "   查看狀態: sudo launchctl list | grep com.trae.mcp.sync"
echo "   停止服務: sudo launchctl unload $SERVICE_PATH"
echo "   啟動服務: sudo launchctl load $SERVICE_PATH"
echo "   查看日誌: tail -f $LOG_PATH"
echo ""
echo "📝 手動執行一次同步:"
echo "   python3 $SCRIPT_PATH --sync-once"
echo ""
echo "🔍 監控連接狀態:"
echo "   python3 /home/alexchuang/aiengine/trae/mac/mcp_monitor.py"
echo ""


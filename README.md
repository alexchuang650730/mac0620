# Trae MCP Git Auto-Sync System

這是一個自動化的Trae MCP Git同步系統，包含Mac端監控和EC2端執行工具。

## 📁 目錄結構

```
mac0620/
├── Mac/                          # Mac端程序
│   ├── trae_mcp_sync.py         # 主要同步監控程序
│   ├── mcp_monitor.py           # 連接狀態監控工具
│   ├── repository_discovery.py  # 倉庫自動發現工具
│   └── install_sync_service.sh  # Mac端服務安裝腳本
└── ec2/                          # EC2端程序
    ├── trae-history             # 指令1：對話歷史提取
    ├── trae-sync                # 指令2：倉庫源碼同步
    ├── trae-send                # 指令3：消息發送工具
    ├── sync_repositories.py     # Git倉庫同步執行程序
    ├── install_commands.sh      # 指令安裝腳本
    └── COMMANDS_GUIDE.md        # 指令使用指南
```

## 🚀 快速開始

### Mac端安裝
```bash
cd Mac/
chmod +x install_sync_service.sh
./install_sync_service.sh
```

### EC2端安裝
```bash
cd ec2/
sudo ./install_commands.sh
```

## 📋 三個核心指令

### 1. `trae-history` - 對話歷史提取
```bash
trae-history <倉庫名稱>
trae-history --list              # 列出可用倉庫
trae-history --all               # 提取所有倉庫歷史
```

### 2. `trae-sync` - 倉庫源碼同步
```bash
trae-sync <倉庫名稱>
trae-sync --discover             # 發現倉庫
trae-sync --all                  # 同步所有倉庫
```

### 3. `trae-send` - 消息發送
```bash
trae-send <倉庫名稱> "<消息內容>"
trae-send --test <倉庫名稱>       # 發送測試消息
```

## 🎯 功能特點

- ✅ **自動監控**: Mac端持續監控MCP與Trae連接狀態
- ✅ **智能同步**: 自動發現並同步Git倉庫
- ✅ **對話提取**: 從Trae提取相關對話歷史
- ✅ **消息發送**: 向Trae發送消息並驗證記錄
- ✅ **結構化存儲**: 按倉庫組織文件和歷史
- ✅ **完整日誌**: 詳細的操作日誌和錯誤處理

## 📊 數據組織

所有數據按以下結構組織：
```
/home/alexchuang/aiengine/trae/git/
├── <倉庫名>/
│   ├── .git/                    # Git倉庫
│   ├── source/                  # 源碼目錄
│   └── history/                 # 對話歷史
│       ├── conversation_history_*.json
│       ├── latest.json
│       └── send_log.jsonl
```

## 🔧 配置說明

### SSH連接配置
- 主機: serveo.net:41269
- 用戶: alexchuang
- 密碼: 123456

### Trae數據庫路徑
```
/Users/alexchuang/Library/Application Support/Trae/User/workspaceStorage/f002a9b85f221075092022809f5a075f/state.vscdb
```

## 📝 更新日誌

### 2025-06-20
- ✅ 創建Mac端監控程序
- ✅ 創建EC2端三個核心指令
- ✅ 實現倉庫自動發現功能
- ✅ 完成對話歷史提取功能
- ✅ 實現消息發送和驗證功能
- ✅ 建立完整的目錄結構和文檔

## 🚨 故障排除

詳細的故障排除指南請參考 `ec2/COMMANDS_GUIDE.md`

## 📞 支持

如有問題請查看相關文檔或檢查日誌文件。


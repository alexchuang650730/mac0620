# Trae Commands 使用指南

## 📋 三個核心指令

### 1. `trae-history` - 對話歷史提取
從Trae提取對話歷史並保存到 `/home/alexchuang/aiengine/trae/git/倉名/history/`

```bash
# 基本用法
trae-history <倉庫名稱>

# 選項
trae-history --list              # 列出可用倉庫
trae-history --all               # 提取所有倉庫的歷史
trae-history powerauto.ai_0.53   # 提取指定倉庫歷史

# 輸出位置
/home/alexchuang/aiengine/trae/git/powerauto.ai_0.53/history/
├── conversation_history_20250620_143022.json
├── latest.json -> conversation_history_20250620_143022.json
└── send_log.jsonl
```

### 2. `trae-sync` - 倉庫源碼同步
找到倉庫並同步源碼到 `/home/alexchuang/aiengine/trae/git/倉名/source/`

```bash
# 基本用法
trae-sync <倉庫名稱>

# 選項
trae-sync --list                 # 列出本地倉庫
trae-sync --discover             # 從Trae發現倉庫
trae-sync --all                  # 同步所有倉庫
trae-sync powerauto.ai_0.53      # 同步指定倉庫

# 輸出位置
/home/alexchuang/aiengine/trae/git/powerauto.ai_0.53/source/
├── src/
├── docs/
├── README.md
├── package.json
└── sync_info.json
```

### 3. `trae-send` - 消息發送
向Trae對話框發送消息並確認記錄到對話歷史

```bash
# 基本用法
trae-send <倉庫名稱> "<消息內容>"

# 選項
trae-send --list                           # 列出可用倉庫
trae-send --test powerauto.ai_0.53         # 發送測試消息
trae-send powerauto.ai_0.53 "你好，這是測試消息"

# 日誌位置
/home/alexchuang/aiengine/trae/git/powerauto.ai_0.53/history/send_log.jsonl
```

## 🚀 安裝指令

```bash
# 1. 設置執行權限
chmod +x /home/alexchuang/aiengine/trae/ec2/install_commands.sh

# 2. 安裝指令到系統PATH
sudo /home/alexchuang/aiengine/trae/ec2/install_commands.sh

# 3. 驗證安裝
trae-history --help
trae-sync --help  
trae-send --help
```

## 📊 目錄結構

執行指令後會創建以下目錄結構：

```
/home/alexchuang/aiengine/trae/git/
├── powerauto.ai_0.53/
│   ├── .git/                    # Git倉庫
│   ├── source/                  # 源碼目錄 (trae-sync)
│   │   ├── src/
│   │   ├── docs/
│   │   └── sync_info.json
│   └── history/                 # 歷史目錄 (trae-history)
│       ├── conversation_history_*.json
│       ├── latest.json
│       └── send_log.jsonl       # 發送日誌 (trae-send)
├── communitypowerautomation/
│   ├── source/
│   └── history/
└── ...
```

## 🔧 配置說明

### SSH連接配置
```python
ssh_config = {
    "host": "serveo.net",
    "port": 41269,
    "user": "alexchuang", 
    "password": "123456"
}
```

### Trae數據庫路徑
```python
trae_db_path = "/Users/alexchuang/Library/Application Support/Trae/User/workspaceStorage/f002a9b85f221075092022809f5a075f/state.vscdb"
```

## 📝 使用示例

### 完整工作流程
```bash
# 1. 發現並同步所有倉庫
trae-sync --discover
trae-sync --all

# 2. 提取所有對話歷史
trae-history --all

# 3. 向特定倉庫發送消息
trae-send powerauto.ai_0.53 "請分析當前代碼結構"

# 4. 檢查消息是否記錄
trae-history powerauto.ai_0.53
```

### 單個倉庫操作
```bash
# 同步特定倉庫
trae-sync powerauto.ai_0.53

# 提取該倉庫的對話歷史
trae-history powerauto.ai_0.53

# 發送消息並驗證
trae-send powerauto.ai_0.53 "代碼更新完成"
```

## 🚨 故障排除

### 常見問題

1. **SSH連接失敗**
   ```bash
   # 檢查Serveo隧道狀態
   ssh -p 41269 alexchuang@serveo.net "echo 'SSH測試'"
   ```

2. **權限問題**
   ```bash
   # 確保指令有執行權限
   chmod +x /home/alexchuang/aiengine/trae/ec2/trae-*
   ```

3. **依賴缺失**
   ```bash
   # 安裝sshpass
   sudo apt-get install sshpass
   
   # 檢查Python3
   python3 --version
   ```

4. **Trae數據庫無法訪問**
   ```bash
   # 檢查Trae是否運行
   trae-send --test powerauto.ai_0.53
   ```

### 日誌查看
```bash
# 查看發送日誌
cat /home/alexchuang/aiengine/trae/git/*/history/send_log.jsonl

# 查看最新對話歷史
cat /home/alexchuang/aiengine/trae/git/*/history/latest.json
```

## 🎯 功能特點

- ✅ **自動化**: 通過SSH自動操作Mac上的Trae
- ✅ **結構化**: 按倉庫組織歷史和源碼
- ✅ **驗證機制**: 確認消息已記錄到對話歷史
- ✅ **日誌記錄**: 完整的操作日誌和時間戳
- ✅ **錯誤處理**: 完善的錯誤處理和重試機制
- ✅ **批量操作**: 支持對所有倉庫批量操作


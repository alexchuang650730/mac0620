#!/usr/bin/env python3
"""
Trae MCP Connection Monitor (Mac端)
輕量級的MCP連接監控工具，用於檢測MCP與Trae的連接狀態
"""

import os
import sys
import time
import json
import psutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

class MCPConnectionMonitor:
    def __init__(self):
        self.trae_app_support = "/Users/alexchuang/Library/Application Support/Trae"
        self.status_file = "/tmp/mcp_trae_status_mac.json"
        
    def check_trae_process(self) -> bool:
        """檢查Trae進程是否運行"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'Trae' in proc.info['name'] or any('Trae' in cmd for cmd in proc.info['cmdline'] or []):
                    return True
            return False
        except Exception:
            return False
    
    def check_mcp_process(self) -> bool:
        """檢查MCP相關進程"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = proc.info['cmdline'] or []
                if any('mcp' in cmd.lower() for cmd in cmdline):
                    return True
            return False
        except Exception:
            return False
    
    def check_trae_database(self) -> bool:
        """檢查Trae數據庫是否可訪問"""
        try:
            db_path = os.path.join(
                self.trae_app_support,
                "User/workspaceStorage/f002a9b85f221075092022809f5a075f/state.vscdb"
            )
            
            if not os.path.exists(db_path):
                return False
            
            # 嘗試連接數據庫
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ItemTable")
            conn.close()
            return True
            
        except Exception:
            return False
    
    def check_git_repositories(self) -> dict:
        """檢查Git倉庫狀態"""
        repos_info = {
            "total_repos": 0,
            "accessible_repos": 0,
            "repositories": []
        }
        
        try:
            ckg_storage_path = os.path.join(
                self.trae_app_support,
                "User/globalStorage/.ckg/storage"
            )
            
            if not os.path.exists(ckg_storage_path):
                return repos_info
            
            for user_dir in os.listdir(ckg_storage_path):
                user_path = os.path.join(ckg_storage_path, user_dir)
                if not os.path.isdir(user_path):
                    continue
                
                for file in os.listdir(user_path):
                    if file.endswith("_codekg.db"):
                        repo_name = file.split("_")[0]
                        if repo_name and repo_name not in ["Shared"]:
                            repos_info["total_repos"] += 1
                            
                            # 檢查數據庫是否可訪問
                            db_path = os.path.join(user_path, file)
                            try:
                                conn = sqlite3.connect(db_path, timeout=2)
                                conn.close()
                                repos_info["accessible_repos"] += 1
                                repos_info["repositories"].append({
                                    "name": repo_name,
                                    "status": "accessible",
                                    "db_path": db_path
                                })
                            except Exception:
                                repos_info["repositories"].append({
                                    "name": repo_name,
                                    "status": "inaccessible",
                                    "db_path": db_path
                                })
            
            return repos_info
            
        except Exception:
            return repos_info
    
    def check_ssh_connection(self) -> bool:
        """檢查SSH連接到EC2服務器"""
        try:
            result = subprocess.run([
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                "-p", "41269",
                "alexchuang@serveo.net",
                "echo 'SSH連接測試'"
            ], capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
        except Exception:
            return False
    
    def get_connection_status(self) -> dict:
        """獲取完整的連接狀態"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "trae_running": self.check_trae_process(),
            "mcp_running": self.check_mcp_process(),
            "database_accessible": self.check_trae_database(),
            "ssh_connection": self.check_ssh_connection(),
            "repositories": self.check_git_repositories(),
            "connection_ready": False,
            "platform": "mac"
        }
        
        # 判斷是否準備好進行同步
        status["connection_ready"] = (
            status["trae_running"] and 
            status["mcp_running"] and 
            status["database_accessible"] and
            status["ssh_connection"]
        )
        
        return status
    
    def save_status(self, status: dict):
        """保存狀態到文件"""
        try:
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存狀態文件失敗: {e}")
    
    def load_status(self) -> dict:
        """從文件加載狀態"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def monitor_once(self) -> dict:
        """執行一次監控檢查"""
        status = self.get_connection_status()
        self.save_status(status)
        return status
    
    def print_status(self, status: dict):
        """打印狀態信息"""
        print(f"🕐 檢查時間: {status['timestamp']}")
        print(f"💻 平台: Mac端")
        print(f"📱 Trae運行: {'✅' if status['trae_running'] else '❌'}")
        print(f"🔗 MCP運行: {'✅' if status['mcp_running'] else '❌'}")
        print(f"💾 數據庫: {'✅' if status['database_accessible'] else '❌'}")
        print(f"🌐 SSH連接: {'✅' if status['ssh_connection'] else '❌'}")
        print(f"📦 倉庫: {status['repositories']['accessible_repos']}/{status['repositories']['total_repos']} 可訪問")
        print(f"🚀 同步就緒: {'✅' if status['connection_ready'] else '❌'}")
        
        if status['repositories']['repositories']:
            print("\n📋 倉庫列表:")
            for repo in status['repositories']['repositories']:
                status_icon = "✅" if repo['status'] == 'accessible' else "❌"
                print(f"   {status_icon} {repo['name']}")

def main():
    """主函數"""
    monitor = MCPConnectionMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        print("🔍 開始持續監控MCP與Trae連接狀態 (Mac端)...")
        print("按 Ctrl+C 停止監控\n")
        
        try:
            while True:
                status = monitor.monitor_once()
                monitor.print_status(status)
                print("-" * 50)
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n🛑 監控已停止")
    else:
        # 執行一次檢查
        status = monitor.monitor_once()
        monitor.print_status(status)
        
        # 返回適當的退出碼
        sys.exit(0 if status['connection_ready'] else 1)

if __name__ == "__main__":
    main()


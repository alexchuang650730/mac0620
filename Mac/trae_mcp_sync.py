#!/usr/bin/env python3
"""
Trae MCP Git Repository Auto-Sync Tool (Mac端)
當Mac終端MCP與Trae連接時自動執行倉庫同步

功能：
1. 監控MCP與Trae的連接狀態
2. 檢測到連接時自動觸發倉庫同步
3. 從Trae數據庫獲取倉庫列表
4. 通過SSH將倉庫同步到EC2服務器
"""

import os
import sys
import time
import json
import sqlite3
import subprocess
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Mac端配置
CONFIG = {
    "trae_app_support": "/Users/alexchuang/Library/Application Support/Trae",
    "target_server": "18.212.97.173",
    "target_directory": "/home/alexchuang/aiengine/trae/ec2/git",
    "github_username": "alexchuang650730",
    "ssh_key_path": "~/.ssh/id_rsa",
    "serveo_port": 41269,
    "check_interval": 30,  # 檢查間隔（秒）
    "log_file": "/tmp/trae_mcp_sync_mac.log",
    "sync_script_path": "/home/alexchuang/aiengine/trae/ec2/sync_repositories.py"
}

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["log_file"]),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TraeMCPSyncMonitor:
    def __init__(self):
        self.is_running = False
        self.last_sync_time = None
        self.known_repositories = set()
        
    def check_mcp_connection(self) -> bool:
        """檢查MCP與Trae的連接狀態"""
        try:
            # 檢查Trae進程是否運行
            result = subprocess.run(
                ["pgrep", "-f", "Trae"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.debug("Trae進程未運行")
                return False
            
            # 檢查MCP相關進程
            result = subprocess.run(
                ["pgrep", "-f", "mcp"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.debug("MCP進程未運行")
                return False
            
            # 檢查Trae數據庫是否可訪問
            db_path = os.path.join(
                CONFIG["trae_app_support"],
                "User/workspaceStorage/f002a9b85f221075092022809f5a075f/state.vscdb"
            )
            
            if not os.path.exists(db_path):
                logger.debug("Trae數據庫文件不存在")
                return False
            
            logger.info("✅ MCP與Trae連接正常")
            return True
            
        except Exception as e:
            logger.error(f"檢查MCP連接時出錯: {e}")
            return False
    
    def get_repositories_from_trae(self) -> List[Dict]:
        """從Trae數據庫獲取倉庫列表"""
        repositories = []
        
        try:
            # 從Trae的codekg數據庫中獲取倉庫信息
            ckg_storage_path = os.path.join(
                CONFIG["trae_app_support"],
                "User/globalStorage/.ckg/storage"
            )
            
            if not os.path.exists(ckg_storage_path):
                logger.warning("CodeKG存儲路徑不存在")
                return repositories
            
            # 遍歷所有用戶目錄
            for user_dir in os.listdir(ckg_storage_path):
                user_path = os.path.join(ckg_storage_path, user_dir)
                if not os.path.isdir(user_path):
                    continue
                
                # 查找codekg數據庫文件
                for file in os.listdir(user_path):
                    if file.endswith("_codekg.db"):
                        # 從文件名提取倉庫名
                        repo_name = file.split("_")[0]
                        if repo_name and repo_name not in ["Shared"]:
                            repositories.append({
                                "name": repo_name,
                                "github_url": f"https://github.com/{CONFIG['github_username']}/{repo_name}.git",
                                "db_file": os.path.join(user_path, file)
                            })
            
            # 添加已知的主要倉庫
            known_repos = [
                "powerauto.ai_0.53",
                "communitypowerautomation", 
                "powerauto_v0.3",
                "powerautomation",
                "final_integration_fixed",
                "communitypowerauto"
            ]
            
            for repo in known_repos:
                if not any(r["name"] == repo for r in repositories):
                    repositories.append({
                        "name": repo,
                        "github_url": f"https://github.com/{CONFIG['github_username']}/{repo}.git",
                        "db_file": None
                    })
            
            logger.info(f"發現 {len(repositories)} 個倉庫")
            return repositories
            
        except Exception as e:
            logger.error(f"從Trae獲取倉庫列表時出錯: {e}")
            return repositories
    
    def trigger_remote_sync(self, repositories: List[Dict]) -> bool:
        """觸發遠程同步"""
        try:
            logger.info("🚀 觸發EC2端倉庫同步...")
            
            # 準備倉庫列表數據
            repo_data = {
                "repositories": repositories,
                "sync_time": datetime.now().isoformat(),
                "source": "mac_trae_mcp"
            }
            
            # 將倉庫列表寫入臨時文件
            temp_file = "/tmp/trae_repo_list.json"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(repo_data, f, indent=2, ensure_ascii=False)
            
            # 通過SSH將文件傳輸到EC2並執行同步腳本
            ssh_cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-p", str(CONFIG["serveo_port"]),
                f"alexchuang@serveo.net"
            ]
            
            # 傳輸倉庫列表文件
            scp_cmd = [
                "scp",
                "-o", "StrictHostKeyChecking=no",
                "-P", str(CONFIG["serveo_port"]),
                temp_file,
                f"alexchuang@serveo.net:/tmp/trae_repo_list.json"
            ]
            
            result = subprocess.run(scp_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"傳輸倉庫列表失敗: {result.stderr}")
                return False
            
            # 執行遠程同步腳本
            remote_cmd = ssh_cmd + [
                f"python3 {CONFIG['sync_script_path']} --repo-list /tmp/trae_repo_list.json"
            ]
            
            result = subprocess.run(
                remote_cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30分鐘超時
            )
            
            if result.returncode == 0:
                logger.info("✅ 遠程同步執行成功")
                logger.info(f"同步輸出: {result.stdout}")
                return True
            else:
                logger.error(f"❌ 遠程同步執行失敗: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ 遠程同步執行超時")
            return False
        except Exception as e:
            logger.error(f"❌ 觸發遠程同步時出錯: {e}")
            return False
        finally:
            # 清理臨時文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def sync_all_repositories(self):
        """同步所有倉庫"""
        logger.info("🚀 開始倉庫同步任務")
        
        repositories = self.get_repositories_from_trae()
        if not repositories:
            logger.warning("未發現任何倉庫")
            return
        
        # 觸發遠程同步
        success = self.trigger_remote_sync(repositories)
        
        if success:
            self.last_sync_time = datetime.now()
            logger.info(f"🎉 倉庫同步任務完成")
        else:
            logger.error("❌ 倉庫同步任務失敗")
        
        # 生成同步報告
        self.generate_sync_report(repositories, success)
    
    def generate_sync_report(self, repositories: List[Dict], success: bool):
        """生成同步報告"""
        try:
            report = {
                "sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
                "total_repositories": len(repositories),
                "sync_success": success,
                "repositories": [repo["name"] for repo in repositories],
                "source": "mac_trae_mcp"
            }
            
            report_file = "/tmp/trae_sync_report_mac.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 同步報告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"生成同步報告時出錯: {e}")
    
    def start_monitoring(self):
        """開始監控"""
        logger.info("🔍 開始監控MCP與Trae連接狀態...")
        self.is_running = True
        
        while self.is_running:
            try:
                if self.check_mcp_connection():
                    # 檢查是否需要同步（避免過於頻繁）
                    if (self.last_sync_time is None or 
                        (datetime.now() - self.last_sync_time).seconds > 3600):  # 1小時間隔
                        
                        self.sync_all_repositories()
                    else:
                        logger.debug("距離上次同步時間過短，跳過本次同步")
                else:
                    logger.debug("MCP與Trae未連接，等待連接...")
                
                time.sleep(CONFIG["check_interval"])
                
            except KeyboardInterrupt:
                logger.info("收到中斷信號，停止監控...")
                self.stop_monitoring()
                break
            except Exception as e:
                logger.error(f"監控過程中出錯: {e}")
                time.sleep(CONFIG["check_interval"])
    
    def stop_monitoring(self):
        """停止監控"""
        self.is_running = False
        logger.info("🛑 監控已停止")

def main():
    """主函數"""
    print("🚀 Trae MCP Git Repository Auto-Sync Tool (Mac端)")
    print("=" * 60)
    
    # 檢查必要的依賴
    if not os.path.exists(CONFIG["trae_app_support"]):
        logger.error(f"Trae應用支持目錄不存在: {CONFIG['trae_app_support']}")
        sys.exit(1)
    
    # 創建監控器
    monitor = TraeMCPSyncMonitor()
    
    try:
        # 如果指定了命令行參數，執行一次性同步
        if len(sys.argv) > 1 and sys.argv[1] == "--sync-once":
            logger.info("執行一次性同步...")
            monitor.sync_all_repositories()
        else:
            # 開始持續監控
            monitor.start_monitoring()
    except Exception as e:
        logger.error(f"程序執行出錯: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


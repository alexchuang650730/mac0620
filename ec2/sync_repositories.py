#!/usr/bin/env python3
"""
Git Repository Sync Tool (EC2端)
接收Mac端的同步請求並執行實際的Git倉庫同步操作

功能：
1. 接收倉庫列表
2. 克隆/更新Git倉庫
3. 管理倉庫目錄
4. 生成同步報告
"""

import os
import sys
import json
import subprocess
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# EC2端配置
CONFIG = {
    "git_directory": "/home/alexchuang/aiengine/trae/ec2/git",
    "github_username": "alexchuang650730",
    "log_file": "/tmp/trae_sync_ec2.log",
    "backup_directory": "/home/alexchuang/aiengine/trae/ec2/backup",
    "max_concurrent_syncs": 3,
    "timeout": 300
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

class GitRepositorySync:
    def __init__(self):
        self.git_dir = Path(CONFIG["git_directory"])
        self.backup_dir = Path(CONFIG["backup_directory"])
        self.ensure_directories()
        
    def ensure_directories(self):
        """確保必要的目錄存在"""
        self.git_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Git目錄: {self.git_dir}")
        logger.info(f"備份目錄: {self.backup_dir}")
    
    def backup_repository(self, repo_name: str) -> bool:
        """備份現有倉庫"""
        try:
            repo_path = self.git_dir / repo_name
            if not repo_path.exists():
                return True
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{repo_name}_{timestamp}"
            
            result = subprocess.run([
                "cp", "-r", str(repo_path), str(backup_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 倉庫 {repo_name} 已備份到 {backup_path}")
                return True
            else:
                logger.error(f"❌ 備份倉庫 {repo_name} 失敗: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 備份倉庫 {repo_name} 時出錯: {e}")
            return False
    
    def clone_repository(self, repo: Dict) -> bool:
        """克隆新倉庫"""
        try:
            repo_name = repo["name"]
            repo_url = repo["github_url"]
            repo_path = self.git_dir / repo_name
            
            logger.info(f"🔄 克隆倉庫: {repo_name}")
            
            result = subprocess.run([
                "git", "clone", repo_url, str(repo_path)
            ], capture_output=True, text=True, timeout=CONFIG["timeout"])
            
            if result.returncode == 0:
                logger.info(f"✅ 倉庫 {repo_name} 克隆成功")
                return True
            else:
                logger.error(f"❌ 克隆倉庫 {repo_name} 失敗: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 克隆倉庫 {repo_name} 超時")
            return False
        except Exception as e:
            logger.error(f"❌ 克隆倉庫 {repo_name} 時出錯: {e}")
            return False
    
    def update_repository(self, repo: Dict) -> bool:
        """更新現有倉庫"""
        try:
            repo_name = repo["name"]
            repo_path = self.git_dir / repo_name
            
            logger.info(f"🔄 更新倉庫: {repo_name}")
            
            # 檢查是否為Git倉庫
            if not (repo_path / ".git").exists():
                logger.warning(f"⚠️ {repo_name} 不是Git倉庫，重新克隆")
                subprocess.run(["rm", "-rf", str(repo_path)], capture_output=True)
                return self.clone_repository(repo)
            
            # 執行git pull
            result = subprocess.run([
                "git", "-C", str(repo_path), "pull", "origin", "main"
            ], capture_output=True, text=True, timeout=CONFIG["timeout"])
            
            if result.returncode == 0:
                logger.info(f"✅ 倉庫 {repo_name} 更新成功")
                return True
            else:
                # 嘗試其他分支
                result = subprocess.run([
                    "git", "-C", str(repo_path), "pull", "origin", "master"
                ], capture_output=True, text=True, timeout=CONFIG["timeout"])
                
                if result.returncode == 0:
                    logger.info(f"✅ 倉庫 {repo_name} 更新成功 (master分支)")
                    return True
                else:
                    logger.error(f"❌ 更新倉庫 {repo_name} 失敗: {result.stderr}")
                    return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 更新倉庫 {repo_name} 超時")
            return False
        except Exception as e:
            logger.error(f"❌ 更新倉庫 {repo_name} 時出錯: {e}")
            return False
    
    def sync_repository(self, repo: Dict) -> bool:
        """同步單個倉庫"""
        try:
            repo_name = repo["name"]
            repo_path = self.git_dir / repo_name
            
            # 備份現有倉庫
            if repo_path.exists():
                self.backup_repository(repo_name)
                return self.update_repository(repo)
            else:
                return self.clone_repository(repo)
                
        except Exception as e:
            logger.error(f"❌ 同步倉庫 {repo['name']} 時出錯: {e}")
            return False
    
    def sync_repositories(self, repositories: List[Dict]) -> Dict:
        """同步所有倉庫"""
        logger.info(f"🚀 開始同步 {len(repositories)} 個倉庫")
        
        results = {
            "total": len(repositories),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for repo in repositories:
            repo_name = repo["name"]
            success = self.sync_repository(repo)
            
            results["details"].append({
                "name": repo_name,
                "success": success,
                "url": repo["github_url"]
            })
            
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"🎉 同步完成: {results['success']}/{results['total']} 成功")
        return results
    
    def cleanup_old_backups(self, days: int = 7):
        """清理舊備份"""
        try:
            logger.info(f"🧹 清理 {days} 天前的備份...")
            
            result = subprocess.run([
                "find", str(self.backup_dir), "-type", "d", 
                "-mtime", f"+{days}", "-exec", "rm", "-rf", "{}", "+"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ 舊備份清理完成")
            else:
                logger.warning(f"⚠️ 清理備份時出現警告: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ 清理備份時出錯: {e}")
    
    def generate_report(self, results: Dict, source_info: Dict = None) -> str:
        """生成同步報告"""
        try:
            report = {
                "sync_time": datetime.now().isoformat(),
                "platform": "ec2",
                "source": source_info or {},
                "results": results,
                "git_directory": str(self.git_dir),
                "backup_directory": str(self.backup_dir)
            }
            
            report_file = f"/tmp/trae_sync_report_ec2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 同步報告已保存: {report_file}")
            return report_file
            
        except Exception as e:
            logger.error(f"生成同步報告時出錯: {e}")
            return ""

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="Git Repository Sync Tool (EC2端)")
    parser.add_argument("--repo-list", help="倉庫列表JSON文件路徑")
    parser.add_argument("--cleanup", action="store_true", help="清理舊備份")
    parser.add_argument("--status", action="store_true", help="顯示倉庫狀態")
    
    args = parser.parse_args()
    
    print("🚀 Git Repository Sync Tool (EC2端)")
    print("=" * 50)
    
    sync_tool = GitRepositorySync()
    
    try:
        if args.cleanup:
            sync_tool.cleanup_old_backups()
            return
        
        if args.status:
            # 顯示倉庫狀態
            git_dir = Path(CONFIG["git_directory"])
            if git_dir.exists():
                repos = [d for d in git_dir.iterdir() if d.is_dir() and (d / ".git").exists()]
                print(f"📦 發現 {len(repos)} 個Git倉庫:")
                for repo in repos:
                    print(f"   📁 {repo.name}")
            else:
                print("📦 Git目錄不存在")
            return
        
        if args.repo_list:
            # 從文件讀取倉庫列表
            with open(args.repo_list, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            repositories = data.get("repositories", [])
            source_info = {
                "sync_time": data.get("sync_time"),
                "source": data.get("source")
            }
            
            if not repositories:
                logger.error("倉庫列表為空")
                sys.exit(1)
            
            # 執行同步
            results = sync_tool.sync_repositories(repositories)
            
            # 生成報告
            report_file = sync_tool.generate_report(results, source_info)
            
            # 清理舊備份
            sync_tool.cleanup_old_backups()
            
            print(f"\n📊 同步結果:")
            print(f"   總計: {results['total']}")
            print(f"   成功: {results['success']}")
            print(f"   失敗: {results['failed']}")
            print(f"   報告: {report_file}")
            
        else:
            print("❌ 請指定倉庫列表文件 (--repo-list)")
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"程序執行出錯: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


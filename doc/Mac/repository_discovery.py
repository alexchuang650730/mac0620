#!/usr/bin/env python3
"""
Trae Repository Discovery Tool
從Trae數據庫和文件中自動發現Git倉庫
"""

import os
import sys
import json
import sqlite3
import re
import glob
from pathlib import Path
from typing import List, Dict, Set
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TraeRepositoryDiscovery:
    def __init__(self, trae_app_support: str = "/Users/alexchuang/Library/Application Support/Trae"):
        self.trae_app_support = Path(trae_app_support)
        self.github_username = "alexchuang650730"
        self.repositories = set()
        
    def search_codekg_databases(self) -> Set[str]:
        """從CodeKG數據庫中搜索倉庫"""
        repos = set()
        
        try:
            ckg_storage_path = self.trae_app_support / "User/globalStorage/.ckg/storage"
            
            if not ckg_storage_path.exists():
                logger.warning(f"CodeKG存儲路徑不存在: {ckg_storage_path}")
                return repos
            
            logger.info(f"搜索CodeKG數據庫: {ckg_storage_path}")
            
            # 遍歷所有用戶目錄
            for user_dir in ckg_storage_path.iterdir():
                if not user_dir.is_dir():
                    continue
                
                # 查找codekg數據庫文件
                for db_file in user_dir.glob("*_codekg.db"):
                    repo_name = db_file.stem.replace("_codekg", "")
                    if repo_name and repo_name not in ["Shared", "temp"]:
                        repos.add(repo_name)
                        logger.info(f"發現倉庫 (CodeKG): {repo_name}")
            
            return repos
            
        except Exception as e:
            logger.error(f"搜索CodeKG數據庫時出錯: {e}")
            return repos
    
    def search_workspace_storage(self) -> Set[str]:
        """從工作區存儲中搜索倉庫"""
        repos = set()
        
        try:
            workspace_path = self.trae_app_support / "User/workspaceStorage"
            
            if not workspace_path.exists():
                logger.warning(f"工作區存儲路徑不存在: {workspace_path}")
                return repos
            
            logger.info(f"搜索工作區存儲: {workspace_path}")
            
            # 搜索所有.vscdb文件
            for db_file in workspace_path.rglob("*.vscdb"):
                try:
                    conn = sqlite3.connect(str(db_file), timeout=5)
                    cursor = conn.cursor()
                    
                    # 查找包含Git相關信息的表
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    
                    for table in tables:
                        table_name = table[0]
                        try:
                            cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
                            rows = cursor.fetchall()
                            
                            for row in rows:
                                row_str = str(row)
                                # 搜索GitHub倉庫模式
                                git_patterns = [
                                    r'github\.com[/:]' + self.github_username + r'[/:]([a-zA-Z0-9._-]+)',
                                    r'powerauto[a-zA-Z0-9._-]*',
                                    r'community[a-zA-Z0-9._-]*',
                                    r'automation[a-zA-Z0-9._-]*'
                                ]
                                
                                for pattern in git_patterns:
                                    matches = re.findall(pattern, row_str, re.IGNORECASE)
                                    for match in matches:
                                        if isinstance(match, str) and len(match) > 2:
                                            repos.add(match.strip())
                                            logger.info(f"發現倉庫 (WorkspaceStorage): {match}")
                        except Exception:
                            continue
                    
                    conn.close()
                    
                except Exception as e:
                    logger.debug(f"無法讀取數據庫 {db_file}: {e}")
                    continue
            
            return repos
            
        except Exception as e:
            logger.error(f"搜索工作區存儲時出錯: {e}")
            return repos
    
    def search_history_files(self) -> Set[str]:
        """從歷史文件中搜索倉庫"""
        repos = set()
        
        try:
            history_path = self.trae_app_support / "User/History"
            
            if not history_path.exists():
                logger.warning(f"歷史文件路徑不存在: {history_path}")
                return repos
            
            logger.info(f"搜索歷史文件: {history_path}")
            
            # 搜索所有JSON文件
            for json_file in history_path.rglob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # 搜索倉庫名稱模式
                        patterns = [
                            r'"([a-zA-Z0-9._-]*powerauto[a-zA-Z0-9._-]*)"',
                            r'"([a-zA-Z0-9._-]*community[a-zA-Z0-9._-]*)"',
                            r'"([a-zA-Z0-9._-]*automation[a-zA-Z0-9._-]*)"',
                            r'"([a-zA-Z0-9._-]*integration[a-zA-Z0-9._-]*)"',
                            r'github\.com[/:]' + self.github_username + r'[/:]([a-zA-Z0-9._-]+)'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for match in matches:
                                if len(match) > 2 and not match.startswith('.'):
                                    repos.add(match)
                                    logger.info(f"發現倉庫 (History): {match}")
                
                except Exception as e:
                    logger.debug(f"無法讀取文件 {json_file}: {e}")
                    continue
            
            return repos
            
        except Exception as e:
            logger.error(f"搜索歷史文件時出錯: {e}")
            return repos
    
    def search_input_database(self) -> Set[str]:
        """從輸入數據庫中搜索倉庫"""
        repos = set()
        
        try:
            # 搜索輸入數據庫
            input_db_pattern = self.trae_app_support / "User/workspaceStorage/*/state.vscdb"
            
            for db_file in glob.glob(str(input_db_pattern)):
                try:
                    conn = sqlite3.connect(db_file, timeout=5)
                    cursor = conn.cursor()
                    
                    # 查詢ItemTable中的輸入記錄
                    cursor.execute("SELECT value FROM ItemTable WHERE key LIKE '%input%'")
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        try:
                            data = json.loads(row[0])
                            if isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict):
                                        # 檢查multiMedia字段
                                        multi_media = item.get('multiMedia', [])
                                        for media in multi_media:
                                            if isinstance(media, dict):
                                                file_name = media.get('fileName', '')
                                                if file_name:
                                                    # 提取可能的倉庫名稱
                                                    repo_patterns = [
                                                        r'([a-zA-Z0-9._-]*powerauto[a-zA-Z0-9._-]*)',
                                                        r'([a-zA-Z0-9._-]*community[a-zA-Z0-9._-]*)',
                                                        r'([a-zA-Z0-9._-]*automation[a-zA-Z0-9._-]*)'
                                                    ]
                                                    
                                                    for pattern in repo_patterns:
                                                        matches = re.findall(pattern, file_name, re.IGNORECASE)
                                                        for match in matches:
                                                            if len(match) > 2:
                                                                repos.add(match)
                                                                logger.info(f"發現倉庫 (Input): {match}")
                        except Exception:
                            continue
                    
                    conn.close()
                    
                except Exception as e:
                    logger.debug(f"無法讀取輸入數據庫 {db_file}: {e}")
                    continue
            
            return repos
            
        except Exception as e:
            logger.error(f"搜索輸入數據庫時出錯: {e}")
            return repos
    
    def get_known_repositories(self) -> Set[str]:
        """獲取已知的倉庫列表"""
        known_repos = {
            "powerauto.ai_0.53",
            "communitypowerautomation",
            "powerauto_v0.3",
            "powerautomation",
            "final_integration_fixed",
            "communitypowerauto",
            "automation",
            "subtitles",
            "powerautoadmin",
            "healthcare",
            "ourdaily",
            "alexc"
        }
        
        logger.info(f"添加已知倉庫: {len(known_repos)} 個")
        return known_repos
    
    def filter_repositories(self, repos: Set[str]) -> List[Dict]:
        """過濾和格式化倉庫列表"""
        filtered_repos = []
        
        # 排除的模式
        exclude_patterns = [
            r'^[0-9]+$',  # 純數字
            r'^[a-f0-9]{8,}$',  # 哈希值
            r'^\.',  # 以點開頭
            r'^temp$|^test$|^shared$',  # 臨時文件
        ]
        
        for repo in repos:
            # 清理倉庫名稱
            clean_repo = repo.strip().lower()
            
            # 檢查是否應該排除
            should_exclude = False
            for pattern in exclude_patterns:
                if re.match(pattern, clean_repo, re.IGNORECASE):
                    should_exclude = True
                    break
            
            if not should_exclude and len(clean_repo) > 2:
                filtered_repos.append({
                    "name": repo.strip(),
                    "github_url": f"https://github.com/{self.github_username}/{repo.strip()}.git",
                    "source": "trae_discovery"
                })
        
        # 按名稱排序並去重
        seen = set()
        unique_repos = []
        for repo in sorted(filtered_repos, key=lambda x: x["name"]):
            if repo["name"] not in seen:
                seen.add(repo["name"])
                unique_repos.append(repo)
        
        return unique_repos
    
    def discover_repositories(self) -> List[Dict]:
        """執行完整的倉庫發現"""
        logger.info("🔍 開始從Trae中發現Git倉庫...")
        
        all_repos = set()
        
        # 從各個來源搜索倉庫
        all_repos.update(self.search_codekg_databases())
        all_repos.update(self.search_workspace_storage())
        all_repos.update(self.search_history_files())
        all_repos.update(self.search_input_database())
        all_repos.update(self.get_known_repositories())
        
        # 過濾和格式化
        repositories = self.filter_repositories(all_repos)
        
        logger.info(f"🎉 發現 {len(repositories)} 個倉庫")
        
        return repositories
    
    def save_repository_list(self, repositories: List[Dict], output_file: str = None) -> str:
        """保存倉庫列表到文件"""
        if output_file is None:
            output_file = "/tmp/trae_discovered_repositories.json"
        
        try:
            data = {
                "discovery_time": str(Path().cwd()),
                "total_repositories": len(repositories),
                "github_username": self.github_username,
                "repositories": repositories
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📁 倉庫列表已保存: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"保存倉庫列表時出錯: {e}")
            return ""

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Trae Repository Discovery Tool")
    parser.add_argument("--trae-path", default="/Users/alexchuang/Library/Application Support/Trae",
                       help="Trae應用支持目錄路徑")
    parser.add_argument("--output", help="輸出文件路徑")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("🔍 Trae Repository Discovery Tool")
    print("=" * 50)
    
    # 檢查Trae目錄是否存在
    if not os.path.exists(args.trae_path):
        logger.error(f"Trae目錄不存在: {args.trae_path}")
        sys.exit(1)
    
    # 創建發現工具
    discovery = TraeRepositoryDiscovery(args.trae_path)
    
    try:
        # 執行倉庫發現
        repositories = discovery.discover_repositories()
        
        # 保存結果
        output_file = discovery.save_repository_list(repositories, args.output)
        
        # 顯示結果
        print(f"\n📊 發現結果:")
        print(f"   總計倉庫: {len(repositories)}")
        print(f"   輸出文件: {output_file}")
        
        print(f"\n📋 倉庫列表:")
        for i, repo in enumerate(repositories, 1):
            print(f"   {i:2d}. {repo['name']}")
        
        return output_file
        
    except Exception as e:
        logger.error(f"倉庫發現過程中出錯: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


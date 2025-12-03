#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小苹果爬虫 - 自动获取class_id + 实时保存 + 屏蔽广告
"""

def install_missing_packages():
    import sys
    import subprocess
    import importlib
    required_packages = ["requests", "sqlite3"]
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            print(f"📦 正在安装缺失的模块: {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
install_missing_packages()

import requests
import json
import time
import sqlite3
import logging
import os
import sys
import threading
from datetime import datetime
from typing import Dict, List, Any, Set, Optional


class XpgRealTimeCrawler:
    def __init__(self, db_path: str = "xpg.db", json_path: str = "xpg_data.json"):
        print("🔧 正在初始化爬虫...")
        print(f"📁 当前工作目录: {os.getcwd()}")
        self.host = "http://asp.xpgtv.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G960U) AppleWebKit/537.36"
        }
        self.db_path = db_path
        self.json_path = json_path
        self.is_running = True
        self.is_paused = False
        self.ad_fingerprint = "dlNQWVppbnZXVVZsZnRhMnRpTkVNT2JaTnpyS010VEs="
        self.class_map = {}  # 存储 type_name -> class_id 的映射
        self.setup_logging()
        self.init_database()
        self.setup_signal_handler()
        self.start_key_listener()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('xpg_crawler.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def init_database(self):
        print(f"💾 正在连接数据库: {self.db_path}")
        self.db_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db_conn.execute('PRAGMA journal_mode = WAL;')
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cj (
                vod_id TEXT PRIMARY KEY,
                vod_name TEXT,
                vod_pic TEXT,
                type_name TEXT,
                class_id TEXT,        -- 新增字段
                vod_year TEXT,
                vod_area TEXT,
                vod_remarks TEXT,
                vod_actor TEXT,
                vod_director TEXT,
                vod_content TEXT,
                vod_play_from TEXT,
                vod_play_url TEXT,
                vod_pubdate TEXT,
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_progress (
                type_id TEXT PRIMARY KEY,
                last_page INTEGER DEFAULT 0,
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.db_conn.commit()
        self.logger.info(f"✅ 数据库初始化完成: {self.db_path}")

    def setup_signal_handler(self):
        import signal
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        print("\n\n🛑 检测到中断信号，正在保存进度...")
        self.is_running = False
        self.db_conn.commit()
        self.db_conn.close()
        print("✅ 进度已保存，程序退出")
        sys.exit(0)

    def fetch_json(self, url: str, params: Dict = None) -> Optional[Dict]:
        print(f"🌐 正在请求: {url}")
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 请求失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None

    def get_categories(self) -> List[Dict]:
        url = f"{self.host}/api.php/v2.vod/androidtypes"
        data = self.fetch_json(url)
        categories = data.get("data", []) if data else []
        # 构建 type_name -> type_id 的映射
        self.class_map = {cat["type_name"]: cat["type_id"] for cat in categories}
        return categories

    def get_last_page(self, type_id: str) -> int:
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT last_page FROM crawl_progress WHERE type_id = ?", (type_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

    def update_last_page(self, type_id: str, page: int):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO crawl_progress (type_id, last_page)
            VALUES (?, ?)
        ''', (type_id, page))
        self.db_conn.commit()

    def detect_total_pages(self, type_id: str, max_test: int = 10) -> int:
        for page in range(1, max_test + 1):
            url = f"{self.host}/api.php/v2.vod/androidfilter10086"
            params = {"page": page, "type": type_id}
            data = self.fetch_json(url, params)
            if not data or not data.get("data"):
                return page - 1
        return max_test

    def remove_ad_links(self, play_from: str, play_url: str) -> tuple:
        if not play_from or not play_url:
            return "", ""
        sources = play_from.split('#')
        urls = play_url.split('#')
        cleaned_sources = []
        cleaned_urls = []
        for src, url in zip(sources, urls):
            if self.ad_fingerprint not in url:
                cleaned_sources.append(src)
                cleaned_urls.append(url)
        if not cleaned_sources:
            return "", ""
        return '#'.join(cleaned_sources), '#'.join(cleaned_urls)

    def save_video(self, video: Dict) -> bool:
        try:
            video["vod_play_from"], video["vod_play_url"] = self.remove_ad_links(
                video["vod_play_from"], 
                video["vod_play_url"]
            )
            if not video["vod_play_url"]:
                print(f"⏭️ 跳过无有效播放源的视频: {video['vod_name']}")
                return False

            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO cj 
                (vod_id, vod_name, vod_pic, type_name, class_id, vod_year, vod_area, 
                 vod_remarks, vod_actor, vod_director, vod_content, 
                 vod_play_from, vod_play_url, vod_pubdate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video['vod_id'], video['vod_name'], video['vod_pic'],
                video['type_name'], video['class_id'],
                video.get('vod_year', ''),
                video.get('vod_area', ''), video.get('vod_remarks', ''),
                video.get('vod_actor', ''), video.get('vod_director', ''),
                video.get('vod_content', ''), video.get('vod_play_from', ''),
                video.get('vod_play_url', ''), video.get('vod_pubdate', '')
            ))
            self.db_conn.commit()
            print(f"✅ 保存成功: {video['vod_name']}")
            self.export_json_incremental()
            return True
        except Exception as e:
            print(f"❌ 保存失败 {video['vod_id']}: {e}")
            self.db_conn.rollback()
            return False

    def export_json_incremental(self):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT * FROM cj")
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            video_list = []
            for row in rows:
                video = dict(zip(columns, row))
                video = {k: (v if v is not None else "") for k, v in video.items()}
                ordered_video = {
                    "vod_id": video["vod_id"],
                    "vod_name": video["vod_name"],
                    "vod_pic": video["vod_pic"],
                    "type_name": video["type_name"],
                    "class_id": video["class_id"],        # 写入 class_id
                    "vod_year": video["vod_year"],
                    "vod_area": video["vod_area"],
                    "vod_remarks": video["vod_remarks"],
                    "vod_actor": video["vod_actor"],
                    "vod_director": video["vod_director"],
                    "vod_content": video["vod_content"],
                    "vod_play_from": video["vod_play_from"],
                    "vod_play_url": video["vod_play_url"],
                    "vod_pubdate": video["vod_pubdate"],
                    "updated_time": video["updated_time"]
                }
                video_list.append(ordered_video)
            result = {
                "list": video_list,
                "parse": 0,
                "jx": 0,
                "last_update": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            }
            temp_path = self.json_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.json_path)
            print(f"🔄 JSON文件已更新: {self.json_path}")
        except Exception as e:
            print(f"❌ JSON导出失败: {e}")

    def get_existing_ids(self) -> Set[str]:
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT vod_id FROM cj")
        return {row[0] for row in cursor.fetchall()}

    def crawl_category(self, type_id: str, type_name: str):
        existing_ids = self.get_existing_ids()
        start_page = self.get_last_page(type_id) + 1
        total_pages = self.detect_total_pages(type_id)
        print(f"📁 开始爬取分类: {type_name} (页码 {start_page}-{total_pages})")
        for page in range(start_page, total_pages + 1):
            if not self.is_running:
                self.update_last_page(type_id, page - 1)
                return
            while self.is_paused:
                time.sleep(1)
            url = f"{self.host}/api.php/v2.vod/androidfilter10086"
            params = {"page": page, "type": type_id}
            data = self.fetch_json(url, params)
            if not data or not data.get("data"):
                print(f"⚠️ 分类 {type_name} 第 {page} 页无数据")
                continue
            for item in data["data"]:
                vod_id = str(item.get("id", ""))
                if not vod_id or vod_id in existing_ids:
                    continue
                detail = self.get_video_detail(vod_id)
                video = {
                    "vod_id": vod_id,
                    "vod_name": item.get("name", ""),
                    "vod_pic": item.get("pic", ""),
                    "type_name": type_name,
                    "class_id": type_id,  # 直接写入分类 ID
                    "vod_year": item.get("year", ""),
                    "vod_area": item.get("area", ""),
                    "vod_remarks": item.get("updateInfo", ""),
                    "vod_actor": detail.get("actor", "") if detail else "",
                    "vod_director": detail.get("director", "") if detail else "",
                    "vod_content": detail.get("content", "") if detail else "",
                    "vod_play_from": "#".join(detail.get("play_from", [])) if detail else "",
                    "vod_play_url": "#".join(detail.get("play_url", [])) if detail else "",
                    "vod_pubdate": item.get("pubdate", "")
                }
                if self.save_video(video):
                    existing_ids.add(vod_id)
            self.update_last_page(type_id, page)
            time.sleep(0.5)

    def get_video_detail(self, vod_id: str) -> Optional[Dict]:
        url = f"{self.host}/api.php/v3.vod/androiddetail2"
        params = {"vod_id": vod_id}
        data = self.fetch_json(url, params)
        if not data or "data" not in data:
            return None
        detail = data["data"]
        play_from = []
        play_url = []
        for url_item in detail.get("urls", []):
            key = url_item.get("key", "").strip()
            url = url_item.get("url", "").strip()
            if key and url:
                play_from.append(key)
                play_url.append(f"{key}${url}")
        return {
            "actor": detail.get("actor", ""),
            "director": detail.get("director", ""),
            "content": detail.get("content", ""),
            "play_from": play_from,
            "play_url": play_url
        }

    def key_listener(self):
        while self.is_running:
            try:
                cmd = input().strip().lower()
                if cmd == 'p':
                    self.is_paused = not self.is_paused
                    status = "⏸️ 已暂停（按 p 继续）" if self.is_paused else "▶️ 继续爬取"
                    print(f"\n{status}\n")
            except:
                pass
            time.sleep(0.1)

    def start_key_listener(self):
        threading.Thread(target=self.key_listener, daemon=True).start()
        print("💡 提示：按 p 键可暂停/继续爬取")

    def run(self):
        print("🚀 开始爬取任务...")
        print("💡 按 Ctrl+C 可安全中断")
        categories = self.get_categories()
        print(f"✅ 获取到 {len(categories)} 个分类")
        for cat in categories:
            if not self.is_running:
                break
            type_id = cat["type_id"]
            type_name = cat["type_name"]
            self.crawl_category(type_id, type_name)
        self.db_conn.close()
        print("🎉 爬取完成！")


if __name__ == "__main__":
    if not os.path.exists("logs"):
        os.makedirs("logs")
    crawler = XpgRealTimeCrawler()
    try:
        crawler.run()
    except KeyboardInterrupt:
        crawler.signal_handler(None, None)

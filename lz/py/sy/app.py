# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2025/1/18
# @Desc    : TVBox爬虫转苹果CMS API - 完整标准版

import os
import sys
import importlib
import json
import inspect
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SPIDER_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spiders")
if SPIDER_FOLDER not in sys.path:
    sys.path.insert(0, SPIDER_FOLDER)

class TVBoxToAppleCMS:
    def __init__(self, spider_folder="spiders"):
        self.spider_folder = spider_folder
        self.spiders = self.load_spiders()
        print(f"✅ 加载爬虫完成，共 {len(self.spiders)} 个爬虫")
        for name in self.spiders.keys():
            print(f"   📺 {name}")

    def load_spiders(self):
        spiders = {}
        
        if not os.path.exists(self.spider_folder):
            print(f"❌ 爬虫目录不存在: {self.spider_folder}")
            return spiders
        
        for file in os.listdir(self.spider_folder):
            if file.endswith('.py') and file != '__init__.py' and not file.startswith('__'):
                spider_name = file[:-3]
                try:
                    module_path = os.path.join(self.spider_folder, file)
                    spec = importlib.util.spec_from_file_location(spider_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[spider_name] = module
                    spec.loader.exec_module(module)
                    
                    spider_class = None
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and name == 'Spider':
                            spider_class = obj
                            break
                    
                    if spider_class:
                        spider_instance = spider_class()
                        spiders[spider_name] = spider_instance
                        print(f"✅ 成功加载爬虫: {spider_name}")
                    else:
                        print(f"❌ 在 {file} 中未找到Spider类")
                        
                except Exception as e:
                    print(f"❌ 加载爬虫 {spider_name} 失败: {e}")
        
        return spiders
    
    def get_home_content(self, filter=True):
        """获取首页内容 - 苹果CMS标准格式"""
        result = {
            "code": 1,
            "msg": "成功",
            "page": 1,
            "pagecount": 1,
            "limit": 20,
            "total": 0,
            "class": [],
            "filters": {},
            "list": []
        }
        
        # 获取分类
        categories = self.get_categories()
        result["class"] = [{"type_id": cat["type_id"], "type_name": cat["type_name"]} for cat in categories]
        
        # 获取首页视频
        all_videos = []
        
        # 方法1: 从 homeVideoContent 获取
        for spider_name, spider in self.spiders.items():
            try:
                home_videos = spider.homeVideoContent()
                if home_videos and 'list' in home_videos:
                    videos = home_videos['list']
                    for video in videos:
                        formatted_video = {
                            'vod_id': f"{spider_name}__{video.get('vod_id', '')}",
                            'vod_name': video.get('vod_name', ''),
                            'vod_pic': video.get('vod_pic', ''),
                            'vod_remarks': video.get('vod_remarks', ''),
                            'vod_year': video.get('vod_year', ''),
                            'vod_score': video.get('vod_score', '0.0')
                        }
                        all_videos.append(formatted_video)
            except Exception as e:
                print(f"从 {spider_name} homeVideoContent 获取失败: {e}")
        
        # 方法2: 如果上面没数据，从分类获取
        if not all_videos:
            for spider_name, spider in self.spiders.items():
                try:
                    home_data = spider.homeContent({})
                    if 'class' in home_data and home_data['class']:
                        first_type = home_data['class'][0]
                        cat_data = spider.categoryContent(first_type['type_id'], 1, False, {})
                        if cat_data and 'list' in cat_data:
                            videos = cat_data['list']
                            for video in videos:
                                formatted_video = {
                                    'vod_id': f"{spider_name}__{video.get('vod_id', '')}",
                                    'vod_name': video.get('vod_name', ''),
                                    'vod_pic': video.get('vod_pic', ''),
                                    'vod_remarks': video.get('vod_remarks', ''),
                                    'vod_year': video.get('vod_year', ''),
                                    'vod_score': video.get('vod_score', '0.0')
                                }
                                all_videos.append(formatted_video)
                            if len(all_videos) >= 20:  # 达到20个就停止
                                break
                except Exception as e:
                    print(f"从 {spider_name} 分类获取失败: {e}")
        
        # 方法3: 如果还是没有数据，创建演示数据
        if not all_videos:
            all_videos = [
                {
                    'vod_id': 'demo__1',
                    'vod_name': '演示视频1',
                    'vod_pic': 'https://img.zcool.cn/community/010a875b830b4ba80121ab9657098c.jpg',
                    'vod_remarks': '演示',
                    'vod_year': '2024',
                    'vod_score': '8.0'
                },
                {
                    'vod_id': 'demo__2',
                    'vod_name': '演示视频2', 
                    'vod_pic': 'https://img.zcool.cn/community/0164a35b830b4ba80121ab96a5f00e.jpg',
                    'vod_remarks': '演示',
                    'vod_year': '2024',
                    'vod_score': '7.5'
                }
            ]
        
        result["list"] = all_videos[:50]  # 限制数量
        result["total"] = len(result["list"])
        
        print(f"首页返回: {len(result['class'])} 个分类, {len(result['list'])} 个视频")
        return result
    
    def get_categories(self):
        """获取所有分类"""
        categories = []
        type_id = 1
        
        for spider_name, spider in self.spiders.items():
            try:
                home_data = spider.homeContent({})
                if 'class' in home_data:
                    for cls in home_data['class']:
                        categories.append({
                            'type_id': type_id,
                            'type_name': f"{spider_name}-{cls['type_name']}",
                            'spider': spider_name,
                            'original_type_id': cls['type_id']
                        })
                        type_id += 1
                else:
                    categories.append({
                        'type_id': type_id,
                        'type_name': spider_name,
                        'spider': spider_name,
                        'original_type_id': '1'
                    })
                    type_id += 1
                    
            except Exception as e:
                print(f"获取 {spider_name} 分类失败: {e}")
                categories.append({
                    'type_id': type_id,
                    'type_name': spider_name,
                    'spider': spider_name,
                    'original_type_id': '1'
                })
                type_id += 1
        
        return categories
    
    def get_category_content(self, tid, pg=1, filter=True, ext=""):
        """获取分类内容 - 苹果CMS标准格式"""
        category = self.find_category_by_type_id(tid)
        if not category:
            return self._apple_error_response("分类不存在")
        
        spider = self.spiders.get(category['spider'])
        if not spider:
            return self._apple_error_response("爬虫不存在")
        
        try:
            extend = {}
            if ext:
                try:
                    extend = json.loads(base64.b64decode(ext).decode('utf-8'))
                except:
                    print("扩展参数解析失败")
            
            result = spider.categoryContent(category['original_type_id'], pg, False, extend)
            
            video_list = []
            if result and 'list' in result:
                for item in result['list']:
                    video_list.append({
                        'vod_id': f"{category['spider']}__{item.get('vod_id', '')}",
                        'vod_name': item.get('vod_name', ''),
                        'vod_pic': item.get('vod_pic', ''),
                        'vod_remarks': item.get('vod_remarks', ''),
                        'vod_year': item.get('vod_year', ''),
                        'vod_score': item.get('vod_score', '0.0')
                    })
            
            return self._apple_success_response(
                video_list, 
                result.get('page', pg),
                result.get('pagecount', 10),
                result.get('total', len(video_list))
            )
            
        except Exception as e:
            print(f"获取分类内容失败: {e}")
            return self._apple_error_response(str(e))
    
    def get_detail_content(self, ids):
        """获取详情内容 - 苹果CMS标准格式"""
        if '__' not in ids:
            return self._apple_error_response("视频ID格式错误")
        
        spider_name, original_id = ids.split('__', 1)
        spider = self.spiders.get(spider_name)
        if not spider:
            return self._apple_error_response("爬虫不存在")
        
        try:
            result = spider.detailContent([original_id])
            
            if not result or not result.get('list'):
                return self._apple_error_response("视频详情获取失败")
            
            item = result['list'][0]
            
            # 处理播放数据
            play_from = item.get('vod_play_from', '默认')
            play_url = item.get('vod_play_url', '')
            
            # 格式化播放信息
            if isinstance(play_from, list):
                play_from = "$$$".join(play_from)
            if isinstance(play_url, list):
                play_url = "$$$".join(play_url)
            
            detail = {
                'vod_id': ids,
                'vod_name': item.get('vod_name', ''),
                'vod_pic': item.get('vod_pic', ''),
                'vod_content': item.get('vod_content', ''),
                'vod_director': item.get('vod_director', ''),
                'vod_actor': item.get('vod_actor', ''),
                'vod_year': item.get('vod_year', ''),
                'vod_area': item.get('vod_area', ''),
                'vod_remarks': item.get('vod_remarks', ''),
                'vod_play_from': play_from,
                'vod_play_url': play_url
            }
            
            return self._apple_success_response([detail])
            
        except Exception as e:
            print(f"获取视频详情失败: {e}")
            return self._apple_error_response(str(e))
    
    def search_content(self, wd, quick=False, pg=1):
        """搜索内容 - 苹果CMS标准格式"""
        all_results = []
        
        for spider_name, spider in self.spiders.items():
            try:
                result = spider.searchContent(wd, quick, pg)
                if result and 'list' in result:
                    for item in result['list']:
                        all_results.append({
                            'vod_id': f"{spider_name}__{item.get('vod_id', '')}",
                            'vod_name': item.get('vod_name', ''),
                            'vod_pic': item.get('vod_pic', ''),
                            'vod_remarks': item.get('vod_remarks', ''),
                            'vod_year': item.get('vod_year', ''),
                            'vod_score': item.get('vod_score', '0.0')
                        })
            except Exception as e:
                print(f"搜索 {spider_name} 失败: {e}")
        
        return self._apple_success_response(all_results, pg)
    
    def find_category_by_type_id(self, type_id):
        """根据type_id查找分类信息"""
        categories = self.get_categories()
        for category in categories:
            if category['type_id'] == int(type_id):
                return category
        return None
    
    def _apple_success_response(self, data, page=1, pagecount=10, total=None):
        """苹果CMS成功响应格式"""
        if total is None:
            total = len(data)
        return {
            'code': 1,
            'msg': '成功',
            'page': page,
            'pagecount': pagecount,
            'limit': 20,
            'total': total,
            'list': data
        }
    
    def _apple_error_response(self, message):
        """苹果CMS错误响应格式"""
        return {
            'code': 0,
            'msg': message,
            'list': []
        }

# 全局转换器实例
converter = TVBoxToAppleCMS("spiders")

@app.route('/')
def index():
    """首页 - 苹果CMS标准格式"""
    try:
        result = converter.get_home_content(filter=True)
        return jsonify(result)
    except Exception as e:
        return jsonify(converter._apple_error_response(str(e)))

@app.route('/api.php')
def api_php():
    """兼容api.php路径"""
    return handle_api_request()

@app.route('/json.php')
def json_php():
    """兼容json.php路径"""
    return handle_api_request()

@app.route('/vod')
def vod():
    """苹果CMS VOD接口兼容"""
    return handle_api_request()

def handle_api_request():
    """处理API请求 - 苹果CMS标准格式"""
    ac = request.args.get('ac')
    t = request.args.get('t', '1')
    pg = request.args.get('pg', '1')
    ids = request.args.get('ids', '')
    wd = request.args.get('wd', '').strip()
    quick = request.args.get('quick', 'false').lower() == 'true'
    ext = request.args.get('ext', '')
    
    print(f"API请求: ac={ac}, t={t}, pg={pg}, ids={ids}, wd={wd}")
    
    try:
        if ac == 'detail' and ids:
            # 视频详情
            result = converter.get_detail_content(ids)
            return jsonify(result)
        
        elif ac == 'list' and wd:
            # 搜索
            result = converter.search_content(wd, quick, int(pg))
            return jsonify(result)
        
        elif ac == 'list':
            # 分类列表
            result = converter.get_category_content(t, int(pg), True, ext)
            return jsonify(result)
        
        elif ac == 'video' and ids:
            # 播放地址（兼容性）
            result = converter.get_detail_content(ids)
            return jsonify(result)
        
        else:
            # 默认返回首页
            result = converter.get_home_content(filter=True)
            return jsonify(result)
            
    except Exception as e:
        print(f"API处理错误: {e}")
        return jsonify(converter._apple_error_response(str(e)))

@app.route('/status')
def status():
    """服务状态检查 - 苹果CMS标准格式"""
    return jsonify({
        "code": 1,
        "msg": "服务正常",
        "version": "1.0",
        "spiders_count": len(converter.spiders),
        "api_url": "http://139.185.42.4:5000/"
    })

# 健康检查接口
@app.route('/ping')
def ping():
    return jsonify({"code": 1, "msg": "pong"})

if __name__ == '__main__':
    print("TVBox转苹果CMS API服务启动...")
    print("=" * 50)
    print("API访问地址: http://139.185.42.4:5000/")
    print("状态检查: http://139.185.42.4:5000/status")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
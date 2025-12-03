# -*- coding: utf-8 -*-
# @Author  : AI Assistant
# @Time    : 2025/1/18
# @Desc    : TVBox爬虫转苹果CMS API

import os
import sys
import importlib
import json
import inspect
from flask import Flask, request, jsonify

app = Flask(__name__)

class TVBoxToAppleCMS:
    def __init__(self, spider_folder="."):
        self.spider_folder = spider_folder
        self.spiders = self.load_spiders()
    
    def load_spiders(self):
        """加载所有爬虫"""
        spiders = {}
        
        # 获取文件夹内所有py文件
        for file in os.listdir(self.spider_folder):
            if file.endswith('.py') and file != '__init__.py' and file != 'apple_cms_api.py':
                spider_name = file[:-3]  # 移除.py
                try:
                    # 动态导入爬虫模块
                    spec = importlib.util.spec_from_file_location(spider_name, os.path.join(self.spider_folder, file))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 查找Spider类
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and name == 'Spider':
                            spiders[spider_name] = obj()
                            break
                except Exception as e:
                    print(f"加载爬虫 {spider_name} 失败: {e}")
        
        return spiders
    
    def get_categories(self):
        """获取所有分类（苹果CMS格式）"""
        categories = []
        type_id = 1
        
        for spider_name, spider in self.spiders.items():
            try:
                # 调用爬虫的homeContent方法
                home_data = spider.homeContent({})
                if 'class' in home_data:
                    for cls in home_data['class']:
                        categories.append({
                            'type_id': str(type_id),
                            'type_name': f"{spider_name}-{cls['type_name']}",
                            'spider': spider_name,
                            'original_type_id': cls['type_id']
                        })
                        type_id += 1
            except Exception as e:
                print(f"获取 {spider_name} 分类失败: {e}")
        
        return categories
    
    def get_video_list(self, type_id, page=1, **filters):
        """获取视频列表（苹果CMS格式）"""
        # 查找对应的爬虫和原始分类
        category = self.find_category_by_type_id(type_id)
        if not category:
            return self._error_response("分类不存在")
        
        spider = self.spiders.get(category['spider'])
        if not spider:
            return self._error_response("爬虫不存在")
        
        try:
            # 调用爬虫的categoryContent方法
            result = spider.categoryContent(
                category['original_type_id'], 
                page, 
                {}, 
                filters
            )
            
            # 转换为苹果CMS格式
            video_list = []
            for item in result.get('list', []):
                video_list.append({
                    'vod_id': f"{category['spider']}__{item['vod_id']}",
                    'vod_name': item['vod_name'],
                    'vod_pic': item['vod_pic'],
                    'vod_remarks': item.get('vod_remarks', ''),
                    'vod_year': item.get('vod_year', ''),
                    'vod_score': '0.0'
                })
            
            return self._success_response(video_list, page)
            
        except Exception as e:
            return self._error_response(str(e))
    
    def get_video_detail(self, vod_id):
        """获取视频详情（苹果CMS格式）"""
        # 解析vod_id格式: spider__original_id
        if '__' not in vod_id:
            return self._error_response("视频ID格式错误")
        
        spider_name, original_id = vod_id.split('__', 1)
        spider = self.spiders.get(spider_name)
        if not spider:
            return self._error_response("爬虫不存在")
        
        try:
            # 调用爬虫的detailContent方法
            result = spider.detailContent([original_id])
            
            if not result.get('list'):
                return self._error_response("视频详情获取失败")
            
            item = result['list'][0]
            
            # 转换为苹果CMS格式
            detail = {
                'vod_id': vod_id,
                'vod_name': item['vod_name'],
                'vod_pic': item['vod_pic'],
                'vod_content': item.get('vod_content', ''),
                'vod_director': item.get('vod_director', ''),
                'vod_actor': item.get('vod_actor', ''),
                'vod_year': item.get('vod_year', ''),
                'vod_area': item.get('vod_area', ''),
                'vod_remarks': item.get('vod_remarks', ''),
                'vod_play_from': item.get('vod_play_from', '默认').split('$$$'),
                'vod_play_url': self._format_play_url(item.get('vod_play_url', ''))
            }
            
            return self._success_response([detail])
            
        except Exception as e:
            return self._error_response(str(e))
    
    def search_video(self, keyword, page=1):
        """搜索视频（苹果CMS格式）"""
        all_results = []
        
        for spider_name, spider in self.spiders.items():
            try:
                result = spider.searchContent(keyword, False, page)
                for item in result.get('list', []):
                    all_results.append({
                        'vod_id': f"{spider_name}__{item['vod_id']}",
                        'vod_name': item['vod_name'],
                        'vod_pic': item['vod_pic'],
                        'vod_remarks': item.get('vod_remarks', ''),
                        'vod_year': item.get('vod_year', ''),
                        'vod_score': '0.0'
                    })
            except Exception as e:
                print(f"搜索 {spider_name} 失败: {e}")
        
        return self._success_response(all_results, page)
    
    def find_category_by_type_id(self, type_id):
        """根据type_id查找分类信息"""
        categories = self.get_categories()
        for category in categories:
            if category['type_id'] == str(type_id):
                return category
        return None
    
    def _format_play_url(self, play_url):
        """格式化播放URL为苹果CMS格式"""
        if '#' in play_url:
            return play_url.split('#')
        return [play_url]
    
    def _success_response(self, data, page=1):
        """成功响应格式"""
        return {
            'code': 1,
            'msg': '成功',
            'page': page,
            'pagecount': 10,  # 默认值
            'limit': 20,
            'total': len(data),
            'list': data
        }
    
    def _error_response(self, message):
        """错误响应格式"""
        return {
            'code': 0,
            'msg': message,
            'list': []
        }

# 全局转换器实例
converter = TVBoxToAppleCMS(".")

# Flask路由
@app.route('/')
def index():
    return jsonify({
        "code": 1,
        "msg": "TVBox转苹果CMS API服务运行中",
        "endpoints": {
            "分类列表": "/api?ac=category",
            "视频列表": "/api?ac=list&t=分类ID&pg=页码",
            "视频详情": "/api?ac=detail&ids=视频ID",
            "视频搜索": "/api?ac=list&wd=关键词&pg=页码"
        }
    })

@app.route('/api')
def api():
    """苹果CMS标准API接口"""
    ac = request.args.get('ac', '')
    t = request.args.get('t', '1')
    pg = request.args.get('pg', '1')
    ids = request.args.get('ids', '')
    wd = request.args.get('wd', '')
    
    try:
        if ac == 'category':
            # 获取分类
            categories = converter.get_categories()
            return jsonify(converter._success_response(categories))
        
        elif ac == 'list' and wd:
            # 搜索视频
            result = converter.search_video(wd, int(pg))
            return jsonify(result)
        
        elif ac == 'list':
            # 获取视频列表
            result = converter.get_video_list(t, int(pg))
            return jsonify(result)
        
        elif ac == 'detail' and ids:
            # 获取视频详情
            result = converter.get_video_detail(ids)
            return jsonify(result)
        
        else:
            return jsonify(converter._error_response("参数错误"))
            
    except Exception as e:
        return jsonify(converter._error_response(str(e)))

if __name__ == '__main__':
    # 启动服务
    print("TVBox转苹果CMS API服务启动...")
    print("访问地址: http://127.0.0.1:5000/api?ac=category")
    app.run(host='0.0.0.0', port=5000, debug=False)
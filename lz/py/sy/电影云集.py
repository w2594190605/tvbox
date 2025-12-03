import sys
import json
import re
import requests
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def __init__(self):
        self.name = "电影云集"
        self.host = "https://dyyjpro.com"
        self.timeout = 10
        self.limit = 20
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.default_image = "https://picsum.photos/300/400"
    
    def getName(self):
        return self.name
    
    def init(self, extend=""):
        print(f"============{extend}============")
    
    def homeContent(self, filter):
        return {
            'class': [
                {"type_name": "电影", "type_id": "dianying"},
                {"type_name": "剧集", "type_id": "ju"},
                {"type_name": "动漫", "type_id": "dongman"},
                {"type_name": "综艺", "type_id": "zongyi"},
                {"type_name": "短剧", "type_id": "duanju"},
                {"type_name": "学习", "type_id": "xuexi"},
                {"type_name": "读物", "type_id": "duwu"},
                {"type_name": "音频", "type_id": "yinpin"}
            ]
        }
    
    def categoryContent(self, tid, pg, filter, extend):
        result = {'list': [], 'page': pg, 'pagecount': 9999, 'limit': self.limit, 'total': 999999}
        
        try:
            # 构建URL
            if pg == 1:
                url = f"{self.host}/category/{tid}"
            else:
                url = f"{self.host}/category/{tid}/page/{pg}"
            
            print(f"分类URL: {url}")
            
            rsp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if rsp.status_code != 200:
                print(f"HTTP状态码错误: {rsp.status_code}")
                return result
            
            html = rsp.text
            
            # 方法1：使用正则表达式提取文章项
            videos = []
            
            # 简化模式，只提取关键信息
            pattern = r'<article[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>.*?</article>'
            
            matches = re.findall(pattern, html, re.S)
            if matches:
                print(f"找到 {len(matches)} 个项目")
                for match in matches:
                    if len(match) >= 3:
                        href = match[0]
                        pic = match[1]
                        name = match[2]
                        
                        # 清理标题
                        if name:
                            name = re.sub(r'<[^>]+>', '', name).strip()
                        
                        # 确保href是完整的URL
                        if href and not href.startswith('http'):
                            href = f"{self.host}{href}" if href.startswith('/') else f"{self.host}/{href}"
                        
                        # 确保图片URL是完整的
                        if pic and not pic.startswith('http'):
                            pic = f"{self.host}{pic}" if pic.startswith('/') else f"{self.host}/{pic}"
                        
                        if href and name:
                            videos.append({
                                "vod_id": href,
                                "vod_name": name,
                                "vod_pic": pic or self.default_image,
                                "vod_remarks": "",
                                "vod_content": name
                            })
            
            # 方法2：如果正则没找到，尝试从页面中提取所有文章链接
            if not videos:
                print("尝试方法2：提取所有文章链接")
                # 查找所有文章链接
                article_pattern = r'<a[^>]*href="([^"]+/\d+\.html)"[^>]*>'
                article_links = re.findall(article_pattern, html)
                article_links = list(set(article_links))  # 去重
                
                for link in article_links[:10]:  # 限制数量
                    if not link.startswith('http'):
                        full_link = f"{self.host}{link}" if link.startswith('/') else f"{self.host}/{link}"
                    else:
                        full_link = link
                    
                    # 从链接中提取标题
                    title = re.sub(r'\.html$', '', link.split('/')[-1])
                    title = title.replace('-', ' ').replace('_', ' ')
                    
                    # 尝试从链接附近提取图片
                    img_pattern = fr'<a[^>]*href="{link}"[^>]*>.*?<img[^>]*src="([^"]*)"'
                    img_match = re.search(img_pattern, html, re.S)
                    pic = img_match.group(1) if img_match else self.default_image
                    
                    if pic and not pic.startswith('http'):
                        pic = f"{self.host}{pic}" if pic.startswith('/') else f"{self.host}/{pic}"
                    
                    videos.append({
                        "vod_id": full_link,
                        "vod_name": title,
                        "vod_pic": pic,
                        "vod_remarks": "",
                        "vod_content": title
                    })
            
            result['list'] = videos
            
            if videos:
                print(f"成功获取 {len(videos)} 个视频")
            else:
                print("警告：没有找到任何视频")
                
        except Exception as e:
            print(f"categoryContent error: {e}")
        
        return result
    
    def detailContent(self, array):
        result = {'list': []}
        if not array:
            return result
        
        try:
            vod_id = array[0]
            url = vod_id if vod_id.startswith('http') else f"{self.host}{vod_id}"
            
            print(f"正在访问详情页: {url}")
            
            rsp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if rsp.status_code != 200:
                raise Exception(f"HTTP状态码: {rsp.status_code}")
            
            html = rsp.text
            
            # 提取标题
            title = "电影云集资源"
            title_patterns = [
                r'<h1[^>]*class="post-title"[^>]*>(.*?)</h1>',
                r'<h1[^>]*>(.*?)</h1>',
                r'<title[^>]*>(.*?)</title>'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, html, re.S | re.I)
                if match:
                    title = match.group(1).strip()
                    title = re.sub(r'<[^>]+>', '', title)
                    break
            
            print(f"提取到标题: {title}")
            
            # 提取内容区域
            content_html = ""
            content_patterns = [
                r'<div[^>]*class="post-content"[^>]*>(.*?)</div>',
                r'<article[^>]*class="post[^"]*"[^>]*>(.*?)</article>',
                r'<div[^>]*class="entry-content"[^>]*>(.*?)</div>'
            ]
            
            for pattern in content_patterns:
                match = re.search(pattern, html, re.S)
                if match:
                    content_html = match.group(1)
                    break
            
            # 如果没有找到内容区域，使用整个页面
            if not content_html:
                content_html = html
            
            # 提取所有网盘链接（改进版本）
            netdisk_patterns = [
                ('百度网盘', r'pan\.baidu\.com/s/[a-zA-Z0-9_-]+'),
                ('夸克网盘', r'pan\.quark\.cn/s/[a-zA-Z0-9]+'),
                ('阿里云盘', r'aliyundrive\.com/s/[a-zA-Z0-9]+'),
                ('迅雷云盘', r'pan\.xunlei\.com/s/[a-zA-Z0-9]+'),
                ('115网盘', r'115\.com/s/[a-zA-Z0-9]+'),
                ('磁力链接', r'magnet:\?xt=urn:btih:[a-zA-Z0-9]{32,}'),
                ('电驴链接', r'ed2k://[^\s"\']+')
            ]
            
            play_items = {}
            
            for netdisk_name, pattern in netdisk_patterns:
                matches = re.findall(pattern, content_html, re.I)
                if matches:
                    # 对链接去重
                    unique_matches = list(dict.fromkeys(matches))
                    print(f"找到 {len(unique_matches)} 个{netdisk_name}链接")
                    
                    # 为每个链接构建推送项
                    formatted_links = []
                    for i, link in enumerate(unique_matches, 1):
                        # 确保链接有完整的协议
                        if link.startswith('magnet:') or link.startswith('ed2k:'):
                            full_link = link
                        else:
                            if not link.startswith(('http://', 'https://')):
                                full_link = f"https://{link}"
                            else:
                                full_link = link
                        
                        # 查找提取码
                        password = ''
                        link_pos = content_html.find(link)
                        if link_pos != -1:
                            # 在链接附近查找提取码
                            start = max(0, link_pos - 50)
                            end = min(len(content_html), link_pos + len(link) + 50)
                            nearby = content_html[start:end]
                            pwd_match = re.search(r'[提取码|密码|pwd][：:]\s*([a-zA-Z0-9]{4})', nearby, re.I)
                            if pwd_match:
                                password = pwd_match.group(1)
                        
                        # 构建显示名称
                        display_name = f"第{i}集"
                        if password:
                            display_name = f"第{i}集(码:{password})"
                        
                        # 关键：构建推送链接 - 确保格式正确
                        push_link = f"push://{full_link}"
                        
                        formatted_links.append(f"{display_name}${push_link}")
                    
                    if formatted_links:
                        play_items[netdisk_name] = formatted_links
            
            # 构建播放源和播放地址
            if play_items:
                play_sources = []
                play_urls = []
                
                for source, links in play_items.items():
                    play_sources.append(source)
                    play_urls.append('#'.join(links))
                
                play_from = '$$$'.join(play_sources)
                play_url = '$$$'.join(play_urls)
                print(f"构建播放源: {play_from}")
            else:
                print("没有找到网盘链接")
                # 尝试提取普通链接
                http_links = re.findall(r'href=["\'](https?://[^"\']+)["\']', content_html)
                if http_links:
                    play_sources = ['普通链接']
                    formatted_links = []
                    for i, link in enumerate(http_links[:3], 1):
                        formatted_links.append(f"链接{i}${link}")
                    play_urls = ['#'.join(formatted_links)]
                    play_from = '$$$'.join(play_sources)
                    play_url = '$$$'.join(play_urls)
                else:
                    play_from = '电影云集'
                    play_url = '暂无资源$#'
            
            # 提取简介
            vod_content = title
            if content_html:
                # 移除HTML标签
                text_content = re.sub(r'<[^>]+>', ' ', content_html)
                text_content = re.sub(r'\s+', ' ', text_content).strip()
                if len(text_content) > 50:
                    vod_content = text_content[:150] + "..."
            
            # 提取图片 - 优先从页面中提取
            vod_pic = self.default_image
            pic_patterns = [
                r'<meta[^>]*property="og:image"[^>]*content="([^"]*)"',
                r'<meta[^>]*name="og:image"[^>]*content="([^"]*)"',
                r'<img[^>]*class="[^"]*wp-post-image[^"]*"[^>]*src="([^"]*)"',
                r'<img[^>]*src="([^"]*)"[^>]*class="[^"]*featured[^"]*"'
            ]
            
            for pattern in pic_patterns:
                match = re.search(pattern, html, re.I)
                if match:
                    pic_url = match.group(1).strip()
                    if pic_url and not pic_url.startswith('data:'):
                        if not pic_url.startswith('http'):
                            pic_url = f"{self.host}{pic_url}" if pic_url.startswith('/') else f"{self.host}/{pic_url}"
                        vod_pic = pic_url
                        print(f"提取到图片: {pic_url}")
                        break
            
            # 创建视频项
            vod_item = {
                'vod_id': url,
                'vod_name': title,
                'vod_pic': vod_pic,
                'vod_content': vod_content,
                'vod_remarks': f"共{len(play_items)}个网盘源" if play_items else "暂无网盘资源",
                'vod_play_from': play_from,
                'vod_play_url': play_url
            }
            
            result['list'].append(vod_item)
            print(f"成功创建视频项: {title}")
            
        except Exception as e:
            print(f"detailContent error: {e}")
            result['list'].append({
                'vod_id': 'error',
                'vod_name': '电影云集资源',
                'vod_pic': self.default_image,
                'vod_content': f'访问失败: {str(e)}',
                'vod_remarks': '',
                'vod_play_from': '电影云集',
                'vod_play_url': '暂无资源$#'
            })
        
        return result
    
    def searchContent(self, key, quick, pg):
        result = {'list': []}
        
        try:
            # URL编码搜索关键词
            import urllib.parse
            encoded_key = urllib.parse.quote(key)
            
            if pg == 1:
                search_url = f"{self.host}/?s={encoded_key}"
            else:
                search_url = f"{self.host}/page/{pg}/?s={encoded_key}"
            
            print(f"搜索URL: {search_url}")
            
            rsp = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            if rsp.status_code == 200:
                html = rsp.text
                
                # 使用与categoryContent相同的方法提取搜索结果
                videos = []
                pattern = r'<article[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>.*?</article>'
                matches = re.findall(pattern, html, re.S)
                
                for match in matches:
                    if len(match) >= 3:
                        href = match[0]
                        pic = match[1]
                        name = match[2]
                        
                        if href and not href.startswith('http'):
                            href = f"{self.host}{href}" if href.startswith('/') else f"{self.host}/{href}"
                        
                        if pic and not pic.startswith('http'):
                            pic = f"{self.host}{pic}" if pic.startswith('/') else f"{self.host}/{pic}"
                        
                        if href and name:
                            name = re.sub(r'<[^>]+>', '', name).strip()
                            videos.append({
                                "vod_id": href,
                                "vod_name": name,
                                "vod_pic": pic or self.default_image,
                                "vod_remarks": "",
                                "vod_content": name
                            })
                
                result['list'] = videos
                print(f"搜索到 {len(videos)} 个结果")
                
        except Exception as e:
            print(f"searchContent error: {e}")
        
        return result
    
    def playerContent(self, flag, id, vipFlags):
        """
        播放器内容处理
        注意：对于网盘链接，我们使用push协议
        """
        print(f"playerContent被调用: flag={flag}, id={id[:100]}...")
        
        try:
            # 对于所有链接，都使用push协议
            # 移除可能存在的重复push://前缀
            if id.startswith("push://"):
                clean_id = id
            else:
                clean_id = f"push://{id}"
            
            # 如果链接包含提取码信息，确保格式正确
            if " 提取码:" in clean_id:
                # push协议应该可以正确处理带提取码的链接
                pass
            
            return {
                "parse": 0,  # 0表示不解析，直接推送
                "playUrl": "",
                "url": clean_id,
                "header": ""
            }
            
        except Exception as e:
            print(f"playerContent error: {e}")
            return {
                "parse": 0,
                "playUrl": "",
                "url": "push://error",
                "header": ""
            }


# 测试代码
if __name__ == '__main__':
    spider = Spider()
    
    # 测试首页
    print("首页分类:")
    home = spider.homeContent({})
    for cls in home['class']:
        print(f"  {cls['type_name']} -> {cls['type_id']}")
    
    # 测试分类页
    print("\n测试分类页:")
    category = spider.categoryContent("dianying", 1, {}, {})
    if category['list']:
        print(f"找到 {len(category['list'])} 个视频")
        for i, vod in enumerate(category['list'][:3], 1):
            print(f"  {i}. {vod['vod_name']}")
            print(f"     图片: {vod['vod_pic'][:50]}...")
    else:
        print("分类页没有数据")
    
    # 测试详情页
    print("\n测试详情页:")
    # 使用一个已知的URL进行测试
    test_url = "https://dyyjpro.com/83556.html"
    detail = spider.detailContent([test_url])
    if detail['list']:
        vod = detail['list'][0]
        print(f"标题: {vod['vod_name']}")
        print(f"图片: {vod['vod_pic']}")
        print(f"播放源: {vod['vod_play_from']}")
        # 只显示部分播放地址
        play_urls = vod['vod_play_url'].split('$$$')
        for i, play_url in enumerate(play_urls):
            print(f"播放源{i+1}: {play_url[:80]}...")
    else:
        print("详情页没有数据")
import re
import sys
import urllib.parse
import base64
import json
from pyquery import PyQuery as pq
import requests

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def __init__(self):
        super().__init__()
        self.base_url = "http://oxax.tv"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': self.base_url
        })
    
    def getName(self):
        return "成人电视直播"
    
    def init(self, extend):
        pass
        
    def homeContent(self, filter):
        result = {}
        classes = [
            {'type_name': '成人直播', 'type_id': '1'},
            {'type_name': '所有频道', 'type_id': '2'}
        ]
        result['class'] = classes
        return result

    def homeVideoContent(self):
        result = {}
        videos = []
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            html_content = response.text
            
            doc = pq(html_content)
            items = doc('.tv_kan_gl .tv_sp')
            
            for i, item in enumerate(items.items()[:20]):
                title = item.attr('title')
                href = item.find('a').attr('href')
                
                if title and href:
                    full_url = self.base_url + href if href.startswith('/') else self.base_url + '/' + href
                    
                    # 提取真实的图片背景
                    try:
                        img_element = item.find('p')
                        if img_element and img_element.attr('style'):
                            style = img_element.attr('style')
                            img_match = re.search(r'background-position:\s*0px\s*(-?\d+)px', style)
                            if img_match:
                                position = img_match.group(1)
                                # 根据位置猜测频道图片
                                img_url = f"{self.base_url}/images/channels/{position}.jpg"
                            else:
                                img_url = f"https://via.placeholder.com/300x200/FF69B4/FFFFFF?text={urllib.parse.quote(title[:15])}"
                        else:
                            img_url = f"https://via.placeholder.com/300x200/FF69B4/FFFFFF?text={urllib.parse.quote(title[:15])}"
                    except:
                        img_url = f"https://via.placeholder.com/300x200/FF69B4/FFFFFF?text={urllib.parse.quote(title[:15])}"
                    
                    videos.append({
                        'vod_id': href,
                        'vod_name': title,
                        'vod_pic': img_url,
                        'vod_remarks': '直播频道'
                    })
        except Exception as e:
            print(f"首页获取失败: {e}")
            
        if videos:
            result['list'] = videos
            
        return result

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        videos = []
        
        try:
            if tid == '1':
                response = self.session.get(self.base_url, timeout=10)
            else:
                response = self.session.get(f"{self.base_url}/all-channels.html", timeout=10)
            
            html_content = response.text
            doc = pq(html_content)
            items = doc('.tv_kan_gl .tv_sp')
            
            items_per_page = 20
            start_idx = (int(pg) - 1) * items_per_page
            end_idx = start_idx + items_per_page
            
            for i, item in enumerate(items.items()[start_idx:end_idx]):
                title = item.attr('title')
                href = item.find('a').attr('href')
                
                if title and href:
                    # 尝试获取真实的频道图片
                    try:
                        img_element = item.find('p')
                        if img_element and img_element.attr('style'):
                            style = img_element.attr('style')
                            img_match = re.search(r'background-position:\s*0px\s*(-?\d+)px', style)
                            if img_match:
                                position = img_match.group(1)
                                img_url = f"{self.base_url}/images/channels/{position}.jpg"
                            else:
                                img_url = f"https://via.placeholder.com/300x200/FF69B4/FFFFFF?text={urllib.parse.quote(title[:15])}"
                        else:
                            img_url = f"https://via.placeholder.com/300x200/FF69B4/FFFFFF?text={urllib.parse.quote(title[:15])}"
                    except:
                        img_url = f"https://via.placeholder.com/300x200/FF69B4/FFFFFF?text={urllib.parse.quote(title[:15])}"
                    
                    videos.append({
                        'vod_id': href,
                        'vod_name': title,
                        'vod_pic': img_url,
                        'vod_remarks': '成人直播'
                    })
                    
            total_items = len(items)
                    
        except Exception as e:
            print(f"分类获取失败: {e}")
            return self._getFallbackCategoryContent(tid, pg)
            
        result['list'] = videos
        result['page'] = int(pg)
        result['pagecount'] = max(1, total_items // items_per_page + (1 if total_items % items_per_page > 0 else 0))
        result['limit'] = items_per_page
        result['total'] = total_items
        
        return result
    
    def _getFallbackCategoryContent(self, tid, pg):
        videos = []
        channels = [
            {"title": "ОХ-АХ HD", "href": "/oh-ah.html"},
            {"title": "CineMan XXX HD", "href": "/sl-hot1.html"},
            {"title": "CineMan XXX2 HD", "href": "/sl-hot2.html"},
            {"title": "Brazzers TV Europe", "href": "/brazzers-tv-europe.html"},
            {"title": "Brazzers TV", "href": "/brazzers-tv.html"},
            {"title": "Red Lips", "href": "/red-lips.html"},
            {"title": "KinoXXX", "href": "/kino-xxx.html"},
            {"title": "XY Max HD", "href": "/xy-max-hd.html"},
            {"title": "XY Plus HD", "href": "/xy-plus-hd.html"},
            {"title": "XY Mix HD", "href": "/xy-mix-hd.html"},
            {"title": "Barely legal", "href": "/barely-legal.html"},
            {"title": "Playboy TV", "href": "/playboy-tv.html"},
            {"title": "Vivid Red HD", "href": "/vivid-red.html"},
            {"title": "Exxxotica HD", "href": "/hot-pleasure.html"},
            {"title": "Babes TV", "href": "/babes-tv.html"},
            {"title": "Русская ночь", "href": "/russkaya-noch.html"},
            {"title": "Pink O TV", "href": "/pink-o.html"},
            {"title": "Erox HD", "href": "/erox-hd.html"},
            {"title": "Eroxxx HD", "href": "/eroxxx-hd.html"},
            {"title": "Hustler HD", "href": "/hustler-hd.html"},
            {"title": "Private TV", "href": "/private-tv.html"},
            {"title": "Redlight HD", "href": "/redlight-hd.html"},
            {"title": "Penthouse Gold HD", "href": "/penthouse-gold.html"},
            {"title": "Penthouse Quickies", "href": "/penthouse-2.html"},
            {"title": "O-la-la", "href": "/o-la-la.html"},
            {"title": "Blue Hustler", "href": "/blue-hustler.html"},
            {"title": "Шалун", "href": "/shalun.html"},
            {"title": "Dorcel TV", "href": "/dorcel-tv.html"},
            {"title": "Extasy HD", "href": "/extasyhd.html"},
            {"title": "XXL", "href": "/xxl.html"},
            {"title": "FAP TV 2", "href": "/fap-tv-2.html"},
            {"title": "FAP TV 3", "href": "/fap-tv-3.html"},
            {"title": "FAP TV 4", "href": "/fap-tv-4.html"},
            {"title": "FAP TV Parody", "href": "/fap-tv-parody.html"},
            {"title": "FAP TV Compilation", "href": "/fap-tv-compilation.html"},
            {"title": "FAP TV Anal", "href": "/fap-tv-anal.html"},
            {"title": "FAP TV Teens", "href": "/fap-tv-teens.html"},
            {"title": "FAP TV Lesbian", "href": "/fap-tv-lesbian.html"},
            {"title": "FAP TV BBW", "href": "/fap-tv-bbw.html"},
            {"title": "FAP TV Trans", "href": "/fap-tv-trans.html"}
        ]
        
        items_per_page = 20
        start_idx = (int(pg) - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        for channel in channels[start_idx:end_idx]:
            title = channel["title"]
            href = channel["href"]
            img_url = f"https://via.placeholder.com/300x200/FF69B4/FFFFFF?text={urllib.parse.quote(title[:15])}"
            
            videos.append({
                'vod_id': href,
                'vod_name': title,
                'vod_pic': img_url,
                'vod_remarks': '成人直播'
            })
        
        result = {}
        result['list'] = videos
        result['page'] = int(pg)
        result['pagecount'] = max(1, len(channels) // items_per_page + (1 if len(channels) % items_per_page > 0 else 0))
        result['limit'] = items_per_page
        result['total'] = len(channels)
        
        return result

    def detailContent(self, array):
        result = {}
        if not array or not array[0]:
            return result
            
        try:
            relative_path = array[0]
            detail_url = self.base_url + relative_path if relative_path.startswith('/') else self.base_url + '/' + relative_path
            
            response = self.session.get(detail_url, timeout=10)
            html_content = response.text
            
            doc = pq(html_content)
            
            # 获取标题
            title = doc('h1').text() or doc('title').text()
            if not title:
                title = relative_path.replace('.html', '').replace('/', '').replace('-', ' ').title()
            
            # 获取描述
            description_elem = doc('.op_ch p')
            description = description_elem.text() if description_elem else '成人电视直播频道，24小时不间断播放成人内容。'
            
            # 获取图片
            image = self._extractImage(doc, relative_path)
            
            # 提取播放地址（关键部分）
            play_urls = self._extractPlayUrlsFromJavaScript(html_content, detail_url)
            
            # 如果JavaScript提取失败，尝试备用方法
            if not play_urls:
                play_urls = self._extractPlayUrlsFromPage(html_content, detail_url)
            
            # 构建播放源
            play_from = []
            play_url = []
            
            for i, url in enumerate(play_urls[:3]):  # 最多3个播放源
                if url:
                    play_from.append(f"播放源{i+1}")
                    play_url.append(f"{title}${url}")
            
            # 如果没有播放地址，使用备用的
            if not play_url:
                play_from = ["备用播放源"]
                play_url = [f"{title}${self._generateBackupStreamUrl(relative_path)}"]
            
            vod = {
                'vod_id': relative_path,
                'vod_name': title,
                'vod_pic': image,
                'vod_remarks': '成人电视直播',
                'vod_content': description,
                'vod_play_from': '$$$'.join(play_from),
                'vod_play_url': '$$$'.join(play_url)
            }
            
            result['list'] = [vod]
            
        except Exception as e:
            print(f"详情页解析错误: {e}")
            return self._getFallbackDetailContent(array[0])
            
        return result
    
    def _extractImage(self, doc, relative_path):
        """提取图片"""
        try:
            # 尝试获取页面中的图片
            img_element = doc('.tv_sp img, .content img').first()
            if img_element:
                img_src = img_element.attr('src')
                if img_src:
                    if img_src.startswith('http'):
                        return img_src
                    elif img_src.startswith('/'):
                        return self.base_url + img_src
                    else:
                        return self.base_url + '/' + img_src
            
            # 尝试从CSS背景中提取
            background_elem = doc('.tv_sp p').first()
            if background_elem:
                style = background_elem.attr('style')
                if style and 'background-position' in style:
                    # 根据背景位置生成图片
                    return f"{self.base_url}/images/channel_bg.jpg"
        except:
            pass
        
        # 默认图片
        title = relative_path.replace('.html', '').replace('/', '').replace('-', ' ').title()
        return f"https://via.placeholder.com/800x450/FF69B4/FFFFFF?text={urllib.parse.quote(title[:20])}"
    
    def _extractPlayUrlsFromJavaScript(self, html_content, referer_url):
        """从JavaScript中提取播放地址（核心方法）"""
        play_urls = []
        
        try:
            # 提取关键JavaScript变量
            kodk_match = re.search(r'var\s+kodk\s*=\s*"([^"]+)"', html_content)
            kos_match = re.search(r'var\s+kos\s*=\s*"([^"]+)"', html_content)
            
            if kodk_match and kos_match:
                kodk = kodk_match.group(1)  # 例如: "1/index.m3u8?k=1764612545p02i52i251i85S"
                kos = kos_match.group(1)    # 例如: "50599d"
                
                print(f"提取到播放参数: kodk={kodk}, kos={kos}")
                
                # 方法1: 尝试直接构建播放地址
                play_url1 = f"https://s.oxax.tv/{kodk}"
                play_urls.append(play_url1)
                
                # 方法2: 另一种可能的格式
                play_url2 = f"https://r.pokaz.aMM6Gs4DQ==/{kodk}"
                play_urls.append(play_url2)
                
                # 方法3: 解码base64参数
                playerjs_match = re.search(r'new Playerjs\("([^"]+)"\)', html_content)
                if playerjs_match:
                    playerjs_param = playerjs_match.group(1)
                    decoded_urls = self._decodePlayerJsParam(playerjs_param, kodk, kos)
                    play_urls.extend(decoded_urls)
            
            # 提取其他可能的m3u8链接
            m3u8_patterns = [
                r'(https?://[^"\']+\.m3u8[^"\']*)',
                r'src=["\'][^"\']*(m3u8)[^"\']*["\']',
                r'file["\']?\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']'
            ]
            
            for pattern in m3u8_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    
                    url = match
                    if url.startswith('//'):
                        url = 'https:' + url
                    elif not url.startswith('http'):
                        if url.startswith('/'):
                            url = self.base_url + url
                        else:
                            url = referer_url.rsplit('/', 1)[0] + '/' + url
                    
                    if 'm3u8' in url and url not in play_urls:
                        play_urls.append(url)
            
        except Exception as e:
            print(f"JavaScript提取播放地址错误: {e}")
        
        # 去重
        unique_urls = []
        for url in play_urls:
            if url and url not in unique_urls:
                unique_urls.append(url)
        
        return unique_urls
    
    def _decodePlayerJsParam(self, param, kodk, kos):
        """解码PlayerJS参数"""
        urls = []
        
        try:
            # 参数可能包含base64编码
            if param.startswith('#F'):
                param = param[2:]  # 移除前缀
            
            # 尝试base64解码
            try:
                decoded = base64.b64decode(param).decode('utf-8')
                print(f"解码PlayerJS参数: {decoded}")
                
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', decoded)
                if json_match:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                    
                    if 'file' in data:
                        file_url = data['file']
                        
                        # 替换可能的变量
                        if '{v1}' in file_url and '{v2}' in file_url:
                            file_url = file_url.replace('{v1}', kodk).replace('{v2}', kos)
                        
                        urls.append(file_url)
            except:
                pass
            
        except Exception as e:
            print(f"解码PlayerJS参数错误: {e}")
        
        return urls
    
    def _extractPlayUrlsFromPage(self, html_content, referer_url):
        """从页面中提取播放地址"""
        play_urls = []
        
        try:
            # 查找iframe和embed标签
            iframe_patterns = [
                r'<iframe[^>]+src=["\']([^"\']+)["\']',
                r'<embed[^>]+src=["\']([^"\']+)["\']',
                r'src=["\'][^"\']*(player|embed|video)[^"\']*["\']'
            ]
            
            for pattern in iframe_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    
                    if match and ('m3u8' in match or 'stream' in match or 'video' in match):
                        url = match
                        if url.startswith('//'):
                            url = 'https:' + url
                        elif not url.startswith('http'):
                            if url.startswith('/'):
                                url = self.base_url + url
                            else:
                                url = referer_url.rsplit('/', 1)[0] + '/' + url
                        
                        if url not in play_urls:
                            play_urls.append(url)
            
        except Exception as e:
            print(f"页面提取播放地址错误: {e}")
        
        return play_urls
    
    def _generateBackupStreamUrl(self, relative_path):
        """生成备用播放地址"""
        channel_id = relative_path.replace('.html', '').replace('/', '')
        
        # 尝试多种可能的流媒体地址格式
        backup_urls = [
            f"https://s.oxax.tv/stream/{channel_id}.m3u8",
            f"https://r.pokaz.aMM6Gs4DQ==/stream/{channel_id}.m3u8",
            f"{self.base_url}/stream/{channel_id}.m3u8",
            f"https://stream.oxax.tv/{channel_id}/index.m3u8"
        ]
        
        return backup_urls[0]  # 返回第一个
    
    def _getFallbackDetailContent(self, relative_path):
        result = {}
        title = relative_path.replace('.html', '').replace('/', '').replace('-', ' ').title()
        
        vod = {
            'vod_id': relative_path,
            'vod_name': title,
            'vod_pic': f"https://via.placeholder.com/800x450/FF69B4/FFFFFF?text={urllib.parse.quote(title[:20])}",
            'vod_remarks': '成人电视直播',
            'vod_content': '成人电视直播频道，24小时不间断播放成人内容。',
            'vod_play_from': '播放源',
            'vod_play_url': f'{title}${self._generateBackupStreamUrl(relative_path)}'
        }
        
        result['list'] = [vod]
        return result

    def searchContent(self, key, quick, page='1'):
        result = {}
        videos = []
        
        try:
            if not key:
                return result
                
            search_url = f"{self.base_url}/search.html?q={urllib.parse.quote(key)}"
            response = self.session.get(search_url, timeout=10)
            html_content = response.text
            
            doc = pq(html_content)
            items = doc('.tv_kan_gl .tv_sp, .search-result .tv_sp')
            
            key_lower = key.lower()
            for item in items.items():
                title = item.attr('title')
                href = item.find('a').attr('href')
                
                if title and href and key_lower in title.lower():
                    # 尝试获取真实的图片
                    try:
                        img_element = item.find('p')
                        if img_element and img_element.attr('style'):
                            style = img_element.attr('style')
                            img_match = re.search(r'background-position:\s*0px\s*(-?\d+)px', style)
                            if img_match:
                                position = img_match.group(1)
                                img_url = f"{self.base_url}/images/channels/{position}.jpg"
                            else:
                                img_url = f"https://via.placeholder.com/300x200/FF69B4/FFFFFF?text={urllib.parse.quote(title[:15])}"
                        else:
                            img_url = f"https://via.placeholder.com/300x200/FF69B4/FFFFFF?text={urllib.parse.quote(title[:15])}"
                    except:
                        img_url = f"https://via.placeholder.com/300x200/FF69B4/FFFFFF?text={urllib.parse.quote(title[:15])}"
                    
                    videos.append({
                        'vod_id': href,
                        'vod_name': title,
                        'vod_pic': img_url,
                        'vod_remarks': '成人直播'
                    })
                    
            # 如果没有搜索结果，使用硬编码
            if not videos:
                channels = [
                    {"title": "ОХ-АХ HD", "href": "/oh-ah.html"},
                    {"title": "CineMan XXX HD", "href": "/sl-hot1.html"},
                    {"title": "CineMan XXX2 HD", "href": "/sl-hot2.html"},
                    {"title": "Brazzers TV Europe", "href": "/brazzers-tv-europe.html"},
                    {"title": "Brazzers TV", "href": "/brazzers-tv.html"},
                    {"title": "Red Lips", "href": "/red-lips.html"},
                    {"title": "KinoXXX", "href": "/kino-xxx.html"},
                    {"title": "XY Max HD", "href": "/xy-max-hd.html"},
                    {"title": "XY Plus HD", "href": "/xy-plus-hd.html"},
                    {"title": "XY Mix HD", "href": "/xy-mix-hd.html"}
                ]
                
                for channel in channels:
                    if key_lower in channel["title"].lower():
                        title = channel["title"]
                        href = channel["href"]
                        img_url = f"https://via.placeholder.com/300x200/FF69B4/FFFFFF?text={urllib.parse.quote(title[:15])}"
                        
                        videos.append({
                            'vod_id': href,
                            'vod_name': title,
                            'vod_pic': img_url,
                            'vod_remarks': '成人直播'
                        })
                    
        except Exception as e:
            print(f"搜索失败: {e}")
            
        result['list'] = videos
        return result

    def playerContent(self, flag, id, vipFlags):
        result = {}
        try:
            if not id:
                return result
            
            # 解析播放地址
            play_url = self._parsePlayUrl(id)
            
            # 如果播放地址是相对路径或需要进一步处理
            if not play_url.startswith(('http://', 'https://')):
                # 尝试从详情页重新提取
                if '/' in play_url and '.html' in play_url:
                    detail_result = self.detailContent([play_url])
                    if detail_result and 'list' in detail_result and detail_result['list']:
                        vod = detail_result['list'][0]
                        play_urls_str = vod.get('vod_play_url', '')
                        if play_urls_str and '$$$' in play_urls_str:
                            play_sources = play_urls_str.split('$$$')
                            for source in play_sources:
                                if '$' in source:
                                    title, url = source.split('$', 1)
                                    if url and ('m3u8' in url or 'mp4' in url):
                                        play_url = url
                                        break
            
            # 最终确定播放地址
            if not play_url.startswith(('http://', 'https://')):
                # 生成备用地址
                if play_url and '/' in play_url:
                    channel_id = play_url.split('/')[-1].replace('.html', '')
                    play_url = f"https://s.oxax.tv/stream/{channel_id}.m3u8"
                else:
                    play_url = f"https://s.oxax.tv/stream/channel.m3u8"
            
            # 设置播放器参数
            result["parse"] = 0  # 0表示直接播放，1表示需要解析
            result["playUrl"] = ''
            result["url"] = play_url
            result["header"] = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': self.base_url,
                'Origin': self.base_url
            }
            
            # 如果是m3u8流，添加必要的头部
            if 'm3u8' in play_url:
                result["header"].update({
                    'Accept': '*/*',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'cross-site'
                })
            
        except Exception as e:
            print(f"播放器内容错误: {e}")
            
        return result
    
    def _parsePlayUrl(self, id_str):
        """解析播放地址字符串"""
        try:
            if '$$$' in id_str:
                # 多个播放源
                play_sources = id_str.split('$$$')
                for source in play_sources:
                    if '$' in source:
                        title, url = source.split('$', 1)
                        if url and ('m3u8' in url or 'mp4' in url):
                            return url
                return play_sources[0].split('$')[1] if '$' in play_sources[0] else play_sources[0]
            elif '$' in id_str:
                title, url = id_str.split('$', 1)
                return url
            else:
                return id_str
        except:
            return id_str

    def isVideoFormat(self, url):
        video_extensions = ['.m3u8', '.mp4', '.flv', '.avi', '.mkv', '.ts']
        return any(ext in url.lower() for ext in video_extensions)

    def manualVideoCheck(self):
        return False

    def localProxy(self, param):
        return {}
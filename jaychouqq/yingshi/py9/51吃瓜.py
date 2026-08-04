# -*- coding: utf-8 -*-
# TVBox爬虫 - 51吃瓜网 (localProxy图片代理修复版)

import sys
import re
import json
import urllib.parse
from base.spider import Spider
from bs4 import BeautifulSoup
import requests


class Spider(Spider):
    def getName(self):
        return "51吃瓜网"

    def init(self, extend=""):
        self.host = "https://adapt.qlcdttsxm.cc"
        # 若失效，可替换为 https://51cg1.com
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.host,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        self.class_map = {
            "wpcz": "今日吃瓜", "xsxy": "学生校园", "whhl": "网红黑料",
            "rdsj": "热门大瓜", "mrdg": "吃瓜榜单", "bkdg": "必看大瓜",
            "cbdj": "AI成人短剧", "ysyl": "看片娱乐", "mrds": "每日大赛",
            "lldd": "伦理道德", "gcjq": "国产剧情", "thjx": "探花精选",
            "whhj": "网黄合集", "snsn": "骚男骚女", "whmx": "明星黑料",
            "hwcg": "海外吃瓜", "rrcg": "人人吃瓜", "ldcg": "领导干部",
            "jpll": "软萌甜妹", "qubk": "吃瓜看戏", "dcbq": "擦边聊骚",
            "zzs": "51涨知识", "cgxw": "吃瓜新闻", "yczq": "原创博主",
            "51djc": "51剧场", "sjb": "世界杯专栏",
        }
        self.debug = False

    def _log(self, msg):
        if self.debug:
            print(f"[51吃瓜] {msg}")

    def _fix_url(self, url):
        if not url:
            return ""
        url = url.strip()
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.host + url
        if not url.startswith("http"):
            return self.host + "/" + url
        return url

    def _fetch(self, url, timeout=15):
        try:
            self._log(f"Fetch: {url}")
            resp = self.session.get(url, timeout=timeout)
            resp.encoding = "utf-8"
            return resp.text
        except Exception as e:
            self._log(f"Fetch error: {e}")
            return ""

    # ---------- 首页分类 ----------
    def homeContent(self, filter=False):
        classes = [{"type_id": cid, "type_name": name} for cid, name in self.class_map.items()]
        return {"class": classes}

    def homeVideoContent(self):
        return self.categoryContent("wpcz", "1", False, {})

    # ---------- 分类列表 ----------
    def categoryContent(self, tid, pg, filter=False, extend=None):
        try:
            pg = int(pg) if pg else 1
            tid_str = str(tid)
            if tid_str not in self.class_map:
                self._log(f"未知分类: {tid_str}")
                return {"list": [], "page": pg, "pagecount": 1, "limit": 20, "total": 0}

            if pg <= 1:
                url = f"{self.host}/category/{tid_str}/"
            else:
                url = f"{self.host}/category/{tid_str}/page/{pg}/"

            html = self._fetch(url)
            if not html:
                self._log("分类页获取失败，尝试首页")
                html = self._fetch(self.host)
                if not html:
                    return {"list": [], "page": pg, "pagecount": 1, "limit": 20, "total": 0}

            videos = self._parse_articles(html)

            # 分页
            pagecount = pg
            soup = BeautifulSoup(html, "html.parser")
            pagination = soup.select(".page-navigator a")
            if pagination:
                max_page = pg
                for a in pagination:
                    href = a.get("href", "")
                    m = re.search(r"/page/(\d+)/", href)
                    if m:
                        num = int(m.group(1))
                        if num > max_page:
                            max_page = num
                if max_page > pg:
                    pagecount = max_page
            elif len(videos) >= 20:
                pagecount = pg + 1

            return {
                "list": videos,
                "page": pg,
                "pagecount": max(pagecount, pg),
                "limit": 20,
                "total": max(pagecount, pg) * 20
            }
        except Exception as e:
            self._log(f"categoryContent异常: {e}")
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    # ---------- 解析文章 ----------
    def _parse_articles(self, html):
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        videos = []
        seen = set()

        articles = soup.find_all("article")
        if not articles:
            links = soup.find_all("a", href=re.compile(r"/archives/\d+"))
            if links:
                for a in links:
                    href = a.get("href")
                    if href in seen:
                        continue
                    seen.add(href)
                    title = a.get_text(strip=True)
                    if not title:
                        h = a.find_previous(["h1", "h2", "h3"])
                        if h:
                            title = h.get_text(strip=True)
                    img = a.find("img")
                    pic = ""
                    if img:
                        pic = img.get("data-src") or img.get("data-xkrkllgl") or img.get("src") or ""
                    pic = self._fix_url(pic)
                    if href and title:
                        videos.append({
                            "vod_id": href,
                            "vod_name": title,
                            "vod_pic": pic,   # 原图，由 localProxy 处理
                            "vod_remarks": ""
                        })
                self._log(f"通过链接提取到 {len(videos)} 个")
                return videos

        for article in articles:
            try:
                a_tag = article.find("a", href=re.compile(r"/archives/\d+"))
                if not a_tag:
                    continue
                href = a_tag.get("href")
                if href in seen:
                    continue
                seen.add(href)

                title_tag = article.find(["h1", "h2", "h3"])
                title = title_tag.get_text(strip=True) if title_tag else a_tag.get_text(strip=True)
                if not title:
                    title = "未知"

                img_tag = article.find("img")
                pic = ""
                if img_tag:
                    pic = img_tag.get("data-src") or img_tag.get("data-xkrkllgl") or img_tag.get("src") or ""
                pic = self._fix_url(pic)

                videos.append({
                    "vod_id": href,
                    "vod_name": title,
                    "vod_pic": pic,   # 原图
                    "vod_remarks": ""
                })
            except Exception as e:
                self._log(f"解析 article 失败: {e}")
                continue

        self._log(f"通用解析共 {len(videos)} 个")
        return videos

    # ---------- 搜索 ----------
    def searchContent(self, key, quick=False, pg="1"):
        try:
            pg = int(pg) if pg else 1
            enc_key = urllib.parse.quote(key)
            url = f"{self.host}/search/{enc_key}/" if pg <= 1 else f"{self.host}/search/{enc_key}/page/{pg}/"
            html = self._fetch(url)
            if not html:
                url = f"{self.host}/?s={enc_key}&page={pg}"
                html = self._fetch(url)
            if not html:
                return {"list": [], "page": pg, "pagecount": 1, "limit": 20, "total": 0}
            videos = self._parse_articles(html)
            pagecount = 3 if len(videos) >= 20 else 1
            return {"list": videos, "page": pg, "pagecount": pagecount, "limit": 20, "total": pagecount * 20}
        except Exception as e:
            self._log(f"searchContent异常: {e}")
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    # ---------- 详情 ----------
    def detailContent(self, ids):
        try:
            if not ids:
                return {"list": []}
            url = ids[0]
            if not url.startswith("http"):
                url = self._fix_url(url)
            html = self._fetch(url)
            if not html:
                return {"list": []}

            soup = BeautifulSoup(html, "html.parser")
            title = ""
            title_tag = soup.find("h1")
            if title_tag:
                title = title_tag.get_text(strip=True)

            pic = ""
            img_tag = soup.find("img")
            if img_tag:
                pic = img_tag.get("data-src") or img_tag.get("data-xkrkllgl") or img_tag.get("src") or ""
            pic = self._fix_url(pic)

            content_div = soup.find("div", class_="entry-content") or soup.find("div", class_="post-content")
            content_text = ""
            if content_div:
                for tag in content_div.find_all(["script", "style", "iframe", "ins"]):
                    tag.decompose()
                content_text = content_div.get_text("\n", strip=True)[:300]

            play_urls = self._extract_video_links(soup, url)
            if play_urls:
                sources = [label for label, _ in play_urls[:5]]
                urls = [f"{label}${link}" for label, link in play_urls[:5]]
                vod_play_from = "#".join(sources)
                vod_play_url = "#".join(urls)
            else:
                vod_play_from = "查看原文"
                vod_play_url = f"原文${url}"

            return {
                "list": [{
                    "vod_id": url,
                    "vod_name": title or "未知",
                    "vod_pic": pic,
                    "vod_content": content_text,
                    "vod_play_from": vod_play_from,
                    "vod_play_url": vod_play_url
                }]
            }
        except Exception as e:
            self._log(f"detailContent异常: {e}")
            return {"list": []}

    def _extract_video_links(self, soup, base_url):
        links = []
        seen = set()
        for video in soup.find_all("video"):
            src = video.get("src")
            if src:
                full = self._fix_url(src)
                if full and full not in seen:
                    seen.add(full)
                    links.append(("Video", full))
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src")
            if src:
                full = self._fix_url(src)
                if full and full not in seen:
                    seen.add(full)
                    links.append(("iframe", full))
        content = soup.get_text()
        for pat in [r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', r'(https?://[^\s"\']+\.(?:mp4|flv|ts)[^\s"\']*)']:
            for m in re.findall(pat, content):
                if m not in seen:
                    seen.add(m)
                    links.append(("直链", m))
        return links

    # ---------- 播放 ----------
    def playerContent(self, flag, id, vipFlags=None):
        if not id:
            return {"parse": 1, "url": "", "header": {}}
        video_exts = [".m3u8", ".mp4", ".flv", ".ts", ".m4a", ".mp3"]
        if any(ext in id.lower() for ext in video_exts):
            return {"parse": 0, "url": id, "header": {"User-Agent": "Mozilla/5.0", "Referer": self.host}}
        else:
            if not id.startswith("http"):
                id = self._fix_url(id)
            return {"parse": 1, "url": id, "header": {"User-Agent": "Mozilla/5.0", "Referer": self.host}}

    # ---------- 本地代理（关键：图片防盗链） ----------
    def localProxy(self, param):
        """
        TVBox 请求图片时，通过此代理转发，添加 Referer 和 User-Agent
        param 为图片的完整 URL（由 TVBox 传入）
        """
        try:
            if not param:
                return [404, "text/plain", b"Not Found"]

            # 只处理图片请求（可根据扩展名判断）
            if not any(param.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']):
                # 非图片请求直接返回 404
                return [404, "text/plain", b"Not Found"]

            # 如果 URL 是相对路径，补全
            if param.startswith("/"):
                param = self.host + param
            elif not param.startswith("http"):
                param = self.host + "/" + param

            # 设置请求头（伪造 Referer 和 User-Agent）
            headers = {
                "Referer": self.host,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = self.session.get(param, headers=headers, timeout=10, stream=True)
            if resp.status_code == 200:
                content_type = resp.headers.get("Content-Type", "image/jpeg")
                return [200, content_type, resp.content]
            else:
                return [resp.status_code, "text/plain", b"Failed"]
        except Exception as e:
            self._log(f"localProxy错误: {e}")
            return [500, "text/plain", b"Internal Server Error"]

    # ---------- 辅助 ----------
    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        if self.session:
            self.session.close()

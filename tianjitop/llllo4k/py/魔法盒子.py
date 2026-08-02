#!/usr/bin/python
# -*- coding: utf-8 -*-
import re, json, requests, time, base64, hashlib, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from base.spider import Spider

class Spider(Spider):
    def getName(self): return "魔法盒子"
    def init(self, extend=""):
        self.host = "http://movie.l98.cn"
        self.headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Referer": self.host}
        self._sources = None; self._home_data = None
        self._play_headers = {"User-Agent": "Mozilla/5.0"}
        self.wbbb_host = "https://wbbb1.com"
        self.wbbb_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36", "Referer": self.wbbb_host, "pics": "1"}
        self._shanzha_initialized = False
        self._shanzha_userid = None
        self._shanzha_token = None
        self._shanzha_host = "http://qkys.qukanwh.com"
        self._shanzha_device_id = "2d590b9842d064a1"
        self._PUB_KEY_B64 = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCoYt0BP77U+DM08BiI/QbSRIfxijXo85BTPqIM1Ow8BNwhLETzRIZ+dEwdWDbydG/PspgBAfRpGaYVdJYtvaC2JnoO8+Ik6qMWojfEJxSFLa0Pb0A892tun4gsxoEMjcreZ+YGyaBxAfqX0BSMfdrOgIYaZQjYrw9TRLlUT31QoQIDAQAB"
        self._shanzha_source_keys = set()
    def _post(self, url, data, timeout=15):
        try: return requests.post(url, json=data, headers=self.headers, timeout=timeout).json()
        except: return {}
    def _get(self, url, timeout=15):
        try: return requests.get(url, headers=self.headers, timeout=timeout).json()
        except: return {}
    def _fix(self, u): return "https:" + u if u and u.startswith("//") else u or ""
    def _is_shanzha_key(self, key):
        return key in self._shanzha_source_keys
    def getSources(self):
        if self._sources is not None: return self._sources
        raw = self._get(self.host + "/api/tvbox/sources", timeout=8).get("data", [])
        self._sources = raw
        self._shanzha_source_keys = set()
        for s in raw:
            if s.get("name","").find("山楂") >= 0:
                self._shanzha_source_keys.add(s["key"])
        return self._sources
    def _init_shanzha(self):
        if self._shanzha_initialized: return True
        try:
            hdrs = {"User-Agent": "okhttp/4.12.0", "Connection": "Keep-Alive", "Accept-Encoding": "gzip", "Content-Type": "application/json;charset=UTF-8", "Cache-Control": "no-cache", "deviceId": self._shanzha_device_id, "client": "app", "deviceType": "Android"}
            resp = requests.get(self._shanzha_host + "/api/v1/app/user/visitorInfo", headers=hdrs, timeout=10).json()
            self._shanzha_userid = resp["data"]["id"]
            self._shanzha_token = resp["data"]["token"]
            self._shanzha_initialized = True
            return True
        except: return False
    def _shanzha_rsa_encrypt(self, data):
        try:
            from Crypto.PublicKey import RSA
            from Crypto.Cipher import PKCS1_v1_5
            key = RSA.import_key(base64.b64decode(self._PUB_KEY_B64))
            cipher = PKCS1_v1_5.new(key)
            return base64.b64encode(cipher.encrypt(data.encode("utf-8"))).decode("utf-8")
        except: return None
    def _shanzha_build_params(self, episode_id="", episode_index="", vid="", player_id="", type_id="", user_id=""):
        return f"episodeId{episode_id}episodeIndex{episode_index}id{vid}playerId{player_id}source0typeId{type_id}userId{user_id}"
    def _shanzha_gen_sign(self, timestamp, params_str):
        raw = f"SaltLSFBTimestamp{timestamp}Params{params_str}ClientappDeviceId{self._shanzha_device_id}"
        b64 = base64.b64encode(raw.encode("utf-8")).decode("utf-8")
        return hashlib.md5(b64.encode("utf-8")).hexdigest().upper()
    def _shanzha_post(self, endpoint, body, sign_params_str):
        if not self._init_shanzha(): return None
        try:
            ts = str(int(time.time()))
            enc_key = self._shanzha_rsa_encrypt(json.dumps(body, separators=(",", ":")))
            if not enc_key: return None
            snjm = self._shanzha_rsa_encrypt("113")
            appsign = self._shanzha_rsa_encrypt("09a8dc51639a31801af5f6418caebfabc695eb24")
            sign = self._shanzha_gen_sign(ts, sign_params_str)
            hdrs = {"snjm": snjm, "appsign": appsign, "timestamp": ts, "sign": sign, "deviceId": self._shanzha_device_id, "token": self._shanzha_token, "client": "app", "deviceType": "Android", "Content-Type": "application/json;charset=UTF-8", "Cache-Control": "no-cache", "User-Agent": "okhttp/4.12.0"}
            r = requests.post(self._shanzha_host + endpoint, headers=hdrs, json={"key": enc_key}, timeout=10)
            return r.json()
        except: return None
    def _decrypt_response(self, enc_data):
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5
        dec_key = RSA.import_key(base64.b64decode(self._PUB_KEY_B64))
        cipher = PKCS1_v1_5.new(dec_key)
        enc_bytes = base64.b64decode(enc_data)
        parts = []
        for i in range(0, len(enc_bytes), 256):
            parts.append(cipher.decrypt(enc_bytes[i:i+256], None))
        return json.loads(b"".join(parts).decode("utf-8"))
    def _fetch_home(self, s):
        try:
            t = 10 if s["key"] == "source-ac9aba9c5a" else 4
            d = self._post(self.host + "/api/tvbox/home", {"api": s["api"], "filter": True}, timeout=t)
            return s["key"], d.get("data", {})
        except: return s["key"], {}
    def _load_all_homes(self):
        if self._home_data is not None: return self._home_data
        sources = self.getSources()
        if not sources: return {}
        self._home_data = {}
        pool = ThreadPoolExecutor(max_workers=13)
        fs = [pool.submit(self._fetch_home, s) for s in sources if s["key"] != "source-8ee56df12f"]
        for f in as_completed(fs):
            if len(self._home_data) >= 12: break
            try:
                k, d = f.result(timeout=0.1)
            except: continue
            if d and d.get("class"): self._home_data[k] = d
        pool.shutdown(wait=False)
        self._home_data["wbbb"] = {"class": [{"type_id": "1", "type_name": "电影"}, {"type_id": "2", "type_name": "剧集"}, {"type_id": "3", "type_name": "动漫"}, {"type_id": "4", "type_name": "综艺"}]}
        return self._home_data
    def _get_source_home(self, key):
        homes = self._load_all_homes()
        if key in homes: return homes[key]
        sources = self.getSources()
        src = next((s for s in sources if s["key"] == key), None)
        if not src: return {}
        d = self._post(self.host + "/api/tvbox/home", {"api": src["api"], "filter": True}, timeout=10).get("data", {})
        if d: self._home_data[key] = d
        return d
    def homeContent(self, filter):
        result = {"class": [], "filters": {}, "list": []}
        sources = self.getSources()
        if not sources: return result
        homes = self._load_all_homes()
        all_src = sources + [{"key": "wbbb", "name": "歪比影视", "api": ""}]
        d = {s["key"]: s for s in all_src if s["key"] != "source-8ee56df12f"}
        order = ["wbbb", "source-681f32793f", "source-37dc8f3871", "tv", "source-a45d5761c9", "source-aa4f0ed30b", "4kav", "source-e18321eaa8", "hema", "source-a63c5a93bc", "source-4df616f958", "yunyun", "source-ac9aba9c5a"]
        ss = [d[k] for k in order if k in d] + [s for s in d.values() if s["key"] not in order]
        ml = []
        for s in ss:
            k = s["key"]; hd = homes.get(k, {})
            cl = hd.get("class", []); bf = hd.get("filters", {})
            result["class"].append({"type_id": k, "type_name": s["name"]})
            if k == "wbbb":
                vv = [{"n": "全部", "v": ""}] + [{"n": c.get("type_name",""), "v": str(c.get("type_id",""))} for c in cl]
                result["filters"][k] = [{"name": "分类", "key": "sub_tid", "value": vv}]
            elif cl:
                vv = [{"n": c.get("type_name", ""), "v": str(c.get("type_id", ""))} for c in cl]
                vv.insert(0, {"n": "全部", "v": ""})
                fl = [{"name": "分类", "key": "sub_tid", "value": vv}]
                for c in cl:
                    sf = bf.get(str(c.get("type_id", "")), [])
                    if sf: fl.extend(sf); break
                result["filters"][k] = fl
            for it in hd.get("list", [])[:4]:
                if isinstance(it, dict) and it.get("vod_name") and it.get("vod_id"):
                    ml.append({"vod_id": k + "|" + str(it["vod_id"]), "vod_name": it.get("vod_name",""), "vod_pic": self._fix(it.get("vod_pic","")), "vod_remarks": it.get("vod_remarks","")})
        if "wbbb" in homes:
            try:
                r = requests.get(self.wbbb_host, headers=self.wbbb_headers, timeout=5)
                for a in BeautifulSoup(r.text, "html.parser").select(".module-poster-item.module-item")[:4]:
                    t = a.get("title",""); m = re.search(r"/detail/(\d+)\.html", a.get("href",""))
                    if not m: continue
                    img = a.select_one(".lazy")
                    p = img.get("data-original","") or img.get("src","") if img else ""
                    rk = a.select_one(".module-item-note")
                    rt = rk.get_text(strip=True) if rk else ""
                    if t: ml.append({"vod_id": "wbbb|" + m.group(1), "vod_name": t, "vod_pic": urllib.parse.urljoin(self.wbbb_host, p) if p else "", "vod_remarks": rt})
            except: pass
        result["list"] = ml[:24]
        return result
    def categoryContent(self, tid, pg, filter, extend):
        if tid == "wbbb": return self._wbbb_category(pg, extend)
        result = {"list": [], "page": int(pg) if pg else 1, "pagecount": 1, "limit": 30, "total": 0}
        try:
            sources = self.getSources()
            src = next((s for s in sources if s["key"] == tid), None)
            if not src: return result
            hd = self._get_source_home(tid)
            cl = hd.get("class", [])
            sub = (extend or {}).get("sub_tid", "")
            if not sub and cl: sub = str(cl[0].get("type_id", ""))
            rex = {k:v for k,v in (extend or {}).items() if k != "sub_tid" and v}
            data = self._post(self.host + "/api/tvbox/category", {"api": src["api"], "tid": sub, "page": int(pg) or 1, "filter": bool(rex), "extend": rex}, timeout=10).get("data", {})
            items = [{"vod_id": tid + "|" + str(v["vod_id"]), "vod_name": v.get("vod_name",""), "vod_pic": self._fix(v.get("vod_pic","")), "vod_remarks": v.get("vod_remarks","")} for v in data.get("list", []) if isinstance(v, dict) and v.get("vod_id")]
            result["list"] = items
            result["pagecount"] = data.get("pagecount") or 99
            result["limit"] = data.get("limit") or len(items)
            result["total"] = data.get("total") or len(items)
        except: pass
        return result
    def _wbbb_category(self, pg, extend):
        result = {"list": [], "page": int(pg) or 1, "pagecount": 1, "limit": 30, "total": 0}
        try:
            ex = extend or {}; sub = ex.get("sub_tid", "1")
            route = [sub, ex.get("AREA",""), ex.get("CLASS",""), ex.get("LANG",""), "","","","","","","", ex.get("YEAR","")]
            url = self.wbbb_host + "/show/" + "-".join(str(x) for x in route) + ".html"
            if int(pg or 1) > 1: url = url.replace(".html", "---" + str(pg) + "---.html")
            soup = BeautifulSoup(requests.get(url, headers=self.wbbb_headers, timeout=10).text, "html.parser")
            items = []
            for a in soup.select(".module-poster-item.module-item"):
                m = re.search(r"/detail/(\d+)\.html", a.get("href",""))
                if not m: continue
                t = a.get("title","")
                img = a.select_one(".lazy")
                p = img.get("data-original","") or img.get("src","") if img else ""
                if not p: continue
                p = urllib.parse.urljoin(self.wbbb_host, p) if not p.startswith("http") else p
                rk = a.select_one(".module-item-note")
                rt = rk.get_text(strip=True) if rk else ""
                items.append({"vod_id": "wbbb|" + m.group(1), "vod_name": t, "vod_pic": p, "vod_remarks": rt})
            result["list"] = items
            pc = int(pg or 1)
            for a in soup.select("a.page-link"):
                if a.get_text(strip=True) == "尾页":
                    mm = re.search(r"---(\d+)---", a.get("href",""))
                    if mm: pc = int(mm.group(1)); break
            result["pagecount"] = pc if items else 0
            result["limit"] = len(items) or 30
            result["total"] = (pc or 1) * 30
        except: pass
        return result
    def detailContent(self, ids):
        tid = ids[0] if ids else ""
        if not tid: return {"list": []}
        if "|" in tid:
            key, real_id = tid.split("|", 1)
        else:
            key, real_id = tid, ""
        if key == "wbbb": return self._wbbb_detail(real_id)
        result = {"list": []}
        try:
            sources = self.getSources()
            src = next((s for s in sources if s["key"] == key), None)
            if not src: return result
            data = self._post(self.host + "/api/detail", {"api": src["api"], "ids": [str(real_id)]}, timeout=8).get("data", {})
            if isinstance(data, list) and data: data = data[0]
            pu = data.get("vod_play_url", "")
            # 山楂影视特殊处理：如果中转站返回的播放链接是空的或无效的，尝试用独立API获取
            if self._is_shanzha_key(key) and (not pu or "/api/tvbox/play/" in pu):
                sh_data = self._get_shanzha_detail_via_api(real_id)
                if sh_data:
                    result["list"] = sh_data
                    return result
            if pu: pu = re.sub(r"(/api/tvbox/play/[^$#\s]+)", lambda m: self.host + m.group(0) if not m.group(0).startswith("http") else m.group(0), pu)
            result["list"] = [{"vod_id": tid, "vod_name": data.get("vod_name",""), "vod_pic": self._fix(data.get("vod_pic","")), "vod_remarks": data.get("vod_remarks",""), "vod_year": data.get("vod_year",""), "vod_area": data.get("vod_area",""), "vod_actor": data.get("vod_actor",""), "vod_director": data.get("vod_director",""), "vod_content": data.get("vod_content",""), "vod_play_from": data.get("vod_play_from",""), "vod_play_url": pu}]
        except: pass
        return result
    def _get_shanzha_detail_via_api(self, vid):
        try:
            if not self._init_shanzha(): return None
            type_id = "M15"
            body = {"id": vid, "source": 0, "typeId": type_id, "userId": self._shanzha_userid, "episodeId": "", "episodeIndex": "", "playerId": ""}
            params_str = self._shanzha_build_params(episode_id="", episode_index="", vid=str(vid), player_id="", type_id=type_id, user_id=str(self._shanzha_userid))
            resp = self._shanzha_post("/api/v1/app/play/movieDetails", body, params_str)
            if not resp or not resp.get("data"): return None
            dec_json = self._decrypt_response(resp["data"])
            current_pid = dec_json["playerId"]
            play_urls = []; show = []; pu = []
            for ep in dec_json.get("episodeList", []):
                pu.append(f"{ep.get('episode','')}${vid}@{current_pid}@{ep.get('id','')}@episode")
            play_urls.append("#".join(pu))
            for mp in dec_json.get("moviePlayerList", []):
                if mp["id"] == current_pid:
                    show.append(mp.get("moviePlayerName", ""))
            for mp in dec_json.get("moviePlayerList", []):
                pid = mp["id"]; et = mp.get("episodeTotal")
                if pid == current_pid or et is None: continue
                pu2 = [f"第{k}集${k}@{pid}@{vid}@virtual" for k in range(1, et + 1)]
                play_urls.append("#".join(pu2))
                nm = mp.get("moviePlayerName", "")
                if nm and nm not in show: show.append(nm)
            desc_body = {"id": vid, "typeId": type_id}
            desc_hdrs = {"User-Agent": "okhttp/4.12.0", "Connection": "Keep-Alive", "Accept-Encoding": "gzip", "Content-Type": "application/json;charset=UTF-8", "Cache-Control": "no-cache", "deviceId": self._shanzha_device_id, "client": "app", "deviceType": "Android", "token": self._shanzha_token}
            dr = requests.post(self._shanzha_host + "/api/v1/app/play/movieDesc", headers=desc_hdrs, json=desc_body, timeout=10).json()
            dd = dr.get("data", {})
            return [{"vod_id": "shanzha_app|" + str(vid), "vod_name": dd.get("name",""), "vod_pic": dd.get("cover",""), "vod_content": dd.get("introduce",""), "vod_year": dd.get("year",""), "vod_area": dd.get("area",""), "vod_remarks": "", "vod_score": dd.get("score",""), "type_name": dd.get("classify",""), "vod_director": dd.get("director",""), "vod_actor": dd.get("star",""), "vod_play_from": "$$$".join(show), "vod_play_url": "$$$".join(play_urls)}]
        except: return None
    def _wbbb_detail(self, vid):
        try:
            soup = BeautifulSoup(requests.get(self.wbbb_host + "/detail/" + str(vid) + ".html", headers=self.wbbb_headers, timeout=10).text, "html.parser")
            h1 = soup.select_one("h1"); name = h1.get_text(strip=True) if h1 else ""
            desc = soup.select_one(".show-desc p")
            dc = desc.get_text(strip=True) if desc else ""
            img_el = soup.select_one(".module-info-poster .lazy, .module-info-poster img")
            pic = urllib.parse.urljoin(self.wbbb_host, img_el.get("data-original","") or img_el.get("src","")) if img_el else ""
            tabs = soup.select(".module-tab-items-box .tab-item")
            froms = [t.get("data-dropdown-value", t.get_text(strip=True)) for t in tabs]
            pus = []
            for pl in soup.select(".module-play-list"):
                eps = []
                for a in pl.select("a.module-play-list-link"):
                    href = a.get("href","")
                    if not href: continue
                    title = a.get("title","") or a.get_text(strip=True)
                    full_url = self.wbbb_host + href if href.startswith("/") else href
                    eps.append(title + "$" + full_url)
                if eps: pus.append("#".join(eps))
            v = {"vod_id": "wbbb|" + str(vid), "vod_name": name, "vod_pic": pic, "vod_content": dc, "vod_play_from": "$$$".join(froms) if froms else "", "vod_play_url": "$$$".join(pus) if pus else ""}
            return {"list": [v]}
        except: return {"list": []}
    def searchContent(self, key, quick, pg="1"):
        result = {"list": [], "page": int(pg) if pg else 1, "pagecount": 1}
        sources = self.getSources()
        if not sources: return result
        seen_ids = set(); all_r = []
        def fet(s):
            try:
                d = self._post(self.host + "/api/search", {"api": s["api"], "key": key, "quick": quick, "page": int(pg) if pg else 1}, timeout=3)
                if not d.get("success"): return []
                items = d.get("data", [])
                if isinstance(items, dict): items = items.get("list", [])
                if not isinstance(items, list): return []
                out = []; src_name = s.get("name", s.get("key", ""))
                for v in items:
                    if not isinstance(v, dict) or not v.get("vod_id") or not v.get("vod_name"): continue
                    vid = str(v["vod_id"])
                    if vid in seen_ids: continue
                    seen_ids.add(vid)
                    out.append({"vod_id": s["key"] + "|" + vid, "vod_name": v.get("vod_name",""), "vod_pic": self._fix(v.get("vod_pic","")), "vod_remarks": src_name})
                return out
            except: return []
        pool = ThreadPoolExecutor(max_workers=6)
        fs = [pool.submit(fet, s) for s in sources[:6] if s["key"] != "source-8ee56df12f"]
        for f in fs:
            try:
                items = f.result(timeout=5)
                if items: all_r.extend(items)
            except: continue
        pool.shutdown(wait=False)
        try:
            pg_int = int(pg) if pg else 1
            q = urllib.parse.quote(key)
            surl = self.wbbb_host + "/search/" + q + "-------------.html"
            if pg_int > 1: surl = self.wbbb_host + "/search/" + q + "----------" + str(pg_int) + "---.html"
            ws = BeautifulSoup(requests.get(surl, headers=self.wbbb_headers, timeout=3).text, "html.parser")
            for item in ws.select(".module-search-item, .module-item"):
                a = item.select_one(".module-poster-item") or (item.select("a[href]") or [None])[0]
                if not a: continue
                m = re.search(r"/detail/(\d+)\.html", a.get("href",""))
                if not m: continue
                t = a.get("title","") or a.get_text(strip=True)
                img = item.select_one(".lazy")
                p = img.get("data-original","") or img.get("src","") if img else ""
                if p and not p.startswith("http"): p = urllib.parse.urljoin(self.wbbb_host, p)
                if t and m.group(1) not in seen_ids:
                    seen_ids.add(m.group(1))
                    all_r.append({"vod_id": "wbbb|" + m.group(1), "vod_name": t, "vod_pic": p, "vod_remarks": "歪比影视"})
        except: pass
        result["list"] = all_r[:100]
        return result
    def playerContent(self, flag, id, vipFlags):
        if id and "wbbb1.com" in str(id): return self._wbbb_play(flag, id)
        # 山楂影视播放：识别 @episode 或 @virtual 后缀的播放链接
        if "@" in str(id):
            parts = id.split("@")
            if len(parts) >= 4:
                if parts[-1] == "episode":
                    eid = parts[2]; pid = parts[1]; vid = id.split("$")[0].split("|")[-1]
                    body = {"episodeId": eid, "id": int(vid), "playerId": pid, "source": 0, "typeId": "M15", "userId": self._shanzha_userid, "episodeIndex": ""}
                    ps = self._shanzha_build_params(episode_id=eid, episode_index="", vid=vid, player_id=pid, type_id="M15", user_id=str(self._shanzha_userid))
                    resp = self._shanzha_post("/api/v1/app/play/movieDetails", body, ps)
                    if resp and resp.get("data"):
                        dj = self._decrypt_response(resp["data"])
                        pu = dj.get("url", "")
                        ppid = dj.get("playerId", "")
                        ar = requests.get(self._shanzha_host + "/api/v1/app/play/analysisMovieUrl", headers={"User-Agent": "okhttp/4.12.0", "deviceId": self._shanzha_device_id, "token": self._shanzha_token, "client": "app", "deviceType": "Android"}, params={"playerUrl": pu, "playerId": ppid}, timeout=10).json()
                        final_url = ar.get("data", "")
                        if final_url:
                            return {"parse": 0, "url": final_url, "header": json.dumps({"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"}), "jx": "0"}
                elif parts[-1] == "virtual":
                    ep_idx = parts[0]; pid = parts[1]; vid = parts[2]
                    body = {"episodeIndex": str(int(ep_idx) - 1), "id": int(vid), "playerId": pid, "source": 0, "typeId": "M15", "userId": self._shanzha_userid, "episodeId": ""}
                    ps = self._shanzha_build_params(episode_id="", episode_index=str(int(ep_idx) - 1), vid=vid, player_id=pid, type_id="M15", user_id=str(self._shanzha_userid))
                    resp = self._shanzha_post("/api/v1/app/play/movieDetails", body, ps)
                    if resp and resp.get("data"):
                        dj = self._decrypt_response(resp["data"])
                        pu = dj.get("url", "")
                        ppid = dj.get("playerId", "")
                        ar = requests.get(self._shanzha_host + "/api/v1/app/play/analysisMovieUrl", headers={"User-Agent": "okhttp/4.12.0", "deviceId": self._shanzha_device_id, "token": self._shanzha_token, "client": "app", "deviceType": "Android"}, params={"playerUrl": pu, "playerId": ppid}, timeout=10).json()
                        final_url = ar.get("data", "")
                        if final_url:
                            return {"parse": 0, "url": final_url, "header": json.dumps({"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"}), "jx": "0"}
        url = id if id.startswith("http") else self.host + id if id.startswith("/") else id
        try:
            r = requests.get(url, allow_redirects=False, timeout=8, headers=self._play_headers)
            if r.status_code in (301, 302, 303, 307, 308):
                loc = r.headers.get("location", "")
                if loc:
                    loc = loc if loc.startswith("http") else self.host + loc
                    return {"parse": 0, "url": loc, "header": json.dumps(self._play_headers)}
        except: pass
        return {"parse": 0, "url": url, "header": json.dumps(self._play_headers)}
    def _wbbb_play(self, flag, id):
        try:
            res = requests.get(id, headers=self.wbbb_headers, timeout=10)
            ifs = ""; u = ""; host = "xn--qvr2v.850088.xyz"
            m = re.search(r'player_aaaa\s*=\s*(\{[^;]+\})', res.text)
            if m:
                try:
                    pd = json.loads(m.group(1)); u = pd.get("url","")
                    ifs = "https://" + host + "/player/?url=" + u
                except: pass
            if not u:
                m2 = re.search(r'<iframe[^>]+src="([^"]+)"', res.text)
                if m2:
                    ifs = m2.group(1).replace("&amp;", "&")
                    u = urllib.parse.parse_qs(urllib.parse.urlparse(ifs).query).get("url", [""])[0]
            if not u: return {"parse": 1, "url": id, "header": json.dumps(self.wbbb_headers)}
            if u.endswith(".m3u8") or u.endswith(".mp4"):
                return {"parse": 0, "url": u, "header": json.dumps({"User-Agent": self.wbbb_headers["User-Agent"], "Referer": self.wbbb_host, "pics": "1"})}
            salt = "stray"; t = str(int(time.time()))
            url_md5 = self._get_md5(u); rc4_k = (url_md5 + " P")[-22:]
            kv = self._enplay(rc4_k, self._get_md5(u + salt))
            vk = self._enplay(rc4_k, t + self._get_md5(rc4_k + salt))
            ck = self._enplay(rc4_k, self._get_md5(host + salt))
            ah = {"User-Agent": self.wbbb_headers["User-Agent"], "Referer": ifs, "Origin": "https://" + host, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest"}
            ar = requests.post("https://" + host + "/player/api.php", data={"url": u, "key": kv, "vkey": vk, "ckey": ck}, headers=ah, timeout=10)
            if ar.status_code == 200:
                e = ar.json().get("url","")
                if e:
                    real = self._decrypt_m3u8(e)
                    return {"parse": 0, "url": real, "header": json.dumps({"User-Agent": ah["User-Agent"], "Referer": "https://" + host + "/", "pics": "1"})}
            return {"parse": 1, "url": ifs, "header": json.dumps({"User-Agent": self.wbbb_headers["User-Agent"], "Referer": self.wbbb_host})}
        except Exception as e:
            return {"parse": 1, "url": id, "header": json.dumps(self.wbbb_headers)}
    def _get_md5(self, text):
        return hashlib.md5(str(text).encode("utf-8")).hexdigest()
    def _rc4(self, key, data):
        S = list(range(256)); j = 0; kb = key.encode("utf-8")
        for i in range(256): j = (j + S[i] + kb[i % len(kb)]) % 256; S[i], S[j] = S[j], S[i]
        i = 0; j = 0; r = bytearray()
        for c in data.encode("utf-8"):
            i = (i + 1) % 256; j = (j + S[i]) % 256; S[i], S[j] = S[j], S[i]
            r.append(c ^ S[(S[i] + S[j]) % 256])
        return r
    def _enplay(self, key, data): return base64.b64encode(self._rc4(key, data)).decode("utf-8")
    def _decrypt_m3u8(self, e):
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        cipher = AES.new(b"OddfJktEbGu7gCv9", AES.MODE_CBC, b"okjutU3RjGpWqB8Z")
        return unpad(cipher.decrypt(base64.b64decode(e)), AES.block_size).decode("utf-8")

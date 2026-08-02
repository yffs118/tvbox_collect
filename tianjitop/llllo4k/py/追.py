from base.spider import Spider
import re,json,requests,time,os,base64,importlib.util
from urllib.parse import quote,unquote

class Spider(Spider):
    def getName(self):
        return "追更助手"

    def init(self,extend=""):
        self.zh="/sdcard/瑾禾本地包/zgzl_zhui.json"
        self.ri="/sdcard/瑾禾本地包/zgzl_ri.json"
        self.ua="Mozilla/5.0"
        self.cfg="/sdcard/瑾禾本地包/demo.json"
        self.gyzs="/sdcard/瑾禾本地包/py/光鸭至臻社.py"
        self.guangya="https://guangyapan.fun"
        self.gywp="https://guangya.qsxy.top"
        self.gycookie="/sdcard/瑾禾本地包/gy_cookie.txt"
        self.search_api=self.guangya+"/api/other/web_search"
        self.okpkg="com.fongmi.android.tv"
        self.oksearch_activity="com.fongmi.android.tv.ui.activity.SearchActivity"

    def isVideoFormat(self,url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    def homeContent(self,filter):
        cls=[{"type_id":"zhui","type_name":"我的周更"},{"type_id":"today","type_name":"今日更新"}]
        cls += [{"type_id":"w_"+i,"type_name":"周"+i} for i in "日一二三四五六"]
        cls += [{"type_id":"ri","type_name":"我的日更"},{"type_id":"okpan","type_name":"光鸭网盘搜索"},{"type_id":"week","type_name":"周更列表"},{"type_id":"new","type_name":"最近更新"}]
        return {"class":cls}

    def homeVideoContent(self):
        return {"list":self.local("zhui",1)[:12]}

    def categoryContent(self,tid,pg,filter,extend):
        pg=int(pg)
        if tid in ["zhui","ri","today"] or tid.startswith("w_"):
            return {"list":self.local(tid,pg),"page":pg,"pagecount":1,"limit":99,"total":99}
        if tid=="okpan":
            return {"list":[],"page":pg,"pagecount":1,"limit":20,"total":0}
        if tid=="week":
            return {"list":self.week(pg),"page":pg,"pagecount":1,"limit":99,"total":99}
        return {"list":self.news(pg),"page":pg,"pagecount":1,"limit":99,"total":99}

    def detailContent(self,array):
        sid=array[0]
        if sid.startswith("local$"):
            _,gen,idx=sid.split("$",2)
            arr=self.load(gen)
            if int(idx)>=len(arr):
                return {"list":[]}
            it=arr[int(idx)]
            name=it.get("name","").split(",")[0].split("|")[0]
            pic=it.get("img","")
            week=it.get("week","")
            yurl=self.realUrl(it.get("yurl","empty"),name,gen)
            if yurl and yurl!="empty" and yurl!=it.get("yurl",""):
                it["yurl"]=yurl
                self.save(gen,arr)
            parts=it.get("name","").split(",")
            now=parts[1] if len(parts)>1 else ""
            total=parts[2] if len(parts)>2 else ""
            urls=[]
            if yurl and yurl!="empty":
                urls.append("只做搜索$push$"+quote(yurl))
            urls.append("光鸭网盘搜索$oksearch$"+quote(name))
            vod={"vod_id":sid,"vod_name":name,"vod_pic":pic,"type_name":"周更" if gen=="zhui" else "日更","vod_year":"","vod_area":"","vod_remarks":"更新至%s%s"%(now,(" / "+total) if total else ""),"vod_actor":"","vod_director":"","vod_content":"更新配置："+week+"\n链接："+yurl,"vod_play_from":"追更","vod_play_url":"#".join(urls)}
            return {"list":[vod]}

        if sid.startswith("ok$"):
            _,name,url,pic=sid.split("$",3)
            name=unquote(name)
            url=unquote(url)
            pic=unquote(pic)
            self.autoAdd(name,"zhui",url,pic)
            vod={"vod_id":sid,"vod_name":name,"vod_pic":pic,"type_name":"OK搜索结果","vod_remarks":"已保存到追更","vod_content":"已写入 /sdcard/瑾禾本地包/zgzl_zhui.json\n"+url,"vod_play_from":"已保存","vod_play_url":"播放$push$"+quote(url)}
            return {"list":[vod]}

        if sid.startswith("web$"):
            _,name,remark=sid.split("$",2)
            name=unquote(name)
            vod={"vod_id":sid,"vod_name":name,"vod_pic":"","type_name":"周历","vod_remarks":unquote(remark),"vod_content":name,"vod_play_from":"搜索","vod_play_url":"光鸭搜索$oksearch$"+quote(name)}
            return {"list":[vod]}
        return {"list":[]}

    def searchContent(self,key,quick,pg="1"):
        k=key.strip()
        res=[]
        for gen in ["zhui","ri"]:
            arr=self.load(gen)
            for i,it in enumerate(arr):
                if k in it.get("name",""):
                    res.append(self.item("local$%s$%s"%(gen,i),it,gen))
        res+=self.okSearch(k)
        return {"list":res,"page":int(pg),"pagecount":1,"limit":50,"total":len(res)}

    def playerContent(self,flag,id,vipFlags):
        if id.startswith("push$"):
            u=unquote(id[5:])
            if self.direct(u):
                return {"parse":0,"url":u,"header":"User-Agent="+self.ua}
            if "pan.baidu.com" in u or "aliyundrive.com" in u or "alipan.com" in u or "quark.cn" in u or "uc.cn" in u:
                return {"parse":1,"jx":1,"url":u,"header":"User-Agent="+self.ua}
            return {"parse":1,"url":u,"header":"User-Agent="+self.ua}
        if id.startswith("oksearch$"):
            k=unquote(id[9:])
            arr=self.okSearch(k)
            if arr:
                u=arr[0].get("vod_content","") or arr[0].get("vod_id","")
                if u.startswith("ok$"):
                    ps=u.split("$")
                    u=unquote(ps[2]) if len(ps)>2 else ""
                pic=arr[0].get("vod_pic","")
                self.autoAdd(k,"zhui",u,pic)
            intent="intent:#Intent;component=%s/%s;S.keyword=%s;end"%(self.okpkg,self.oksearch_activity,quote(k))
            return {"parse":0,"url":intent,"header":"User-Agent="+self.ua}
        return {"parse":1,"url":id,"header":"User-Agent="+self.ua}

    def localProxy(self,param):
        return [200,"video/MP2T",""]

    def okSearch(self,key):
        res=self.localPanSearch(key)
        return res if res else self.remotePanSearch(key)

    def localPanSearch(self,key):
        try:
            spec=importlib.util.spec_from_file_location("_zgzl_gyzs",self.gyzs)
            mod=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            pan=mod.Spider()
            pan.init({})
            js=pan.searchContent(key,False,"1")
            out=[]
            for it in js.get("list",[])[:30]:
                u=it.get("vod_id","")
                n=it.get("vod_name","") or key
                p=it.get("vod_pic","")
                m=it.get("vod_remarks","") or "光鸭至臻社"
                if not u:
                    continue
                out.append({"vod_id":"ok$"+quote(n)+"$"+quote(u)+"$"+quote(p),"vod_name":n,"vod_pic":p,"vod_remarks":m,"vod_content":u})
            return out
        except Exception as e:
            return []

    def guangyaPanSearch(self,key):
        try:
            html=requests.get(self.guangya+"/s/"+quote(key)+".html",headers={"User-Agent":self.ua,"Referer":self.guangya+"/"},timeout=12).text
            m=re.search(r"var\s+jsonData\s*=\s*'([\s\S]*?)';",html) or re.search(r"let\s+listItems\s*=\s*JSON\.parse\('([\s\S]*?)'\)",html)
            out=[]
            if m:
                text=m.group(1).replace('\\/','/')
                try:
                    arr=json.loads(text)
                except:
                    arr=json.loads(text.encode('utf-8').decode('unicode_escape'))
                for it in arr:
                    u=it.get("url","")
                    if not u:
                        continue
                    n=it.get("title","") or it.get("name","") or key
                    code=it.get("code","") or ""
                    if code and "pwd=" not in u and "pan.baidu.com" not in u:
                        u+=("&" if "?" in u else "?")+"pwd="+code
                    typ={0:"夸克网盘",1:"阿里云盘",2:"百度网盘",3:"UC网盘",4:"迅雷网盘",5:"光鸭磁力"}.get(int(it.get("is_type",0) or 0),"光鸭网盘")
                    out.append({"vod_id":"ok$"+quote(key)+"$"+quote(u)+"$","vod_name":n,"vod_pic":"","vod_remarks":typ+(" 提取码:"+code if code else ""),"vod_content":u})
                    if len(out)>=30:
                        break
            return out
        except Exception as e:
            return []

    def remotePanSearch(self,key):
        local=self.guangyaPanSearch(key)
        if local:
            return local
        try:
            r=requests.get(self.search_api,params={"title":key,"is_type":2},headers={"User-Agent":self.ua,"Accept":"text/event-stream","Referer":self.guangya+"/s/"+quote(key)+".html"},timeout=20)
            res=[]
            for line in r.text.splitlines():
                line=line.strip()
                if not line.startswith("data:") or "[DONE]" in line:
                    continue
                try:
                    it=json.loads(line[5:].strip())
                except:
                    continue
                u=it.get("url","")
                n=it.get("title",key) or key
                if not u:
                    continue
                res.append({"vod_id":"ok$"+quote(key)+"$"+quote(u)+"$","vod_name":n,"vod_pic":"","vod_remarks":"光鸭百度网盘","vod_content":u})
                if len(res)>=30:
                    break
            return res
        except:
            return []
    def realUrl(self,u,name="",gen="zhui"):
        if not u or u=="empty" or "guangyapan.com/s/" in u:
            return u
        if "guangya.qsxy.top" not in u:
            return u
        try:
            ck=open(self.gycookie,"r",encoding="utf-8").read().strip()
        except Exception:
            ck=""
        try:
            h={"User-Agent":self.ua,"Referer":self.gywp+"/"}
            if ck:
                h["Cookie"]=ck
            html=requests.get(u,headers=h,timeout=12).text
            if "内容已隐藏" in html and not ck:
                return u
            m=re.search(r'<a[^>]+href=["\']([^"\']*\?golink=([^"\'&]+)[^"\']*)["\'][^>]*>(https?://www\.guangyapan\.com/s/[^<]+)</a>',html,re.S) or re.search(r'(https?://www\.guangyapan\.com/s/[A-Za-z0-9_\-]+)',html)
            if m:
                return unquote(m.group(3) if len(m.groups())>=3 and m.group(3) else m.group(1)).replace('&#038;','&')
            g=re.search(r'golink=([A-Za-z0-9+/=_%\-]+)',html)
            if g:
                return base64.b64decode(unquote(g.group(1))).decode("utf-8")
        except Exception:
            return u
        return u

    def autoAdd(self,name,gen,yurl="",pic=""):
        name=(name or "").strip()
        yurl=self.realUrl(yurl,name,gen) if yurl else yurl
        if not name:
            return
        arr=self.raw(gen)
        for it in arr:
            if it.get("name","").split(",")[0].split("|")[0]==name:
                if yurl and (not it.get("yurl") or it.get("yurl")=="empty" or ("guangya.qsxy.top" in it.get("yurl","") and yurl!=it.get("yurl",""))):
                    it["yurl"]=yurl
                if pic and not it.get("img"):
                    it["img"]=pic
                self.save(gen,arr)
                return
        week=self.weekday()+",1,10,自动" if gen=="zhui" else "1,1,10"
        arr.insert(0,{"name":name+",0","week":week,"img":pic or "","yurl":yurl or "empty","riqi":self.today()})
        self.save(gen,arr)

    def raw(self,gen):
        path=self.zh if gen=="zhui" else self.ri
        try:
            return json.loads(open(path,"r",encoding="utf-8").read())
        except:
            return []

    def save(self,gen,arr):
        path=self.zh if gen=="zhui" else self.ri
        try:
            d=os.path.dirname(path)
            if d and not os.path.exists(d):
                os.makedirs(d)
            open(path,"w",encoding="utf-8").write(json.dumps(arr,ensure_ascii=False))
        except:
            pass

    def load(self,gen):
        arr=self.raw(gen)
        arr=self.update(arr,gen)
        self.save(gen,arr)
        return arr

    def item(self,vid,it,gen):
        name=it.get("name","").split(",")[0].split("|")[0]
        parts=it.get("name","").split(",")
        now=parts[1] if len(parts)>1 else ""
        total=parts[2] if len(parts)>2 else ""
        wk=it.get("week","").split(",")
        tm=wk[2] if len(wk)>2 else "10"
        plat=wk[3] if len(wk)>3 else ""
        remark=("第%s集"%now if now else "")+(("/共%s集"%total) if total else "")
        if plat:
            remark=remark+" "+plat
        return {"vod_id":vid,"vod_name":name,"vod_pic":it.get("img",""),"vod_remarks":remark,"vod_content":"%s %s点更新"%(("周"+wk[0]) if gen=="zhui" and wk else "日更",tm)}

    def local(self,tid,pg):
        if tid=="ri":
            arr=self.load("ri")
            return [self.item("local$ri$%s"%i,it,"ri") for i,it in enumerate(arr)]
        arr=self.load("zhui")
        day=self.weekday()
        want=None
        if tid=="today":
            want=day
        elif tid.startswith("w_"):
            want=tid.split("_",1)[1]
        return [self.item("local$zhui$%s"%i,it,"zhui") for i,it in enumerate(arr) if want is None or it.get("week","").split(",")[0]==want]

    def update(self,arr,gen):
        today=self.today()
        for it in arr:
            wk=it.get("week","").split(",")
            if len(wk)<2:
                continue
            last=it.get("riqi","")
            target=today if gen=="ri" else self.lastday(wk[0])
            days=self.days(last,target)
            step=7 if gen=="zhui" else 1
            times=days//step if days>0 else 0
            if times<=0:
                continue
            names=it.get("name","").split(",")
            nums=[i for i in range(1,len(names)) if re.match(r"^\d+$",names[i])]
            if nums:
                p=nums[0]
                cur=int(names[p])
                add=times*int(wk[1])
                if len(nums)>1:
                    cur=min(cur+add,int(names[nums[1]]))
                else:
                    cur=cur+add
                names[p]=str(cur)
                it["name"]=",".join(names)
            it["riqi"]=target
        return arr

    def week(self,pg):
        html=self.get("http://www.yatu.tv:2082/zhouli.asp")
        blocks=re.findall(r'<tr[\s\S]*?</tr>',html)
        res=[]
        for row in blocks:
            title=self.clean(self.m(row,r'<a[^>]*>(.*?)</a>'))
            if not title:
                continue
            txt=self.clean(row)
            remark=self.m(txt,r'(\d+集[^热日期]*)') or self.m(txt,r'(第?\d+[^ ]*)') or "周更"
            res.append({"vod_id":"web$"+quote(title)+"$"+quote(remark),"vod_name":title,"vod_pic":"","vod_remarks":remark,"vod_content":txt})
        return res[:80]

    def news(self,pg):
        html=self.get("http://www.yatu.tv:2082/zuijin.asp")
        rows=re.findall(r'<td[\s\S]*?</td>',html)
        res=[]
        for row in rows:
            title=self.clean(self.m(row,r'<a[^>]*>(.*?)</a>'))
            if not title:
                continue
            txt=self.clean(row)
            remark=self.m(txt,r'(更新[^日期]*)') or "最近更新"
            res.append({"vod_id":"web$"+quote(title)+"$"+quote(remark),"vod_name":title,"vod_pic":"","vod_remarks":remark,"vod_content":txt})
        return res[:80]

    def get(self,url):
        try:
            r=requests.get(url,headers={"User-Agent":self.ua},timeout=8)
            r.encoding="gbk"
            return r.text
        except:
            return ""

    def clean(self,s):
        return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",s or "")).strip()

    def m(self,s,p):
        r=re.search(p,s or "",re.S)
        return r.group(1).strip() if r else ""

    def today(self):
        return time.strftime("%Y-%m-%d",time.localtime())

    def weekday(self):
        return "日一二三四五六"[int(time.strftime("%w",time.localtime()))]

    def lastday(self,w):
        mp={"日":0,"一":1,"二":2,"三":3,"四":4,"五":5,"六":6}
        now=time.time()
        cur=int(time.strftime("%w",time.localtime(now)))
        diff=(cur-mp.get(w,cur)+7)%7
        return time.strftime("%Y-%m-%d",time.localtime(now-diff*86400))

    def days(self,a,b):
        try:
            return int((time.mktime(time.strptime(b,"%Y-%m-%d"))-time.mktime(time.strptime(a,"%Y-%m-%d")))/86400)
        except:
            return 0

    def direct(self,u):
        return bool(re.search(r'\.(m3u8|mp4|flv|mkv|mp3)(\?|$)',u,re.I))
var HOST = "https://gimyplus.com";
var PROXY = "https://gimyplus-com.translate.goog";
var TRANS = "_x_tr_sl=auto&_x_tr_tl=zh-CN&_x_tr_hl=zh-CN";
var UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
var CLASSES = [{ type_id: "2", type_name: "电视剧" }, { type_id: "1", type_name: "电影" }, { type_id: "4", type_name: "动漫" }, { type_id: "29", type_name: "综艺" }, { type_id: "34", type_name: "短剧" }];
var SUBTYPES = {
    "1": [["全部", "1"], ["剧情片", "11"], ["动作片", "6"], ["科幻片", "9"], ["喜剧片", "7"], ["恐怖片", "10"], ["爱情片", "8"], ["战争片", "12"], ["动画电影", "24"]],
    "2": [["全部", "2"], ["陆剧", "13"], ["韩剧", "20"], ["美剧", "16"], ["日剧", "15"], ["台剧", "14"], ["港剧", "21"], ["短剧", "34"], ["AI漫剧", "38"], ["海外剧", "31"], ["纪录片", "22"]],
    "4": [["全部", "4"]], "29": [["全部", "29"]], "34": [["全部", "34"]]
};
var AREAS = [["中国大陆", "中國大陸"], ["大陆", "大陸"], ["韩国", "韓國"], ["日本", "日本"], ["台湾", "台灣"], ["香港", "香港"], ["美国", "美國"], ["欧美", "歐美"], ["泰国", "泰國"], ["英国", "英國"], ["法国", "法國"], ["新加坡", "新加坡"], ["越南", "越南"], ["其他", "其他"]];
var FILTERS = {};

function str(v) { return v === undefined || v === null ? "" : String(v); }
function clean(s) { return str(s).replace(/<script[\s\S]*?<\/script>/gi, "").replace(/<style[\s\S]*?<\/style>/gi, "").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/\s+/g, " ").trim(); }
function norm(s) {
    var from = "殺風體國劇電視網綜門間骨頭還樹劉陸韓美臺灣港漫紀錄動畫愛情科幻戰爭恐怖綜藝更新總雲線路畫質無盡極速優順暢清晰如意盡聲說龍鳳凰實學會時後前開關點長短萬與為這個們來對當裏難歡樂發現有沒幾次於從將被";
    var to =   "杀风体国剧电视网络门间骨头还树刘陆韩美台湾港漫纪录动画爱情科幻战争恐怖综艺更新总云线路画质无尽极速优顺畅清晰如意尽声说龙凤凤实学会时后前开关点长短万与为这个们来对当里难欢乐发现有没几次于从将被";
    var map = {}, out = "", value = str(s).toLowerCase();
    for (var i = 0; i < from.length; i++) map[from.charAt(i)] = to.charAt(i);
    for (var j = 0; j < value.length; j++) out += map[value.charAt(j)] || value.charAt(j);
    return out.replace(/\s+/g, "");
}
function attr(s, n) { var m = new RegExp(n + "\\s*=\\s*([\"'])([\\s\\S]*?)\\1", "i").exec(s || ""); return m ? m[2] : ""; }
function result(v) { return JSON.stringify(v); }
function proxyUrl(path, params) { path = str(path).replace(/^https?:\/\/[^/]+/, "").split("?")[0]; return PROXY + path + "?" + (params ? params + "&" : "") + TRANS; }
function requestText(path, params) {
    for (var i = 0; i < 2; i++) {
        try {
            var r = req(proxyUrl(path, params), { method: "GET", headers: { "User-Agent": UA, "Referer": HOST + "/" }, timeout: 20000 });
            var text = str(typeof r === "string" ? r : r && (r.content || r.body || r.data));
            if (text && !/Just a moment|Attention Required/i.test(text)) return text;
        } catch (e) { }
    }
    return "";
}
function getJson(url, referer) {
    try {
        var r = req(url, { method: "GET", headers: { "User-Agent": UA, "Referer": referer || url.replace(/[^/]+$/, "") }, timeout: 25000 });
        return JSON.parse(str(typeof r === "string" ? r : r && (r.content || r.body || r.data)) || "{}");
    } catch (e) { return {}; }
}
function idPath(href, type) { var m = new RegExp("/" + type + "/(\\d+)(?:\\.html|-)").exec(href || ""); return m ? m[1] : ""; }
function parseList(html) {
    var out = [], seen = {}, re = /<a\b(?=[^>]*class=["'][^"']*card__thumb)(?=[^>]*href=["']([^"']*\/vod\/(\d+)\.html[^"']*))[^>]*>[\s\S]*?<\/a>/gi, m;
    while ((m = re.exec(html || "")) !== null) {
        if (seen[m[2]]) continue;
        seen[m[2]] = 1;
        var block = m[0], img = (/<img\b[^>]*>/i.exec(block) || [""])[0];
        var name = attr(img, "alt"), pic = attr(img, "data-src") || attr(img, "src"), remark = clean(block);
        if (name) out.push({ vod_id: m[2], vod_name: name, vod_pic: pic, vod_remarks: remark });
    }
    return out;
}
function buildFilters() {
    var years = [{ n: "全部", v: "" }];
    for (var y = 2026; y >= 2016; y--) years.push({ n: str(y), v: str(y) });
    for (var k in SUBTYPES) FILTERS[k] = [
        { key: "type", name: "类型", value: SUBTYPES[k].map(function (x) { return { n: x[0], v: x[1] }; }) },
        { key: "area", name: "地区", value: [{ n: "全部", v: "" }].concat(AREAS.map(function (x) { return { n: x[0], v: x[1] }; })) },
        { key: "year", name: "年份", value: years },
        { key: "by", name: "排序", value: [{ n: "最新更新", v: "time" }, { n: "最新上架", v: "time_add" }, { n: "周人气", v: "hits_week" }, { n: "总人气", v: "hits" }] }
    ];
}
function parseExt(ext) { if (!ext) return {}; if (typeof ext === "object") return ext; try { return JSON.parse(ext); } catch (e) { return {}; } }

function init(ext) { buildFilters(); }
function home(filter) { return result({ class: CLASSES, filters: FILTERS }); }
function homeVod() { return result({ list: parseList(requestText("/")) }); }
function category(tid, pg, filter, extend) {
    pg = parseInt(pg || 1) || 1;
    var e = parseExt(extend), type = str(e.type || tid), area = str(e.area || ""), year = str(e.year || ""), by = str(e.by || "time");
    var filtered = !!(area || year || e.by), path = filtered ? "/show/" + type + "-" + encodeURIComponent(area) + "-" + by + "------" + pg + "---" + year + ".html" : "/type/" + type + (pg > 1 ? "-" + pg : "") + ".html";
    var list = parseList(requestText(path));
    return result({ page: pg, pagecount: list.length ? pg + 1 : pg, limit: list.length || 36, total: (pg + 1) * (list.length || 36), list: list });
}
function detail(id) {
    var vid = (str(id).match(/\d+/) || [""])[0], html = requestText("/vod/" + vid + ".html");
    if (!html) return result({ list: [] });
    var name = clean((/<h1[^>]*>([\s\S]*?)<\/h1>/i.exec(html) || ["", ""])[1]);
    if (!name) name = str((/property=["']og:title["'][^>]*content=["']([^"']+)/i.exec(html) || ["", ""])[1]).split("線上看")[0];
    var pic = (/(?:property=["']og:image["'][^>]*content|content=["']([^"']+)["'][^>]*property=["']og:image)/i.exec(html) || ["", ""])[1] || "";
    var desc = clean((/property=["']og:description["'][^>]*content=["']([^"']+)/i.exec(html) || ["", ""])[1]);
    var starts = [], sr = /<div\b[^>]*class=["'][^"']*playlist-block[^"']*["'][^>]*>/gi, sm;
    while ((sm = sr.exec(html)) !== null) starts.push(sm.index);
    var froms = [], urls = [];
    for (var i = 0; i < starts.length; i++) {
        var block = html.slice(starts[i], i + 1 < starts.length ? starts[i + 1] : html.length);
        var title = clean((/playlist-block__title[^>]*>([\s\S]*?)<\//i.exec(block) || ["", ""])[1]) || "线路" + (i + 1);
        var eps = [], er = /<a\b[^>]*href=["']([^"']*\/ep\/(\d+)-(\d+)-(\d+)\.html[^"']*)["'][^>]*>([\s\S]*?)<\/a>/gi, em;
        while ((em = er.exec(block)) !== null) eps.push((clean(em[5]) || "播放") + "$/ep/" + em[2] + "-" + em[3] + "-" + em[4] + ".html");
        if (eps.length) { froms.push(title); urls.push(eps.join("#")); }
    }
    return result({ list: [{ vod_id: vid, vod_name: name, vod_pic: pic, vod_content: desc, vod_play_from: froms.join("$$$"), vod_play_url: urls.join("$$$") }] });
}
function parsePlayer(html) {
    var m = /var\s+player_data\s*=\s*(\{[\s\S]*?\})\s*<\/script>/i.exec(html || "");
    if (!m) return {};
    try { return JSON.parse(m[1]); } catch (e) { return {}; }
}
function resolveSpecial(url) {
    var api = /^JD(?:-|QM-|HG-)/.test(url) ? "https://v.gimy.bot/jd/api.php" : /^(NSYS-|NS4K-)/.test(url) ? "https://player.gimy.bot/n/api.php" : "https://v.gimy.bot/jx/api.php";
    var data = getJson(api + "?url=" + encodeURIComponent(url), api.replace(/api\.php.*$/, ""));
    return data && Number(data.code) === 200 ? str(data.url) : "";
}
function play(flag, id, flags) {
    var path = str(id).replace(/^https?:\/\/[^/]+/, ""), data = parsePlayer(requestText(path)), url = str(data.url).replace(/\\\//g, "/");
    if (data.encrypt == 1) try { url = unescape(url); } catch (e1) { }
    if (data.encrypt == 2) try { url = decodeURIComponent(url); } catch (e2) { }
    if (url && !/\.(m3u8|mp4|flv)(\?|$)/i.test(url)) url = resolveSpecial(url);
    if (/^https?:\/\//.test(url) && /\.(m3u8|mp4|flv)(\?|$)/i.test(url)) return result({ parse: 0, url: url, header: { "User-Agent": UA }, headers: { "User-Agent": UA } });
    return result({ parse: 1, jx: 0, url: HOST + path, header: { "User-Agent": UA, "Referer": HOST + "/" } });
}
function search(wd, quick, pg) {
    pg = parseInt(pg || 1) || 1;
    var keyword = norm(wd);
    var list = parseList(requestText("/")).filter(function (x) { return norm(x.vod_name).indexOf(keyword) >= 0; });
    if (!list.length) {
        try {
            var rssUrl = "https://www.bing.com/search?format=rss&q=" + encodeURIComponent("site:gimyplus.com/vod/ " + wd);
            var r = req(rssUrl, { method: "GET", headers: { "User-Agent": UA }, timeout: 15000 });
            var xml = str(typeof r === "string" ? r : r && (r.content || r.body || r.data));
            var seen = {}, ir = /<item>([\s\S]*?)<\/item>/gi, im;
            while ((im = ir.exec(xml)) !== null) {
                var block = im[1], link = clean((/<link>([\s\S]*?)<\/link>/i.exec(block) || ["", ""])[1]);
                var idm = /gimyplus\.com\/vod\/(\d+)\.html/i.exec(link);
                if (!idm || seen[idm[1]]) continue;
                seen[idm[1]] = 1;
                var title = clean((/<title>([\s\S]*?)<\/title>/i.exec(block) || ["", ""])[1]).replace(/\s*-\s*Gimy.*$/i, "").replace(/線上看|线上看/g, "").trim();
                list.push({ vod_id: idm[1], vod_name: title || wd, vod_pic: "", vod_remarks: "搜索索引" });
            }
        } catch (e) { }
    }
    return result({ page: pg, pagecount: pg, limit: list.length || 20, total: list.length, list: list });
}

__JS_SPIDER__ = { init: init, home: home, homeVod: homeVod, category: category, detail: detail, play: play, search: search };

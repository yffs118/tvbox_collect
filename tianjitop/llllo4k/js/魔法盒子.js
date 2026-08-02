import cheerio from 'assets://js/lib/cheerio.min.js';

const appConfig = {
    siteName: "魔法盒子",
    siteUrl: "http://movie.l98.cn"
}

const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36";
const Headers = {
    "User-Agent": UA,
    "Referer": appConfig.siteUrl + "/",
}

const disabledSources = ["source-a45d5761c9", "source-ac9aba9c5a"];

const sourceSubCategories = {
    "hema": [
        { type_id: "462", type_name: "甜宠" },
        { type_id: "1102", type_name: "古装仙侠" },
        { type_id: "1145", type_name: "现代言情" },
        { type_id: "1170", type_name: "青春" },
        { type_id: "585", type_name: "豪门恩怨" },
        { type_id: "417-464", type_name: "逆袭" },
        { type_id: "439-465", type_name: "重生" },
        { type_id: "1159", type_name: "系统" },
        { type_id: "1147", type_name: "总裁" },
        { type_id: "943", type_name: "职场商战" }
    ],
    "source-8ee56df12f": [
        { type_id: "1", type_name: "电影" },
        { type_id: "2", type_name: "剧集" },
        { type_id: "3", type_name: "动漫" },
        { type_id: "4", type_name: "综艺" }
    ],
    "source-681f32793f": [
        { type_id: "1", type_name: "电影" },
        { type_id: "2", type_name: "电视剧" },
        { type_id: "3", type_name: "综艺" },
        { type_id: "4", type_name: "动漫" }
    ],
    "source-aa4f0ed30b": [
        { type_id: "1", type_name: "电影" },
        { type_id: "2", type_name: "电视剧" },
        { type_id: "3", type_name: "动漫" },
        { type_id: "4", type_name: "综艺" }
    ],
    "tv": [
        { type_id: "1", type_name: "电影" },
        { type_id: "2", type_name: "电视剧" },
        { type_id: "3", type_name: "综艺" },
        { type_id: "4", type_name: "动漫" }
    ],
    "source-37dc8f3871": [
        { type_id: "1", type_name: "连续剧" },
        { type_id: "2", type_name: "综艺" },
        { type_id: "3", type_name: "电影" },
        { type_id: "4", type_name: "动漫" }
    ],
    "yunyun": [
        { type_id: "1", type_name: "推荐歌单" },
        { type_id: "2", type_name: "排行榜" },
        { type_id: "3", type_name: "热门歌单" },
        { type_id: "4", type_name: "热门歌手" }
    ]
};

let sources = [];
let allClasses = [];

async function init(ext) {
    console.log("初始化爬虫:", appConfig.siteName);
}

function getYearFilter() {
    let years = [{ "n": "全部", "v": "" }];
    const currentYear = new Date().getFullYear().toString();
    for (let y = currentYear; y >= currentYear - 22; y--) {
        years.push({ "n": String(y), "v": String(y) });
    }
    return { "key": "year", "name": "年份", "value": years };
}

function getLetterFilter() {
    return {
        "key": "letter", "name": "字母", "value": [
            { "n": "全部", "v": "" },
            { "n": "A", "v": "A" }, { "n": "B", "v": "B" }, { "n": "C", "v": "C" }, { "n": "D", "v": "D" },
            { "n": "E", "v": "E" }, { "n": "F", "v": "F" }, { "n": "G", "v": "G" }, { "n": "H", "v": "H" },
            { "n": "I", "v": "I" }, { "n": "J", "v": "J" }, { "n": "K", "v": "K" }, { "n": "L", "v": "L" },
            { "n": "M", "v": "M" }, { "n": "N", "v": "N" }, { "n": "O", "v": "O" }, { "n": "P", "v": "P" },
            { "n": "Q", "v": "Q" }, { "n": "R", "v": "R" }, { "n": "S", "v": "S" }, { "n": "T", "v": "T" },
            { "n": "U", "v": "U" }, { "n": "V", "v": "V" }, { "n": "W", "v": "W" }, { "n": "X", "v": "X" },
            { "n": "Y", "v": "Y" }, { "n": "Z", "v": "Z" }, { "n": "0-9", "v": "0-9" }
        ]
    }
}

function getOrderFilter() {
    return {
        "key": "orderBy", "name": "排序", "value": [
            { "n": "时间", "v": "time" },
            { "n": "人气", "v": "hits" },
            { "n": "评分", "v": "score" }
        ]
    }
}

function getStatusFilter() {
    return {
        "key": "status", "name": "状态", "value": [
            { "n": "全部", "v": "" },
            { "n": "完结", "v": "completed" },
            { "n": "更新中", "v": "updating" }
        ]
    }
}

function getAreaFilter() {
    return {
        "key": "area", "name": "地区", "value": [
            { "n": "全部", "v": "" }, { "n": "大陆", "v": "大陆" }, { "n": "香港", "v": "香港" },
            { "n": "台湾", "v": "台湾" }, { "n": "美国", "v": "美国" }, { "n": "韩国", "v": "韩国" },
            { "n": "日本", "v": "日本" }, { "n": "泰国", "v": "泰国" }, { "n": "新加坡", "v": "新加坡" },
            { "n": "马来西亚", "v": "马来西亚" }, { "n": "印度", "v": "印度" }, { "n": "英国", "v": "英国" },
            { "n": "法国", "v": "法国" }, { "n": "加拿大", "v": "加拿大" }, { "n": "西班牙", "v": "西班牙" },
            { "n": "俄罗斯", "v": "俄罗斯" }, { "n": "其它", "v": "其它" }
        ]
    }
}

function getLangFilter() {
    return {
        "key": "lang", "name": "语言", "value": [
            { "n": "全部", "v": "" }, { "n": "国语", "v": "国语" }, { "n": "英语", "v": "英语" },
            { "n": "粤语", "v": "粤语" }, { "n": "闽南语", "v": "闽南语" }, { "n": "韩语", "v": "韩语" },
            { "n": "日语", "v": "日语" }, { "n": "其它", "v": "其它" }
        ]
    }
}

const CommonFilters = [
    getStatusFilter(),
    getAreaFilter(),
    getLangFilter(),
    getYearFilter(),
    getLetterFilter(),
    getOrderFilter()
];

function buildFiltersMap() {
    const filters = {};
    for (const [sourceKey, subs] of Object.entries(sourceSubCategories)) {
        for (const sub of subs) {
            const typeId = `${sourceKey}###${sub.type_id}`;
            filters[typeId] = CommonFilters;
        }
    }
    return filters;
}

async function loadSources() {
    if (sources.length > 0 && allClasses.length > 0) return;
    try {
        const response = await req(`${appConfig.siteUrl}/api/tvbox/sources`, {
            method: 'GET',
            headers: Headers
        });
        const data = JSON.parse(response.content || response.body || '{}');
        if (data.success) {
            sources = data.data.filter(s => !disabledSources.includes(s.key));

            allClasses = [];
            for (const source of sources) {
                const subs = sourceSubCategories[source.key] || [];
                for (const sub of subs) {
                    allClasses.push({
                        type_id: `${source.key}###${sub.type_id}`,
                        type_name: `${source.name} - ${sub.type_name}`
                    });
                }
            }
        }
    } catch (e) {
        console.error("加载数据源失败:", e.message);
    }
}

async function home(filter) {
    await loadSources();

    const filters = buildFiltersMap();

    return JSON.stringify({
        class: allClasses,
        filters: filters
    });
}

function isCompleted(remarks) {
    if (!remarks) return false;
    const r = remarks.toLowerCase();
    return r.includes('完本') || r.includes('完结') || r.includes('全') || r.includes('已完结');
}

function isUpdating(remarks) {
    if (!remarks) return false;
    const r = remarks.toLowerCase();
    return r.includes('更新') || r.includes('连载');
}

function parseTypeId(tid) {
    const parts = tid.split('###');
    return {
        sourceKey: parts[0] || '',
        subId: parts[1] || ''
    };
}

async function category(tid, pg, filter, extend) {
    await loadSources();

    pg = pg || 1;
    const { sourceKey, subId } = parseTypeId(tid);

    const source = sources.find(s => s.key === sourceKey);
    if (!source) {
        return JSON.stringify({ page: 1, pagecount: 0, limit: 20, total: 0, list: [] });
    }

    try {
        let data;
        let pagecount = 1;
        let total = 0;
        let limit = 20;

        if (subId) {
            const requestData = JSON.stringify({ api: source.api, tid: subId, pg: String(pg) });
            const response = await req(`${appConfig.siteUrl}/api/tvbox/category`, {
                method: 'POST',
                headers: { ...Headers, 'Content-Type': 'application/json' },
                body: requestData
            });
            data = JSON.parse(response.content || response.body || '{}');
            if (data && data.data) {
                pagecount = parseInt(data.data.pagecount) || 1;
                total = parseInt(data.data.total) || 0;
                limit = parseInt(data.data.limit) || 20;
            }
        } else {
            const requestData = JSON.stringify({ api: source.api });
            const response = await req(`${appConfig.siteUrl}/api/tvbox/home`, {
                method: 'POST',
                headers: { ...Headers, 'Content-Type': 'application/json' },
                body: requestData
            });
            data = JSON.parse(response.content || response.body || '{}');
        }

        if (!data.success) {
            return JSON.stringify({ page: pg, pagecount: 1, limit: 20, total: 0, list: [] });
        }

        let list = [];
        if (data.data && data.data.list && Array.isArray(data.data.list)) {
            list = data.data.list;
        }

        if (extend && extend.keyword) {
            const kw = extend.keyword.toLowerCase();
            list = list.filter(item =>
                item.vod_name && item.vod_name.toLowerCase().includes(kw)
            );
        }

        if (extend && extend.status) {
            const st = extend.status.toLowerCase();
            if (st === 'completed') {
                list = list.filter(item => isCompleted(item.vod_remarks));
            } else if (st === 'updating') {
                list = list.filter(item => isUpdating(item.vod_remarks));
            }
        }

        if (extend && extend.area) {
            const area = extend.area;
            list = list.filter(item =>
                (item.vod_area && item.vod_area.includes(area)) ||
                (item.area && item.area.includes(area))
            );
        }

        if (extend && extend.year) {
            const year = extend.year;
            list = list.filter(item =>
                (item.vod_year && String(item.vod_year).includes(year)) ||
                (item.year && String(item.year).includes(year))
            );
        }

        if (extend && extend.lang) {
            const lang = extend.lang;
            list = list.filter(item =>
                (item.vod_lang && item.vod_lang.includes(lang)) ||
                (item.lang && item.lang.includes(lang))
            );
        }

        if (extend && extend.letter) {
            const letter = extend.letter;
            list = list.filter(item => {
                const name = item.vod_name || item.name || '';
                if (!name) return false;
                const firstChar = name.charAt(0).toUpperCase();
                if (letter === '0-9') {
                    return /[0-9]/.test(firstChar);
                }
                return firstChar === letter;
            });
        }

        const resultList = list.map(item => {
            const vod_id = item.vod_id || item.id || '';
            const vod_name = item.vod_name || item.name || '';
            const vod_pic = item.vod_pic || item.pic || '';
            const vod_remarks = item.vod_remarks || item.remarks || '';

            return {
                vod_id: `${source.key}@@@${vod_id}`,
                vod_name,
                vod_pic: vod_pic.startsWith('http') ? vod_pic : appConfig.siteUrl + vod_pic,
                vod_remarks
            };
        });

        const returnPagecount = pagecount > 0 ? pagecount : (resultList.length > 0 ? 1 : 0);

        return JSON.stringify({
            page: parseInt(pg),
            pagecount: returnPagecount,
            limit: limit || resultList.length,
            total: total || resultList.length,
            list: resultList
        });

    } catch (e) {
        console.error("分类列表获取失败:", e.message);
        return JSON.stringify({ page: pg, pagecount: 0, limit: 20, total: 0, list: [] });
    }
}

async function search(wd, quick, page) {
    await loadSources();

    page = page || 1;
    if (!wd || page >= 2) {
        return JSON.stringify({ page: page, pagecount: 1, limit: 20, total: 0, list: [] });
    }

    try {
        let allResults = [];

        for (const source of sources) {
            try {
                const requestData = JSON.stringify({ api: source.api });
                const response = await req(`${appConfig.siteUrl}/api/tvbox/home`, {
                    method: 'POST',
                    headers: { ...Headers, 'Content-Type': 'application/json' },
                    body: requestData
                });

                const data = JSON.parse(response.content || response.body || '{}');
                if (data.success && data.data && data.data.list && Array.isArray(data.data.list)) {
                    const filtered = data.data.list.filter(item =>
                        item.vod_name && item.vod_name.toLowerCase().includes(wd.toLowerCase())
                    ).map(item => {
                        const vod_id = item.vod_id || item.id || '';
                        const vod_name = item.vod_name || item.name || '';
                        const vod_pic = item.vod_pic || item.pic || '';
                        const vod_remarks = item.vod_remarks || item.remarks || '';

                        return {
                            vod_id: `${source.key}@@@${vod_id}`,
                            vod_name,
                            vod_pic: vod_pic.startsWith('http') ? vod_pic : appConfig.siteUrl + vod_pic,
                            vod_remarks
                        };
                    });
                    allResults = allResults.concat(filtered);
                }
            } catch (e) {
                continue;
            }

            await new Promise(r => setTimeout(r, 300));
        }

        return JSON.stringify({
            page: page,
            pagecount: 1,
            limit: allResults.length,
            total: allResults.length,
            list: allResults.slice(0, 50)
        });

    } catch (e) {
        console.error("搜索失败:", e.message);
        return JSON.stringify({ page: page, pagecount: 1, limit: 20, total: 0, list: [] });
    }
}

async function detail(id) {
    try {
        const parts = id.split('@@@');
        const sourceKey = parts[0] || '';
        const parsedId = parts[1] || id;

        const source = sources.find(s => s.key === sourceKey);
        if (!source) {
            return JSON.stringify({ list: [] });
        }

        const requestData = JSON.stringify({ api: source.api, ids: parsedId });
        const response = await req(`${appConfig.siteUrl}/api/detail`, {
            method: 'POST',
            headers: { ...Headers, 'Content-Type': 'application/json' },
            body: requestData
        });

        const data = JSON.parse(response.content || response.body || '{}');
        if (!data.success || !data.data) {
            return JSON.stringify({ list: [] });
        }

        const item = data.data;

        let vod_play_from = item.vod_play_from || '';
        let vod_play_url = item.vod_play_url || '';

        if (vod_play_url) {
            vod_play_url = vod_play_url.replace(/\/api\/tvbox\/play\//g, appConfig.siteUrl + '/api/tvbox/play/');
        }

        const vod_pic = item.vod_pic || '';
        const vod_content = (item.vod_content || '').replace(/<[^>]+>/g, '').trim();

        const vod = {
            vod_id: id,
            vod_name: item.vod_name || '',
            vod_pic: vod_pic.startsWith('http') ? vod_pic : (vod_pic ? appConfig.siteUrl + vod_pic : ''),
            type_name: item.type_name || '',
            vod_year: item.vod_year || '',
            vod_area: item.vod_area || '',
            vod_director: item.vod_director || '',
            vod_actor: item.vod_actor || '',
            vod_lang: item.vod_lang || '',
            vod_remarks: item.vod_remarks || '',
            vod_content: vod_content,
            vod_play_from: vod_play_from,
            vod_play_url: vod_play_url
        };

        return JSON.stringify({ list: [vod] });
    } catch (error) {
        console.error(`获取详情失败 [ID: ${id}]:`, error);
        return JSON.stringify({ list: [] });
    }
}

async function play(flag, id, flags) {
    try {
        let playUrl = id;

        if (playUrl.startsWith('/api/tvbox/play/')) {
            playUrl = appConfig.siteUrl + playUrl;
        }

        return JSON.stringify({
            parse: 0,
            Header: {
                "User-Agent": UA,
                "Referer": appConfig.siteUrl + "/"
            },
            url: playUrl
        });
    } catch (e) {
        console.error("播放失败:", e);
        return JSON.stringify({ parse: 0, url: "" });
    }
}

export default {
    init,
    home,
    category,
    detail,
    search,
    play
};

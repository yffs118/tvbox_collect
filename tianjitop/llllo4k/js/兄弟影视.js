import { Crypto, load, _ } from 'assets://js/lib/cat.js';

let siteUrl = 'https://www.brovod.com';
let siteKey = '';
let siteType = 0;
let headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    'Referer': 'https://www.brovod.com/'
};

async function request(reqUrl, postData, get) {
    let res = await req(reqUrl, {
        method: get ? 'get' : 'post',
        headers: headers,
        data: postData || {},
        postType: get ? '' : 'form',
    });
    return res.content;
}

async function init(cfg) {
    siteKey = cfg.skey;
    siteType = cfg.stype;
}

async function home(filter) {
    let classes = [
        { type_id: 'Movies', type_name: '电影' },
        { type_id: 'TV', type_name: '剧集' },
        { type_id: 'Shows', type_name: '综艺' },
        { type_id: 'Anime', type_name: '动漫' },
        { type_id: 'Snaps', type_name: '短剧' },
        { type_id: 'Documentaries', type_name: '纪录片' }
    ];

    let filterObj = genFilterObj();
    return JSON.stringify({
        class: classes,
        filters: filterObj
    });
}

function getVideos($) {
    let videos = [];
    $('div.public-list-box').each((i, n) => {
        let a = $(n).find('a.public-list-exp');
        let img = $(n).find('img.lazy');
        if (a.length > 0 && img.length > 0) {
            let id = a.attr('href');
            let name = a.attr('title');
            let pic = img.attr('data-src') || img.attr('src');
            let remark = $(n).find('span.public-list-prb').text();
            videos.push({
                vod_id: id,
                vod_name: name,
                vod_pic: pic,
                vod_remarks: remark,
            });
        }
    });
    return videos;
}

async function homeVod() {
    const html = await request(siteUrl, null, true);
    const $ = load(html);
    let videos = getVideos($);
    return JSON.stringify({
        list: videos,
    });
}

async function category(tid, pg, filter, extend) {
    if (!pg) pg = 1;
    let area = extend.area || '';
    let by = extend.by || '';
    let clazz = extend.class || '';
    let lang = extend.lang || '';
    let letter = extend.letter || '';
    let year = extend.year || '';
    
    let url = siteUrl + `/show/${tid}-${encodeURIComponent(area)}-${encodeURIComponent(by)}-${encodeURIComponent(clazz)}-${encodeURIComponent(lang)}-${encodeURIComponent(letter)}---${pg}---${encodeURIComponent(year)}/`;
    
    const html = await request(url, null, true);
    const $ = load(html);
    let videos = getVideos($);
    
    return JSON.stringify({
        page: parseInt(pg),
        pagecount: videos.length === 0 ? parseInt(pg) : parseInt(pg) + 1,
        limit: 40,
        total: 999,
        list: videos,
    });
}

async function detail(id) {
    try {
        let url = siteUrl + id;
        const html = await request(url, null, true);
        const $ = load(html);
        
        let title = $('h3.slide-info-title').text();
        let pic = $('.detail-pic img').attr('data-src');
        
        let infos = $('.slide-info');
        let year = '', area = '', clazz = '', remark = '', director = '', actor = '';
        infos.each((i, n) => {
            let text = $(n).text();
            if (text.indexOf('导演') >= 0) {
                director = $(n).find('a').map((i, a) => $(a).text()).get().join(', ');
            } else if (text.indexOf('演员') >= 0) {
                actor = $(n).find('a').map((i, a) => $(a).text()).get().join(', ');
            } else if (text.indexOf('备注') >= 0) {
                remark = text.replace('备注 :', '').trim();
            } else if (text.indexOf('更新') >= 0) {
                if(!remark) remark = text.replace('更新 :', '').trim();
            } else if (i === 0) {
                let remarks = $(n).find('span.slide-info-remarks').map((i, s) => $(s).text().trim()).get();
                year = remarks[0] || '';
                area = remarks[1] || '';
                clazz = $(n).find('a').last().text() || '';
            }
        });
        
        let content = $('#height_limit').text();
        
        let playFroms = [];
        $('.anthology-tab a').each((i, n) => {
            playFroms.push($(n).text().trim().replace(/[\d\s]+$/, ''));
        });
        
        let playUrls = [];
        $('.anthology-list-play').each((i, list) => {
            let urls = [];
            $(list).find('li a').each((j, a) => {
                urls.push($(a).text().trim() + '$' + $(a).attr('href'));
            });
            playUrls.push(urls.join('#'));
        });
        
        let video = {
            vod_id: id,
            vod_name: title,
            vod_pic: pic,
            vod_year: year,
            vod_area: area,
            vod_class: clazz,
            vod_remarks: remark,
            vod_director: director,
            vod_actor: actor,
            vod_content: content,
            vod_play_from: playFroms.join('$$$'),
            vod_play_url: playUrls.join('$$$')
        };
        
        return JSON.stringify({ list: [video] });
    } catch (e) {}
    return null;
}

async function search(wd, quick, pg) {
    if (!pg) pg = 1;
    let url = siteUrl + `/ss/${encodeURIComponent(wd)}----------${pg}---/`;
    const html = await request(url, null, true);
    const $ = load(html);
    
    let videos = [];
    $('.search-box').each((i, n) => {
        let a = $(n).find('a.public-list-exp');
        let img = $(n).find('img.lazy');
        let id = a.attr('href');
        let name = $(n).find('.thumb-txt a').text();
        let pic = img.attr('data-src');
        let remark = $(n).find('span.public-list-prb').text();
        videos.push({
            vod_id: id,
            vod_name: name,
            vod_pic: pic,
            vod_remarks: remark,
        });
    });
    return JSON.stringify({
        page: parseInt(pg),
        pagecount: videos.length === 0 ? parseInt(pg) : parseInt(pg) + 1,
        list: videos,
    });
}

function base64Decode(text) {
    return Crypto.enc.Utf8.stringify(Crypto.enc.Base64.parse(text));
}

async function play(flag, id, flags) {
    let playUrl = '';
    try {
        let playPage = siteUrl + id;
        let html = await request(playPage, null, true);

        let match = html.match(/var player_aaaa=(.*?)<\/script>/s);
        if (!match) {
            return JSON.stringify({ parse: 1, url: id });
        }

        let player = JSON.parse(match[1].trim().replace(/;$/, ''));
        playUrl = player.url || '';
        let next = player.link_next || '';
        let title = '在线观看';

        if (player.vod_data && player.vod_data.vod_name) {
            let nid = player.nid ? player.nid : '';
            title = '剧集《' + player.vod_data.vod_name + '》' + nid + '在线观看';
        }

        if (player.encrypt == 1) {
            playUrl = unescape(playUrl);
        } else if (player.encrypt == 2) {
            playUrl = unescape(base64Decode(playUrl));
        }

        if (/\.m3u8|\.mp4/i.test(playUrl)) {
            return JSON.stringify({
                parse: 0,
                url: playUrl,
                headers: { "User-Agent": headers['User-Agent'] }
            });
        }

        let nextUrl = siteUrl + next.replace(/\\\//g, '/');
        let jxUrl = "https://play.brovod.com/?url=" + encodeURIComponent(playUrl) + "&next=" + encodeURIComponent(nextUrl) + "&title=" + encodeURIComponent(title);

        let jx = await req(jxUrl, {
            method: 'get',
            headers: {
                "User-Agent": headers['User-Agent'],
                "Referer": playPage
            }
        });

        let configMatch = jx.content.match(/var config\s*=\s*(\{[\s\S]*?\})\s*(?:;|<\/script>)/);
        if (!configMatch) {
            return JSON.stringify({ parse: 1, url: playUrl });
        }

        let configStr = configMatch[1].replace(/,\s*\}/g, '}');
        let config = JSON.parse(configStr);

        let t = new Date();
        t.setMinutes(0, 0, 0);
        let hourlyStamp = Math.floor(t.getTime() / 1000);
        let key = Crypto.SHA256(hourlyStamp + "cnmdhb").toString(Crypto.enc.Hex).toLowerCase();

        let postData = {
            url: config.url.replace(/%20/g, '+'),
            pbgjz: config.pbgjz || '',
            dmkey: config.dmkey || '',
            key: key
        };

        let result = await req("https://play.brovod.com/JX", {
            method: "post",
            headers: {
                "User-Agent": headers['User-Agent'],
                "Referer": "https://play.brovod.com/",
                "Origin": "https://play.brovod.com",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest"
            },
            data: JSON.stringify(postData),
            postType: ""
        });

        let json = JSON.parse(result.content);
        let finalUrl = json.cnmdhb || json.url || '';

        if (finalUrl) {
            return JSON.stringify({
                parse: 0,
                url: finalUrl,
                headers: { "User-Agent": headers['User-Agent'] }
            });
        }

        return JSON.stringify({ parse: 1, url: playUrl });
    } catch (e) {
        return JSON.stringify({ parse: 1, url: playUrl || id });
    }
}

function genFilterObj() {
    return {
        "Movies": [
            {"key": "class", "name": "剧情", "value": [{"n": "全部", "v": ""}, {"n": "喜剧", "v": "喜剧"}, {"n": "爱情", "v": "爱情"}, {"n": "动作", "v": "动作"}, {"n": "科幻", "v": "科幻"}, {"n": "剧情", "v": "剧情"}, {"n": "战争", "v": "战争"}, {"n": "警匪", "v": "警匪"}, {"n": "犯罪", "v": "犯罪"}, {"n": "动画", "v": "动画"}, {"n": "奇幻", "v": "奇幻"}, {"n": "武侠", "v": "武侠"}, {"n": "冒险", "v": "冒险"}, {"n": "枪战", "v": "枪战"}, {"n": "恐怖", "v": "恐怖"}, {"n": "悬疑", "v": "悬疑"}, {"n": "惊悚", "v": "惊悚"}, {"n": "经典", "v": "经典"}, {"n": "青春", "v": "青春"}, {"n": "家庭", "v": "家庭"}, {"n": "记录", "v": "记录"}]},
            {"key": "area", "name": "地区", "value": [{"n": "全部", "v": ""}, {"n": "大陆", "v": "大陆"}, {"n": "香港", "v": "香港"}, {"n": "台湾", "v": "台湾"}, {"n": "美国", "v": "美国"}, {"n": "法国", "v": "法国"}, {"n": "英国", "v": "英国"}, {"n": "日本", "v": "日本"}, {"n": "韩国", "v": "韩国"}, {"n": "德国", "v": "德国"}, {"n": "泰国", "v": "泰国"}, {"n": "印度", "v": "印度"}, {"n": "意大利", "v": "意大利"}, {"n": "西班牙", "v": "西班牙"}, {"n": "加拿大", "v": "加拿大"}]},
            {"key": "year", "name": "年份", "value": [{"n": "全部", "v": ""}, {"n": "2025", "v": "2025"}, {"n": "2024", "v": "2024"}, {"n": "2023", "v": "2023"}, {"n": "2022", "v": "2022"}, {"n": "2021", "v": "2021"}, {"n": "2020", "v": "2020"}, {"n": "2019", "v": "2019"}, {"n": "2018", "v": "2018"}, {"n": "2017", "v": "2017"}, {"n": "2016", "v": "2016"}, {"n": "2015", "v": "2015"}, {"n": "2014", "v": "2014"}, {"n": "2013", "v": "2013"}, {"n": "2012", "v": "2012"}, {"n": "2011", "v": "2011"}, {"n": "2010", "v": "2010"}]},
            {"key": "lang", "name": "语言", "value": [{"n": "全部", "v": ""}, {"n": "国语", "v": "国语"}, {"n": "英语", "v": "英语"}, {"n": "粤语", "v": "粤语"}, {"n": "韩语", "v": "韩语"}, {"n": "日语", "v": "日语"}, {"n": "法语", "v": "法语"}]},
            {"key": "by", "name": "排序", "value": [{"n": "时间", "v": "time"}, {"n": "人气", "v": "hits"}, {"n": "评分", "v": "score"}]},
            {"key": "letter", "name": "字母", "value": [{"n": "全部", "v": ""}, {"n": "A", "v": "A"}, {"n": "B", "v": "B"}, {"n": "C", "v": "C"}, {"n": "D", "v": "D"}, {"n": "E", "v": "E"}, {"n": "F", "v": "F"}, {"n": "G", "v": "G"}, {"n": "H", "v": "H"}, {"n": "I", "v": "I"}, {"n": "J", "v": "J"}, {"n": "K", "v": "K"}, {"n": "L", "v": "L"}, {"n": "M", "v": "M"}, {"n": "N", "v": "N"}, {"n": "O", "v": "O"}, {"n": "P", "v": "P"}, {"n": "Q", "v": "Q"}, {"n": "R", "v": "R"}, {"n": "S", "v": "S"}, {"n": "T", "v": "T"}, {"n": "U", "v": "U"}, {"n": "V", "v": "V"}, {"n": "W", "v": "W"}, {"n": "X", "v": "X"}, {"n": "Y", "v": "Y"}, {"n": "Z", "v": "Z"}]}
        ],
        "TV": [
            {"key": "class", "name": "剧情", "value": [{"n": "全部", "v": ""}, {"n": "古装", "v": "古装"}, {"n": "战争", "v": "战争"}, {"n": "青春", "v": "青春"}, {"n": "偶像", "v": "偶像"}, {"n": "喜剧", "v": "喜剧"}, {"n": "家庭", "v": "家庭"}, {"n": "犯罪", "v": "犯罪"}, {"n": "动作", "v": "动作"}, {"n": "奇幻", "v": "奇幻"}, {"n": "剧情", "v": "剧情"}, {"n": "历史", "v": "历史"}, {"n": "经典", "v": "经典"}, {"n": "情景", "v": "情景"}, {"n": "商战", "v": "商战"}, {"n": "网剧", "v": "网剧"}]},
            {"key": "area", "name": "地区", "value": [{"n": "全部", "v": ""}, {"n": "大陆", "v": "大陆"}, {"n": "韩国", "v": "韩国"}, {"n": "香港", "v": "香港"}, {"n": "台湾", "v": "台湾"}, {"n": "日本", "v": "日本"}, {"n": "美国", "v": "美国"}, {"n": "泰国", "v": "泰国"}, {"n": "英国", "v": "英国"}, {"n": "新加坡", "v": "新加坡"}]},
            {"key": "year", "name": "年份", "value": [{"n": "全部", "v": ""}, {"n": "2025", "v": "2025"}, {"n": "2024", "v": "2024"}, {"n": "2023", "v": "2023"}, {"n": "2022", "v": "2022"}, {"n": "2021", "v": "2021"}, {"n": "2020", "v": "2020"}, {"n": "2019", "v": "2019"}, {"n": "2018", "v": "2018"}, {"n": "2017", "v": "2017"}, {"n": "2016", "v": "2016"}, {"n": "2015", "v": "2015"}, {"n": "2014", "v": "2014"}, {"n": "2013", "v": "2013"}, {"n": "2012", "v": "2012"}, {"n": "2011", "v": "2011"}, {"n": "2010", "v": "2010"}]},
            {"key": "lang", "name": "语言", "value": [{"n": "全部", "v": ""}, {"n": "国语", "v": "国语"}, {"n": "英语", "v": "英语"}, {"n": "粤语", "v": "粤语"}, {"n": "韩语", "v": "韩语"}, {"n": "日语", "v": "日语"}]},
            {"key": "by", "name": "排序", "value": [{"n": "时间", "v": "time"}, {"n": "人气", "v": "hits"}, {"n": "评分", "v": "score"}]},
            {"key": "letter", "name": "字母", "value": [{"n": "全部", "v": ""}, {"n": "A", "v": "A"}, {"n": "B", "v": "B"}, {"n": "C", "v": "C"}, {"n": "D", "v": "D"}, {"n": "E", "v": "E"}, {"n": "F", "v": "F"}, {"n": "G", "v": "G"}, {"n": "H", "v": "H"}, {"n": "I", "v": "I"}, {"n": "J", "v": "J"}, {"n": "K", "v": "K"}, {"n": "L", "v": "L"}, {"n": "M", "v": "M"}, {"n": "N", "v": "N"}, {"n": "O", "v": "O"}, {"n": "P", "v": "P"}, {"n": "Q", "v": "Q"}, {"n": "R", "v": "R"}, {"n": "S", "v": "S"}, {"n": "T", "v": "T"}, {"n": "U", "v": "U"}, {"n": "V", "v": "V"}, {"n": "W", "v": "W"}, {"n": "X", "v": "X"}, {"n": "Y", "v": "Y"}, {"n": "Z", "v": "Z"}]}
        ],
        "Shows": [
            {"key": "class", "name": "剧情", "value": [{"n": "全部", "v": ""}, {"n": "脱口秀", "v": "脱口秀"}, {"n": "真人秀", "v": "真人秀"}, {"n": "选秀", "v": "选秀"}, {"n": "美食", "v": "美食"}, {"n": "旅游", "v": "旅游"}, {"n": "访谈", "v": "访谈"}, {"n": "播报", "v": "播报"}]},
            {"key": "area", "name": "地区", "value": [{"n": "全部", "v": ""}, {"n": "大陆", "v": "大陆"}, {"n": "韩国", "v": "韩国"}, {"n": "香港", "v": "香港"}, {"n": "台湾", "v": "台湾"}, {"n": "日本", "v": "日本"}, {"n": "美国", "v": "美国"}]},
            {"key": "year", "name": "年份", "value": [{"n": "全部", "v": ""}, {"n": "2025", "v": "2025"}, {"n": "2024", "v": "2024"}, {"n": "2023", "v": "2023"}, {"n": "2022", "v": "2022"}, {"n": "2021", "v": "2021"}, {"n": "2020", "v": "2020"}]},
            {"key": "by", "name": "排序", "value": [{"n": "时间", "v": "time"}, {"n": "人气", "v": "hits"}, {"n": "评分", "v": "score"}]}
        ],
        "Anime": [
            {"key": "class", "name": "剧情", "value": [{"n": "全部", "v": ""}, {"n": "热血", "v": "热血"}, {"n": "格斗", "v": "格斗"}, {"n": "恋爱", "v": "恋爱"}, {"n": "校园", "v": "校园"}, {"n": "搞笑", "v": "搞笑"}, {"n": "玄幻", "v": "玄幻"}, {"n": "剧情", "v": "剧情"}, {"n": "战争", "v": "战争"}, {"n": "仙侠", "v": "仙侠"}]},
            {"key": "area", "name": "地区", "value": [{"n": "全部", "v": ""}, {"n": "大陆", "v": "大陆"}, {"n": "日本", "v": "日本"}, {"n": "美国", "v": "美国"}]},
            {"key": "year", "name": "年份", "value": [{"n": "全部", "v": ""}, {"n": "2025", "v": "2025"}, {"n": "2024", "v": "2024"}, {"n": "2023", "v": "2023"}, {"n": "2022", "v": "2022"}, {"n": "2021", "v": "2021"}, {"n": "2020", "v": "2020"}]},
            {"key": "by", "name": "排序", "value": [{"n": "时间", "v": "time"}, {"n": "人气", "v": "hits"}, {"n": "评分", "v": "score"}]}
        ],
        "Snaps": [
            {"key": "year", "name": "年份", "value": [{"n": "全部", "v": ""}, {"n": "2025", "v": "2025"}, {"n": "2024", "v": "2024"}, {"n": "2023", "v": "2023"}]},
            {"key": "by", "name": "排序", "value": [{"n": "时间", "v": "time"}, {"n": "人气", "v": "hits"}, {"n": "评分", "v": "score"}]}
        ],
        "Documentaries": [
            {"key": "area", "name": "地区", "value": [{"n": "全部", "v": ""}, {"n": "大陆", "v": "大陆"}, {"n": "美国", "v": "美国"}, {"n": "英国", "v": "英国"}]},
            {"key": "year", "name": "年份", "value": [{"n": "全部", "v": ""}, {"n": "2025", "v": "2025"}, {"n": "2024", "v": "2024"}, {"n": "2023", "v": "2023"}]}
        ]
    };
}

export function __jsEvalReturn() {
    return {
        init: init,
        home: home,
        homeVod: homeVod,
        category: category,
        detail: detail,
        play: play,
        search: search,
    };
}
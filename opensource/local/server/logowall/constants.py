"""Static lookup tables: office codes, regions and the built-in brand logo DB."""
import json
import logging

from . import config

log = logging.getLogger('logowall')

OFFICE_MAP = {
    'BJI': '北京', 'CDU': '成都', 'CQI': '重庆', 'CSH': '长沙',
    'DLI': '大连', 'GZH': '广州', 'NJI': '南京', 'QDA': '青岛',
    'SHA': '上海', 'SUZ': '苏州', 'SZH': '深圳', 'TWN': '台湾',
    'WHA': '武汉', 'XAN': '西安', 'XME': '厦门', 'ZZH': '郑州',
}

# Region grouping
REGION_MAP = {
    'BJI': '华北', 'DLI': '华北', 'QDA': '华北', 'XAN': '华北',
    'SHA': '华东', 'SUZ': '华东', 'NJI': '华东', 'ZZH': '华东',
    'GZH': '华南', 'SZH': '华南', 'WHA': '华南', 'CSH': '华南', 'XME': '华南',
    'CDU': '华西', 'CQI': '华西',
    'TWN': '台湾',
}
# Hong Kong office code if added later
REGION_MAP.setdefault('HKG', '香港')


def get_region(office_code):
    return REGION_MAP.get(office_code, '其他')


# ---------------------------------------------------------------------------
# Brand/logo keyword database (used for auto-match in admin / Excel import).
# These point at third-party icon sites and may go stale; deployments can
# override or extend them with DATA_DIR/brand_keywords.json ({"keyword": url}),
# where an empty url removes a built-in entry.
# ---------------------------------------------------------------------------
_BUILTIN_BRAND_KEYWORDS = {
    '小红书': 'https://cdn-icons-png.flaticon.com/512/3536/3536745.png',
    '华为': 'https://pic.pngsucai.com/00/80/95/9d5ae013f7d16592.webp',
    '百度': 'https://bkimg.cdn.bcebos.com/smart/b8014a90f603738da97755563251a751f81986184626-bkimg-process,v_1,rw_1,rh_1,pad_1,color_ffffff?x-bce-process=image/format,f_auto',
    '阿里巴巴': 'https://pic.pngsucai.com/00/78/52/e88d67fa29444baf.webp',
    '腾讯': 'https://cdn-icons-png.flaticon.com/512/1944/1944478.png',
    '字节跳动': 'http://logo800.cn/uploads/logoxinshang/56/logo800_16491624083325586.png',
    '美团': 'https://logo800.cn/uploads/logoxinshang/58/logo800_16491625929115709.png',
    '小米': 'http://www.kuaipng.com/Uploads/pic/w/2021/03-31/98651/water_98651_698_698_.png',
    '京东': 'http://www.kuaipng.com/Uploads/pic/w/2018/09-12/47466/water_47466_698_698_.png',
    '招商银行': 'https://logo800.cn/uploads/logoxinshang/56/logo800_16491623685385554.png',
    '渣打银行': 'https://logo800.cn/uploads/logoxinshang/56/logo800_16491623510295541.png',
    '中国平安': 'https://logo800.cn/uploads/logoxinshang/54/logo800_16491621460625367.png',
    '中国人寿': 'https://pic.616pic.com/ys_img/00/04/50/KQA6o4catq.jpg',
    'IBM': 'https://pngimg.com/uploads/ibm/ibm_PNG19658.png',
    '微软': 'https://cdn-icons-png.flaticon.com/512/732/732221.png',
    '苹果': 'https://cdn-icons-png.flaticon.com/512/0/747.png',
    'Google': 'https://cdn-icons-png.flaticon.com/512/2702/2702602.png',
    '西门子': 'https://cdn-icons-png.flaticon.com/512/1602/1602062.png',
    '三星': 'https://cdn-icons-png.flaticon.com/512/732/732106.png',
    '丰田': 'https://cdn-icons-png.flaticon.com/512/196/196600.png',
    '波音': 'https://www.pngmart.com/files/23/Boeing-Logo-PNG-Picture.png',
    '特斯拉': 'https://cdn-icons-png.flaticon.com/512/732/732282.png',
    'Netflix': 'https://cdn-icons-png.flaticon.com/512/732/732228.png',
    'Meta': 'https://cdn-icons-png.flaticon.com/512/5968/5968764.png',
    '亚马逊': 'https://cdn-icons-png.flaticon.com/512/2702/2702652.png',
    '甲骨文': 'https://cdn-icons-png.flaticon.com/512/5968/5968480.png',
    'SAP': 'https://cdn-icons-png.flaticon.com/512/5968/5968474.png',
    'Salesforce': 'https://cdn-icons-png.flaticon.com/512/5968/5968484.png',
    '英特尔': 'https://cdn-icons-png.flaticon.com/512/1602/1602031.png',
    '思科': 'https://cdn-icons-png.flaticon.com/512/732/732138.png',
    '高通': 'https://cdn-icons-png.flaticon.com/512/5969/5969138.png',
    '英伟达': 'https://cdn-icons-png.flaticon.com/512/5969/5969006.png',
    'AMD': 'https://cdn-icons-png.flaticon.com/512/1602/1602010.png',
    'Adobe': 'https://cdn-icons-png.flaticon.com/512/732/732236.png',
    'Autodesk': 'https://www.liblogo.com/img-logo/au96d848-autodesk-logo-download-hd-autodesk-logo-graphic-design-transparent-png-image.png',
    '耐克': 'https://cdn-icons-png.flaticon.com/512/732/732229.png',
    '阿迪达斯': 'https://cdn-icons-png.flaticon.com/512/732/732247.png',
    '星巴克': 'https://cdn-icons-png.flaticon.com/512/5977/5977591.png',
    '麦当劳': 'https://cdn-icons-png.flaticon.com/512/104/104388.png',
    '可口可乐': 'https://cdn-icons-png.flaticon.com/512/732/732222.png',
    '雀巢': 'https://cdn-icons-png.flaticon.com/512/5968/5968464.png',
    '联合利华': 'https://cdn-icons-png.flaticon.com/512/5968/5968852.png',
    '宝洁': 'https://cdn-icons-png.flaticon.com/512/5969/5969030.png',
    '强生': 'https://cdn-icons-png.flaticon.com/512/5968/5968534.png',
    '辉瑞': 'https://cdn-icons-png.flaticon.com/512/5968/5968486.png',
    '罗氏': 'https://cdn-icons-png.flaticon.com/512/5968/5968472.png',
    '诺华': 'https://cdn-icons-png.flaticon.com/512/5968/5968466.png',
    '汇丰银行': 'https://cdn-icons-png.flaticon.com/512/5968/5968456.png',
    '花旗': 'https://cdn-icons-png.flaticon.com/512/5968/5968436.png',
    '摩根大通': 'https://cdn-icons-png.flaticon.com/512/5968/5968446.png',
    '高盛': 'https://cdn-icons-png.flaticon.com/512/5968/5968450.png',
    '普华永道': 'https://cdn-icons-png.flaticon.com/512/5968/5968504.png',
    '德勤': 'https://cdn-icons-png.flaticon.com/512/5968/5968500.png',
    '安永': 'https://cdn-icons-png.flaticon.com/512/5968/5968508.png',
    '毕马威': 'https://cdn-icons-png.flaticon.com/512/5968/5968512.png',
}


def brand_keywords() -> dict:
    """Built-in brand DB merged with the optional DATA_DIR override file."""
    merged = dict(_BUILTIN_BRAND_KEYWORDS)
    path = config.BRAND_KEYWORDS_JSON
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                override = json.load(f)
            for kw, url in override.items():
                if url:
                    merged[str(kw)] = str(url)
                else:
                    merged.pop(str(kw), None)
        except (OSError, ValueError, AttributeError) as e:
            log.warning('Ignoring invalid %s: %s', path, e)
    return merged


def match_brand_logo(company: str):
    """Return (keyword, url) of the first built-in brand matching `company`."""
    company_lower = (company or '').lower()
    if not company_lower:
        return None, None
    for kw, url in brand_keywords().items():
        if kw.lower() in company_lower or company_lower in kw.lower():
            return kw, url
    return None, None

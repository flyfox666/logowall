#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anonymize a real data.json into a safe demo dataset for the open-source release.

Every company name, brand, person, office/city/region and business line is
replaced with a fictional, freshly shuffled (but plausible) value. Logos and
websites are stripped. The record count is kept so the demo looks alive.

Usage:
    python anonymize.py --src /path/to/real/data.json --out /path/to/demo/data.json
"""
import argparse
import json
import random

SEED = 42

BRAND_PRE = ['星辰', '云帆', '天穹', '灵犀', '沧海', '曜石', '青柠', '极光',
             '岚图', '沐光', '知远', '汇川', '明澈', '南风', '望舒', '拾光',
             '澄川', '曜阳', '澜庭', '峻岭']
BRAND_SUF = ['科技', '智联', '信息', '数据', '网络', '云创', '智能', '互联',
             '数字', '通信', '软件', '系统']
COMPANY_TYPE = ['有限公司', '科技有限公司', '咨询有限公司', '信息技术有限公司']
OWNER_SUR = ['林', '陈', '赵', '周', '吴', '郑', '孙', '钱', '冯', '褚',
             '卫', '蒋', '沈', '韩', '杨', '朱', '秦', '尤', '许', '何']
OWNER_GIV = ['思远', '雨桐', '子墨', '欣怡', '浩然', '梦琪', '俊杰', '雅静',
             '天佑', '诗涵', '明轩', '若曦', '志强', '婉婷', '建华', '晓芸',
             '文博', '静怡', '国强', '慧敏']

DEPARTMENTS = ['咨询', '审计', '税务']

# Office code -> city / region (mirrors the server-side maps)
OFFICE_MAP = {
    'BJI': '北京', 'CDU': '成都', 'CQI': '重庆', 'CSH': '长沙',
    'DLI': '大连', 'GZH': '广州', 'NJI': '南京', 'QDA': '青岛',
    'SHA': '上海', 'SUZ': '苏州', 'SZH': '深圳', 'TWN': '台湾',
    'WHA': '武汉', 'XAN': '西安', 'XME': '厦门', 'ZZH': '郑州',
}
REGION_MAP = {
    'BJI': '华北', 'DLI': '华北', 'QDA': '华北', 'XAN': '华北',
    'SHA': '华东', 'SUZ': '华东', 'NJI': '华东', 'ZZH': '华东',
    'GZH': '华南', 'SZH': '华南', 'WHA': '华南', 'CSH': '华南', 'XME': '华南',
    'CDU': '华西', 'CQI': '华西',
    'TWN': '台湾',
}
# Bigger cities appear more often so the demo looks realistic
OFFICE_WEIGHTS = {
    'SHA': 4, 'BJI': 4, 'SZH': 3, 'GZH': 3, 'SUZ': 2, 'NJI': 2, 'CDU': 2,
    'WHA': 2, 'CSH': 1, 'XME': 1, 'QDA': 1, 'DLI': 1, 'XAN': 1, 'ZZH': 1,
    'CQI': 1, 'TWN': 1,
}

COLORS = ['#4F46E5', '#7C3AED', '#DB2777', '#DC2626', '#EA580C',
          '#CA8A04', '#16A34A', '#0891B2', '#2563EB', '#9333EA',
          '#0D9488', '#65A30D', '#C026D3', '#0284C7', '#475569']


def color_from_name(name: str) -> str:
    h = 0
    for ch in name or '':
        h = ord(ch) + ((h << 5) - h)
    return COLORS[abs(h) % len(COLORS)]


def weighted_office(rng: random.Random) -> str:
    codes = list(OFFICE_WEIGHTS)
    weights = [OFFICE_WEIGHTS[c] for c in codes]
    return rng.choices(codes, weights=weights, k=1)[0]


def main():
    ap = argparse.ArgumentParser(description='Anonymize data.json for open-source demo')
    ap.add_argument('--src', required=True, help='path to the real data.json')
    ap.add_argument('--out', required=True, help='path to write the demo data.json')
    args = ap.parse_args()

    rng = random.Random(SEED)

    with open(args.src, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Unique fictional brand pool (shuffled combinations)
    combos = [(p, s) for p in BRAND_PRE for s in BRAND_SUF]
    rng.shuffle(combos)
    owner_pool = [s + g for s in OWNER_SUR for g in OWNER_GIV]
    rng.shuffle(owner_pool)

    records = data.get('records', [])
    for i, r in enumerate(records):
        # Fresh random office / city / region
        code = weighted_office(rng)
        city = OFFICE_MAP[code]

        pre, suf = combos[i % len(combos)]
        brand = pre + suf
        company = brand + ('（%s）' % city) + rng.choice(COMPANY_TYPE)

        r['office_code'] = code
        r['office_city'] = city
        r['region'] = REGION_MAP[code]
        r['company'] = company
        r['brand'] = brand
        r['owners'] = rng.sample(owner_pool, rng.choice([1, 1, 2]))
        r['departments'] = rng.sample(DEPARTMENTS, rng.choice([1, 1, 2]))
        r['logo_url'] = None
        r['website'] = ''
        r['color'] = color_from_name(company)
        # Replace the free-text description with a fully fictional one —
        # real profiles may embed legal names, capital, subsidiaries, etc.
        r['description'] = ('%s，成立于%d年，位于%s市，是一家专注于%s领域的'
                            '虚构演示企业。本条目由开源演示数据生成器创建，'
                            '与任何真实机构无关。'
                            % (company, rng.randint(1998, 2023), city, brand))

    data['title'] = '客户品牌墙'
    data['title_en'] = 'CLIENT LOGO WALL'
    data['tagline'] = 'OFFICE × BUSINESS LINE  ·  连接客户价值，共创长期合作'
    data['footer_text'] = '连接  ·  协作  ·  共创价值'
    data['theme'] = 'classic'
    data['bg_pattern'] = 'none'
    data.pop('custom_primary', None)
    data.pop('custom_accent', None)

    # Rebuild aggregate fields the same way the server does
    data['total_count'] = len(records)
    data['offices'] = sorted({r['office_city'] for r in records if r.get('office_city')})
    data['departments'] = sorted({d for r in records for d in (r.get('departments') or [])})
    data['regions'] = sorted({r.get('region', '其他') for r in records if r.get('region')})

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Distribution summary for a quick sanity check
    cities = {}
    for r in records:
        cities[r['office_city']] = cities.get(r['office_city'], 0) + 1
    print('Wrote %d anonymized records to %s' % (len(records), args.out))
    print('City distribution: ' + ', '.join('%s=%d' % kv for kv in sorted(cities.items(), key=lambda x: -x[1])))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Movie Fairy - 数据抓取脚本
抓取豆瓣电影 Top 榜单，输出 movies.json
"""

import argparse
import json
import os
import re
import sys
import time

import requests
import yaml
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 豆瓣平台图标文件名 → 中文名映射
PLATFORM_MAP = {
    "miguvideo": "咪咕视频",
    "qq": "腾讯视频",
    "bilibili": "哔哩哔哩",
    "iqiyi": "爱奇艺",
    "youku": "优酷视频",
    "mgtv": "芒果TV",
    "hulu": "Hulu",
    "netflix": "Netflix",
    "disney": "Disney+",
    "amazon": "Amazon",
    "cctv": "CCTV",
    "xigua": "西瓜视频",
    "pptv": "PPTV",
    "sohu": "搜狐视频",
    "1905": "1905电影网",
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_ids(ids_str):
    """解析 ID 列表，如 '1,3,5-10,15' → {1, 3, 5, 6, 7, 8, 9, 10, 15}"""
    ids = set()
    for part in ids_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            ids.update(range(int(start), int(end) + 1))
        else:
            ids.add(int(part))
    return ids


def fetch_page(url, retries=3, session=None):
    for i in range(retries):
        try:
            if session:
                resp = session.get(url, timeout=15)
            else:
                resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            print(f"  请求失败 ({i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(3)
    return None


def parse_streaming_platforms(soup):
    """从详情页解析「在哪儿看这部电影」板块，返回平台列表"""
    platforms = []

    # 定位 h2 标题
    h2 = soup.find("h2", string=lambda t: t and "在哪儿看" in t)
    if not h2:
        return platforms

    # 取 h2 所在容器（通常为 <div> 或 <section>）
    container = h2.find_parent()
    if not container:
        return platforms

    items = container.find_all("li")
    for li in items:
        platform_name = ""
        access_type = ""
        url = ""

        # 1) 从 <a> 标签提取平台名和链接
        a_tag = li.find("a")
        if a_tag:
            url = a_tag.get("href", "")
            a_text = a_tag.get_text(strip=True)
            if a_text:
                platform_name = a_text

        # 2) 从图标文件名推断平台名
        if not platform_name:
            img = li.find("img")
            if img:
                src = img.get("src", "")
                for key, name in PLATFORM_MAP.items():
                    if key in src:
                        platform_name = name
                        break
                if not platform_name:
                    platform_name = img.get("alt", "")

        # 3) 从 li 文本中提取（排除观看方式描述）
        if not platform_name:
            text = li.get_text(strip=True)
            for kw in ("VIP免费观看", "免费观看", "用券观看", "付费观看",
                        "会员免费观看", "单片付费"):
                text = text.replace(kw, "")
            platform_name = text.strip()

        # 提取观看方式
        li_text = li.get_text(strip=True)
        for kw in ("VIP免费观看", "会员免费观看", "免费观看",
                    "用券观看", "付费观看", "单片付费"):
            if kw in li_text:
                access_type = kw
                break

        if platform_name:
            entry = {"platform": platform_name}
            if access_type:
                entry["type"] = access_type
            if url:
                entry["url"] = url
            platforms.append(entry)

    return platforms


def fetch_streaming_info(movies, cookie_str=None):
    """逐部抓取详情页的在线播放信息，直接写入每部电影的 streaming 字段"""
    session = requests.Session()
    session.headers.update(HEADERS)
    if cookie_str:
        try:
            session.headers["Cookie"] = cookie_str.encode('ascii', 'ignore').decode('ascii')
        except Exception as e:
            print(f"  Cookie 编码失败: {e}")

    total = len(movies)
    updated = 0

    for i, movie in enumerate(movies):
        douban_url = movie.get("douban_url")
        if not douban_url:
            movie["streaming"] = []
            continue

        title = movie.get("title", "")
        print(f"  [{i+1}/{total}] {title} ...", end=" ", flush=True)

        html = fetch_page(douban_url, retries=2, session=session)
        if not html:
            print("失败")
            movie["streaming"] = []
            continue

        if "登录跳转" in html:
            print("被反爬拦截，需 --cookie")
            movie["streaming"] = []
            continue

        soup = BeautifulSoup(html, "html.parser")
        platforms = parse_streaming_platforms(soup)
        movie["streaming"] = platforms
        updated += 1

        count = len(platforms)
        if count:
            names = ", ".join(p["platform"] for p in platforms)
            print(f"{count} 平台 ({names})")
        else:
            print("暂无")

        time.sleep(3)

    print(f"\n  已获取 {updated}/{total} 部电影的在线播放信息")
    return movies


def parse_movie_info(info_text):
    """从 '1994 / 美国 / 犯罪 剧情' 格式中提取年份、国家、类别"""
    year = ""
    countries = ""
    categories = []

    parts = [p.strip() for p in info_text.split("/")]
    for part in parts:
        if re.match(r"^\d{4}$", part):
            year = int(part)
        elif not year and re.match(r"^\d{4}", part):
            year = int(part.strip()[:4])
        elif any("\u4e00" <= c <= "\u9fff" for c in part) and not categories:
            if not countries:
                countries = part
            else:
                categories = part.split()
        elif part and not countries:
            countries = part
        else:
            categories = part.split()

    # 尝试更精准的提取
    parts2 = info_text.split("/")
    if len(parts2) >= 3:
        year_str = parts2[0].strip()
        if year_str.isdigit():
            year = int(year_str)
        countries = parts2[1].strip()
        categories = parts2[2].strip().split()

    return year, countries, categories


def scrape_douban(config, top_n, cookie_str=None):
    """抓取豆瓣 Top 榜单"""
    base_url = config["douban"]["base_url"]
    per_page = config["douban"]["per_page"]
    pages = (top_n + per_page - 1) // per_page

    movies = []

    session = None
    if cookie_str:
        session = requests.Session()
        session.headers.update(HEADERS)
        try:
            session.headers["Cookie"] = cookie_str.encode('ascii', 'ignore').decode('ascii')
        except Exception as e:
            print(f"  Cookie 编码失败: {e}")
            session = None

    for page in range(pages):
        start = page * per_page
        fetch_count = min(per_page, top_n - len(movies))
        if fetch_count <= 0:
            break

        url = f"{base_url}?start={start}&filter="
        print(f"正在抓取第 {page+1}/{pages} 页: {url}")

        html = fetch_page(url, session=session)
        if not html:
            print(f"  跳过第 {page+1} 页（请求失败）")
            continue

        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("ol.grid_view li")

        if not items:
            print("  未找到电影条目，可能被反爬限制。")
            print("  建议：稍后重试，或使用代理。")
            break

        for item in items:
            if len(movies) >= top_n:
                break

            img = item.select_one(".pic img")
            poster_url = img["src"] if img else ""
            title = img["alt"] if img else ""

            link_el = item.select_one(".pic a")
            douban_url = link_el["href"] if link_el else ""

            rating_el = item.select_one(".rating_num")
            rating = float(rating_el.text.strip()) if rating_el else 0.0

            quote_el = item.select_one("p.quote span")
            quote = quote_el.text.strip() if quote_el else ""

            bd = item.select_one(".bd")
            year, countries, categories = 0, "", []
            if bd:
                info_lines = bd.get_text("\n").split("\n")
                for line in info_lines:
                    line = line.strip()
                    if "/" in line and any(c.isdigit() for c in line):
                        year, countries, categories = parse_movie_info(line)
                        break

            movie = {
                "id": len(movies) + 1,
                "title": title,
                "poster_url": poster_url,
                "poster_url_remote": poster_url,  # 保留原始豆瓣 CDN URL
                "synopsis": quote,
                "rating": rating,
                "categories": categories,
                "year": year,
                "countries": countries,
                "douban_url": douban_url,
            }
            movies.append(movie)
            print(f"  [{len(movies):3d}] {title} ({year}) {rating}")

        if page < pages - 1:
            time.sleep(2)

    return movies


def download_posters(movies, posters_dir, session=None, update_url=True):
    """下载海报图片到本地"""
    os.makedirs(posters_dir, exist_ok=True)
    for movie in movies:
        poster_url = movie.get("poster_url", "")
        douban_url = movie.get("douban_url", "")
        filename = f"{movie['id']:03d}.jpg"
        filepath = os.path.join(posters_dir, filename)

        if os.path.exists(filepath):
            continue

        # 优先用 poster_url_remote（原始豆瓣 CDN URL），直接下载不走详情页
        remote_url = movie.get("poster_url_remote", "")

        if poster_url.startswith("data/") or not poster_url:
            # 有 CDN URL 直接用
            if remote_url and remote_url.startswith("http"):
                poster_url = remote_url
            elif douban_url:
                # 兜底：从详情页取（可能被 403）
                try:
                    if session:
                        resp = session.get(douban_url, headers=HEADERS, timeout=15)
                    else:
                        resp = requests.get(douban_url, headers=HEADERS, timeout=15)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "html.parser")
                    img = soup.select_one("#mainpic img")
                    if not img or not img.get("src"):
                        continue
                    poster_url = img["src"]
                except Exception as e:
                    print(f"  获取海报URL失败 [{movie['title']}]: {e}")
                    continue

        # 下载海报
        try:
            if session:
                img_resp = session.get(poster_url, headers={**HEADERS, "Referer": "https://movie.douban.com/"}, timeout=15)
            else:
                img_resp = requests.get(poster_url, headers={**HEADERS, "Referer": "https://movie.douban.com/"}, timeout=15)
            img_resp.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(img_resp.content)
            print(f"  下载海报: {movie['title']}")
            if update_url and not movie.get("poster_url", "").startswith("data/"):
                movie["poster_url"] = f"data/posters/{filename}"
            time.sleep(0.3)
        except Exception as e:
            print(f"  海报下载失败 [{movie['title']}]: {e}")


def generate_data_js(movies, path):
    """将 movies 数据写入 data.js（供前端静态加载）"""
    js = "// Movie Fairy - 电影数据（由 fetch_movies.py 生成）\n"
    js += "const MOVIES = "
    js += json.dumps(movies, ensure_ascii=False, indent=2)
    js += ";\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"  前端数据已同步到 {path}（{len(movies)} 部）")


def main():
    parser = argparse.ArgumentParser(description="Movie Fairy 数据抓取脚本")
    parser.add_argument("--source", default=None, help="数据源: douban / imdb")
    parser.add_argument("--top", type=int, default=None, help="抓取数量")
    parser.add_argument("--ids", default=None,
                        help="指定电影 ID，如 1,3,5-10,15")
    parser.add_argument("--download-posters", action="store_true",
                        help="下载海报到本地")
    parser.add_argument("--fetch-streaming", action="store_true",
                        help="抓取每部电影的在线播放信息")
    parser.add_argument("--cookie", default=None,
                        help="豆瓣 cookie 字符串（访问详情页必需）")
    args = parser.parse_args()

    config = load_config()
    output_path = os.path.join(SCRIPT_DIR, config["output"]["movies_json"])

    id_set = parse_ids(args.ids) if args.ids else None
    has_ops = args.download_posters or args.fetch_streaming

    # ── 数据来源：抓取或加载 ──
    if args.top:
        # 有 --top：抓取
        source = args.source or config.get("source", "douban")
        top_n = args.top
        print(f"数据源: {source}, 抓取数量: {top_n}\n")
        if source == "douban":
            movies = scrape_douban(config, top_n, cookie_str=args.cookie)
        else:
            print(f"暂不支持数据源: {source}")
            sys.exit(1)
        if not movies:
            print("未抓取到任何电影数据。")
            sys.exit(1)

    elif id_set and not has_ops:
        # 只有 --ids，无操作：抓取基本信息
        source = args.source or config.get("source", "douban")
        top_n = max(id_set)
        print(f"数据源: {source}, 抓取到 ID {top_n}\n")
        if source == "douban":
            movies = scrape_douban(config, top_n, cookie_str=args.cookie)
        else:
            print(f"暂不支持数据源: {source}")
            sys.exit(1)
        movies = [m for m in movies if m["id"] in id_set]
        print(f"\n筛选：保留 {len(movies)} 部指定 ID 的电影")

    else:
        # 无 --top：从 movies.json 加载
        if not os.path.exists(output_path):
            print(f"未找到 {output_path}，请先抓取电影列表。")
            sys.exit(1)
        with open(output_path, "r", encoding="utf-8") as f:
            movies = json.load(f)
        print(f"从 {output_path} 加载了 {len(movies)} 部电影")

    # ── 按 ID 筛选 ──
    if id_set:
        movies = [m for m in movies if m["id"] in id_set]
        print(f"ID 筛选：保留 {len(movies)} 部")

    # ── 操作：抓取播放源 ──
    if args.fetch_streaming:
        print(f"\n开始抓取在线播放信息 ...\n")
        fetch_streaming_info(movies, cookie_str=args.cookie)
        before = len(movies)
        movies = [m for m in movies if m.get("streaming")]
        print(f"过滤：{before} → {len(movies)} 部（仅保留有播放源的）")

    # ── 操作：下载海报 ──
    if args.download_posters:
        posters_dir = os.path.join(SCRIPT_DIR, config["output"]["posters_dir"])
        print(f"\n开始下载海报到 {posters_dir}")
        download_posters(movies, posters_dir, update_url=args.top is not None)

    # ── 保存 ──
    if args.fetch_streaming or args.top or (id_set and not has_ops):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(movies, f, ensure_ascii=False, indent=2)
        print(f"\n已保存 {len(movies)} 部电影到 {output_path}")
        data_js_path = os.path.join(SCRIPT_DIR, config["output"]["data_js"])
        generate_data_js(movies, data_js_path)

    print("\n完成！")


if __name__ == "__main__":
    main()

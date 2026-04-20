#!/bin/bash
# MovieFairy 数据查询脚本
# 从 movies.json 查询电影信息，不跑网络请求
# 用法: bash query.sh <命令> <目标> [平台]

set -e

DATA="/Users/nicky/Documents/movie-fetch/data/movies.json"

if [ ! -f "$DATA" ]; then
  echo "错误: $DATA 不存在"
  exit 1
fi

CMD="${1:-help}"
TARGET="${2:-}"
PLATFORM="${3:-}"

# 通过 python3 查询，支持 ID/精确/模糊匹配
query() {
  local cmd="$1"
  local target="$2"
  local platform="$3"

  python3 -c "
import json, sys

data = json.load(open('$DATA'))

def find_movies(target):
    if not target:
        return []
    # 1. 按 ID 查
    if target.isdigit():
        m = [x for x in data if x.get('id') == int(target)]
        if m: return m
        # ID不存在，提示排名对应的
        n = int(target)
        if n >= 1 and n <= len(data):
            m = data[n-1]
            print(f'ID {target} 不存在，排名第{target}的是: {m[\"title\"]} (ID {m[\"id\"]}, {m.get(\"year\",\"?\")}) ⭐{m.get(\"rating\",\"?\")}')
            return [m]
        print(f'ID {target} 不存在，且排名超出范围（共{len(data)}部）')
        return []
    # 2. 精确匹配
    m = [x for x in data if x.get('title','') == target]
    if m: return m
    # 3. 模糊匹配（标题包含关键词）
    m = [x for x in data if target in x.get('title','')]
    if m: return m
    return []

cmd = '$cmd'
target = '''$target'''
platform = '''$platform'''

movies = find_movies(target)

if not movies:
    print('未找到匹配的电影')
    sys.exit(0)

if len(movies) > 1:
    print(f'模糊匹配到 {len(movies)} 部:')
    for m in movies:
        print(f'  ID {m[\"id\"]}: {m[\"title\"]} ({m.get(\"year\",\"?\")}) ⭐{m.get(\"rating\",\"?\")}')
    print('请指定ID获取详情')
    sys.exit(0)

m = movies[0]
title = m.get('title','')
year = m.get('year','')
rating = m.get('rating','')
cats = ' / '.join(m.get('categories',[]))
synopsis = m.get('synopsis','')
streaming = m.get('streaming', [])

if cmd == 'info':
    print(f'{title} ({year})')
    print(f'评分: ⭐{rating}')
    print(f'分类: {cats}')
    if synopsis:
        print(f'简介: {synopsis}')
    douban = m.get('douban_url','')
    if douban:
        print(f'豆瓣: {douban}')

elif cmd == 'streaming':
    print(f'{title} ({year}) ⭐{rating}')
    if not streaming:
        print('播放源: 无数据')
    elif platform:
        found = [s for s in streaming if platform in s.get('platform','')]
        if found:
            for s in found:
                print(f'  ✅ {s[\"platform\"]} - {s.get(\"type\",\"\")}')
                print(f'     {s.get(\"url\",\"\")}')
        else:
            print(f'播放源（{platform}）: ❌ 无数据')
            plats = ', '.join([s['platform'] for s in streaming])
            print(f'已有平台: {plats}')
    else:
        for s in streaming:
            print(f'  ✅ {s[\"platform\"]} - {s.get(\"type\",\"\")}')
            print(f'     {s.get(\"url\",\"\")}')
        if not streaming:
            print('  ❌ 无播放源数据')

elif cmd == 'poster':
    poster = m.get('poster_url','') or m.get('poster_url_remote','')
    if poster:
        print(f'{title} 海报: {poster}')
    else:
        print(f'{title}: 无海报数据')

elif cmd == 'list':
    pass
" 2>/dev/null
}

list_movies() {
  local n="${1:-10}"
  python3 -c "
import json
data = json.load(open('$DATA'))
n = min(int('$n'), len(data))
print(f'共 {len(data)} 部电影，显示前 {n} 部:')
for m in data[:n]:
    s = ', '.join([x['platform'] for x in m.get('streaming',[])]) if m.get('streaming') else '无'
    print(f'  ID {m[\"id\"]:>3}: {m[\"title\"]} ({m.get(\"year\",\"?\")}) ⭐{m.get(\"rating\",\"?\")} [{s}]')
" 2>/dev/null
}

case "$CMD" in
  info|streaming|poster)
    if [ -z "$TARGET" ]; then
      echo "用法: query.sh $CMD <ID或电影名>"
      exit 1
    fi
    query "$CMD" "$TARGET" "$PLATFORM"
    ;;
  open)
    set +e
    if [ -z "$TARGET" ]; then
      echo "用法: query.sh open <ID或电影名> <平台>"
      exit 1
    fi
    URL=$(python3 -c "
import json, sys
from urllib.parse import unquote
data = json.load(open('$DATA'))
target = '''$TARGET'''
platform = '''$PLATFORM'''

def find_movies(t):
    if t.isdigit():
        m = [x for x in data if x.get('id') == int(t)]
        if m: return m
    m = [x for x in data if x.get('title','') == t]
    if m: return m
    m = [x for x in data if t in x.get('title','')]
    if m: return m
    return []

movies = find_movies(target)
if not movies:
    sys.exit(1)
if len(movies) > 1:
    sys.exit(1)

m = movies[0]
streaming = m.get('streaming', [])
if not streaming:
    sys.exit(1)

if platform:
    found = [s for s in streaming if platform in s.get('platform','')]
else:
    found = streaming

if not found:
    sys.exit(1)

url = found[0].get('url','')
if 'douban.com/link2' in url:
    import re
    m2 = re.search(r'url=([^&]+)', url)
    if m2:
        url = unquote(m2.group(1))
print(url)
")
    RET=$?
    if [ $RET -ne 0 ] || [ -z "$URL" ]; then
      echo "未找到播放源"
      exit 1
    fi
    echo "打开: $URL"
    open "$URL"
    ;;
  list)
    list_movies "$TARGET"
    ;;
  help|*)
    echo "MovieFairy 数据查询"
    echo ""
    echo "用法: query.sh <命令> <目标> [平台]"
    echo ""
    echo "命令:"
    echo "  info <目标>              电影基本信息"
    echo "  streaming <目标>         所有播放源"
    echo "  streaming <目标> <平台>  指定平台播放源"
    echo "  poster <目标>            海报URL"
    echo "  open <目标> [平台]       打开播放页面（默认浏览器）"
    echo "  list [N]                 列出前N部（默认10）"
    echo ""
    echo "目标: ID数字（不存在则自动匹配排名） / 完整电影名 / 部分关键词（模糊匹配）"
    ;;
esac

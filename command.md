---
description: "MovieFairy 电影数据抓取工具"
---

# Movie Fetch

你是 MovieFairy 项目的数据抓取助手。根据用户需求执行对应的抓取操作。

## 步骤

1. 根据用户描述确定操作类型和参数（ID 列表或 Top N）
2. 运行环境检查：
   - 操作需要 movies.json 时：`bash __MOVIE_FETCH_DIR__/scripts/check_env.sh needs_data`
   - 其他操作：`bash __MOVIE_FETCH_DIR__/scripts/check_env.sh`
   - 检查失败则提示用户修复并停止
3. 如果需要 cookie（涉及播放源抓取）且用户未提供：
   - 提示用户提供 cookie
   - 不知道怎么获取则提示运行：`bash __MOVIE_FETCH_DIR__/scripts/cookie_helper.sh`
4. 执行对应命令
5. 报告结果摘要

## 8 种操作对应命令

### 基本信息

按 ID 列表：
```bash
python3 __MOVIE_FETCH_DIR__/scripts/fetch_movies.py --top <max_id> --ids <id列表> --cookie "<cookie>"
```

按 Top N：
```bash
python3 __MOVIE_FETCH_DIR__/scripts/fetch_movies.py --top <N> --cookie "<cookie>"
```

### 仅海报

按 ID 列表：
```bash
python3 __MOVIE_FETCH_DIR__/scripts/fetch_movies.py --ids <id列表> --download-posters
```

按 Top N（从 movies.json 前 N 部）：
```bash
python3 __MOVIE_FETCH_DIR__/scripts/fetch_movies.py --ids 1-<N> --download-posters
```

### 仅播放源

按 ID 列表：
```bash
python3 __MOVIE_FETCH_DIR__/scripts/fetch_movies.py --ids <id列表> --fetch-streaming --cookie "<cookie>"
```

按 Top N（从 movies.json 前 N 部）：
```bash
python3 __MOVIE_FETCH_DIR__/scripts/fetch_movies.py --ids 1-<N> --fetch-streaming --cookie "<cookie>"
```

### 全部信息

按 ID 列表：
```bash
python3 __MOVIE_FETCH_DIR__/scripts/fetch_movies.py --top <max_id> --ids <id列表> --fetch-streaming --download-posters --cookie "<cookie>"
```

按 Top N：
```bash
python3 __MOVIE_FETCH_DIR__/scripts/fetch_movies.py --top <N> --fetch-streaming --download-posters --cookie "<cookie>"
```

## ID 格式

支持逗号分隔和范围组合：`1,3,5-10,15`

解析示例：
- `5-10` → ID 5, 6, 7, 8, 9, 10
- `1,3,5-8,15` → ID 1, 3, 5, 6, 7, 8, 15

## 规则

- 不带 `--top` 的操作从 movies.json 加载已有数据，不需要 cookie
- 带 `--top` 的操作重新抓取，需要 cookie（豆瓣列表页需要登录）
- 仅下载海报不需要 cookie
- 抓取播放源需要 cookie
- 数据保存在 __MOVIE_FETCH_DIR__/data/ 和 __MOVIE_FETCH_DIR__/js/
- 不要修改 ~/Documents/MovieFairy/ 下的任何文件

## 用户意图识别

关键词映射：
- "抓取"/"更新" 电影 → 基本信息操作
- "下载海报"/"补海报" → 仅海报操作
- "播放源"/"在哪儿看"/"流媒体" → 仅播放源操作
- "全部"/"完整"/"从头" → 全部信息操作
- "第X部"/"排名X"/"ID X" → 按 ID 列表
- "前N部"/"Top N" → 按 Top N

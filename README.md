# Movie Fetch

个人skill备份：豆瓣电影数据抓取工具，以 Claude Code Skill 形式运行。

## 功能

- 查询电影信息、播放源、海报（本地数据，无需网络）
- 直接打开播放页面到默认浏览器
- 抓取豆瓣 Top250 电影基本信息
- 抓取在线播放源（需 cookie）
- 下载电影海报
- 支持按排名 ID 或 Top N 筛选
- ID 不存在时自动匹配排名对应的影片

## 安装

```bash
git clone https://github.com/你的用户名/movie-fetch.git
cd movie-fetch
./install.sh
```

安装后在 Claude Code 中输入 `/movie-fetch` 即可使用。

## 更新

```bash
cd movie-fetch
git pull
./install.sh
```

## 卸载

```bash
./uninstall.sh
```

## 数据查询（无需网络）

```bash
# 基本信息
bash scripts/query.sh info <ID或电影名>

# 播放源
bash scripts/query.sh streaming <ID或电影名> [平台]

# 打开播放页面
bash scripts/query.sh open <ID或电影名> [平台]

# 海报
bash scripts/query.sh poster <ID或电影名>

# 列表
bash scripts/query.sh list [N]
```

支持 ID 数字、完整电影名、部分关键词（模糊匹配）。ID 不存在时自动提示排名对应的影片。

## 8 种抓取操作

| | 按 ID 列表 | 按 Top N |
|---|---|---|
| 基本信息 | `--top <max> --ids 1,3,5` | `--top 50` |
| 仅海报 | `--ids 1,3,5 --download-posters` | `--ids 1-50 --download-posters` |
| 仅播放源 | `--ids 1,3,5 --fetch-streaming` | `--fetch-streaming` |
| 全部信息 | `--top <max> --ids 1,3,5 --fetch-streaming --download-posters` | `--top 50 --fetch-streaming --download-posters` |

## Cookie 获取

抓取播放源需要豆瓣 cookie：

```bash
bash scripts/cookie_helper.sh
```

## 目录结构

```
movie-fetch/
├── command.md          # Skill 定义（路径占位符）
├── install.sh          # 安装脚本
├── uninstall.sh        # 卸载脚本
├── scripts/
│   ├── query.sh        # 数据查询（info/streaming/open/poster/list）
│   ├── fetch_movies.py # 主抓取脚本
│   ├── check_env.sh    # 环境检查
│   ├── cookie_helper.sh# Cookie 获取指引
│   ├── config.yaml     # 配置
│   └── requirements.txt
├── data/               # 生成数据（gitignore）
└── js/                 # 生成数据（gitignore）
```

# Movie Fetch

个人skill备份：豆瓣电影数据抓取工具，以 Claude Code Skill 形式运行。

## 功能

- 抓取豆瓣 Top250 电影基本信息
- 抓取在线播放源（需 cookie）
- 下载电影海报
- 支持按排名 ID 或 Top N 筛选

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

## 8 种操作

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
│   ├── fetch_movies.py # 主脚本
│   ├── check_env.sh    # 环境检查
│   ├── cookie_helper.sh# Cookie 获取指引
│   ├── config.yaml     # 配置
│   └── requirements.txt
├── data/               # 生成数据（gitignore）
└── js/                 # 生成数据（gitignore）
```

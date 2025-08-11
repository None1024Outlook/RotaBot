# RotaBot (Open Source Version) / RotaBot (开放源码版)

## 中文说明

### 项目描述
RotaBot 是一个非官方的 Rotaeno 相关 Discord 机器人。此项目为开放源码版本，与 Rotaeno 开发组（Dream Engine Games）和心动网络没有任何关联。

### 注意事项
- 本项目不会经常更新，仅在有重大更新或开发者有时间时维护
- 任何人都可以自由下载、修改与分发源代码

### 使用指南

#### 准备工作
1. 准备 Discord Bot 的 Token
2. 下载 Rotaeno 游戏资源文件

#### 安装步骤
1. 更新数据库文件：
   - `song_alias.db` (存储歌曲别名及其对应ID)
   - `song_data.db` (存储歌曲数据)
   
2. 添加图片资源：
   将 Rotaeno 图片资源放入 `rotaeno/assets/img/` 目录下，目录结构如下：
   ```
   .
   ├─avatar (头像)
   ├─background (背景)
   ├─character (角色立绘)
   ├─rank (歌曲评级图片)
   ├─source (歌曲曲绘原文件)
   └─thumb (歌曲曲绘缩略图)
   ```
   *注：所有文件应为 PNG 格式*

3. 配置机器人：
   修改 `bot.py` 文件中的 `DISCORD_BOT_TOKEN` 为你的 Discord Bot Token

#### 运行机器人
```bash
python bot.py
```
*注意：可能需要先安装必要的Python库*

---

## English Description

### Project Overview
RotaBot is an unofficial Discord bot related to Rotaeno. This is the open-source version and is not affiliated with Rotaeno development team (Dream Engine Games) or XD Network.

### Important Notes
- This project is not regularly updated, maintenance only occurs for major updates or when developers have time
- Anyone is free to download, modify and distribute the source code

### Usage Guide

#### Prerequisites
1. Prepare a Discord Bot Token
2. Download Rotaeno game resource files

#### Installation Steps
1. Update database files:
   - `song_alias.db` (stores song aliases and their corresponding IDs)
   - `song_data.db` (stores song data)
   
2. Add image resources:
   Place Rotaeno image resources in `rotaeno/assets/img/` with the following structure:
   ```
   .
   ├─avatar (avatars)
   ├─background (backgrounds)
   ├─character (character illustrations)
   ├─rank (song rating images)
   ├─source (original song cover files)
   └─thumb (song cover thumbnails)
   ```
   *Note: All files should be in PNG format*

3. Configure the bot:
   Modify `DISCORD_BOT_TOKEN` in `bot.py` with your Discord Bot Token

#### Running the Bot
```bash
python bot.py
```
*Note: You may need to install required Python libraries first*

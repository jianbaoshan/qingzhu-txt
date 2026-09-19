# 青竹txt书籍下载

书籍 TXT 批量下载器（Windows 桌面 App，Python + PyQt6）。支持**书名搜索**与**任意网页链接下载全书**两种模式，一键导出 UTF-8 纯文本，用于本地阅读与 AI 有声书制作（ebook2audiobook / EmotiVoice 等）。

> ⚠️ **重要免责声明**：本工具仅用于抓取你拥有合法授权、公有领域、作者开放免费转载的书籍文本。未经版权方许可，私自抓取受版权保护的网络小说、出版物文本用于下载、二次制作、发布（抖音等平台）属于侵权行为，由此产生全部法律责任由使用者自行承担。请严格遵守网站 robots 协议与著作权法。

## 功能特性

<!-- AUTO:features -->

- **模式一 · 书名搜索**：输入书名，勾选数据源，跨站检索；结果表格多选，一键下载全书 TXT
- **模式二 · 链接下载（任意网页）**：粘贴书籍目录链接，自动识别站点、解析全部章节（含目录分页、正文分页、镜像域名、重复章节恢复），批量导出全书
- **文本清洗**：剔除网页标签/脚注/页眉页脚/多余空行，强制 UTF-8，结果可直接喂给 TTS
- **可选分章节导出**：按章节拆分为独立 txt，适配 ebook2audiobook / EmotiVoice 等分批合成
- **反爬/健壮性**：UA 随机伪装、请求间隔、单章重试、失败自动跳过不崩溃；目录解析过程实时打印进度
- **实时进度**：进度条 + 带时间戳日志窗口

<!-- /AUTO:features -->

## 环境要求

- Windows 10 / 11 64 位
- Python 3.9+（需 PyQt6 环境）
- 使用「识典古籍」数据源时需 Node.js（其页面需逆向签名，脚本见 `core/*.js`，非本项目运行时依赖）

## 安装与运行

```bash
pip install -r requirements.txt
python app.py
```

依赖清单见 [requirements.txt](requirements.txt)：PyQt6 / requests / beautifulsoup4。

## 使用说明

启动后先阅读并确认免责声明，然后进入主界面：

1. **顶部**勾选数据源（可多选）
2. **Tab1 按书名搜索下载**
   - 输入书名（例：三国演义）→ 点击【开始搜索】
   - 在结果表格勾选书籍 → 点击【下载选中书籍】
3. **Tab2 根据网页链接下载全书**
   - 粘贴书籍目录页链接（支持任意小说网站）→ 点击【解析目录】
   - 查看日志确认章节总数后点击【开始下载全书 TXT】
4. **下载设置**：输出目录（默认 `D:\书籍TXT下载\`）、自动清洗、分章节导出
5. 底部日志实时显示解析/下载进度，完成后点击【打开输出文件夹】

### 输出示例

```
D:\书籍TXT下载\
├─三国演义_维基文库.txt
└─三国演义_维基文库_分章节\
   ├─第001回.txt
   ├─第002回.txt
   └─……
```

## 项目结构

<!-- AUTO:project_tree -->

本站点仅列举应用自身模块；其余数据源逆向脚本（core/*.js）与调试文件不分发。

```
qingzhu-txt\
    ├─ app.py                   # 青竹txt书籍下载 - 书籍 TXT 批量下载器
    ├─ core\downloader.py       # 下载调度逻辑：解析目录 → 逐章抓取 → 清洗合并 → 保存文件。
    ├─ core\file_manager.py     # 本地文件管理：安全文件名、UTF-8 保存、分章导出。
    ├─ core\http_client.py      # HTTP 请求封装：UA 伪装、请求间隔、重试、超时处理。
    ├─ core\models.py           # 数据模型与自定义异常。
    ├─ core\text_cleaner.py     # 通用文本清洗引擎：剔除网页残留、压缩空行、去除页眉页脚。
    ├─ adapters\base.py         # 站点适配器基类与统一接口。
    ├─ adapters\ctext.py        # CTEXT 中国哲学书电子化计划适配器（ctext.org/zh）。
    ├─ adapters\generic.py      # 通用启发式适配器：针对未内置的任意小说网站。
    ├─ adapters\shidianguji.py  # 识典古籍适配器（www.shidianguji.com）—— 基于服务端渲染（SSR）数据解析。
    ├─ adapters\wikisource.py   # 维基文库适配器（zh.wikisource.org）。
    ├─ ui\disclaimer.py         # 启动免责声明弹窗。
    └─ ui\main_window.py        # 主窗口：搜索 / URL 下载两个模式 + 下载设置 + 日志进度。
```

<!-- /AUTO:project_tree -->

## 数据源与适配器

通用适配器（`generic.py`）会自动识别「任意网页」的目录/正文结构，支持目录分页、正文分页、镜像域名章节、重复/残缺目录恢复等站点特性。

<!-- AUTO:adapters -->

| 数据源 | 适配器 | 支持站点 |
| --- | --- | --- |
| **维基文库** | wikisource.py | zh.wikisource.org 公有领域古籍 |
| **识典古籍** | shidianguji.py | shidianguji.com 古籍（需 Node 环境逆向签名） |
| **CTEXT** | ctext.py | ctext.org/zh 中文古籍库 |
| **任意网页** | generic.py | 启发式适配任意小说网站，支持任意目录链接解析全书 |

<!-- /AUTO:adapters -->

## README 自动维护

`README.md` 的项目结构 / 数据源 / 功能特性区段由 `tools/update_readme.py` 从代码自动生成（描述取自各模块 docstring 首行）。仓库已配置 [`.githooks/pre-commit`](.githooks/pre-commit)，每次 `git commit` 前会自动重跑脚本并纳入提交，因此改动代码后无需手动维护这些区段。

若在其它机器克隆后想启用该钩子，只需执行一次：

```bash
git config core.hooksPath .githooks
```

## 已知限制

- **CTEXT**：站点对程序化请求启用了 Cloudflare 人机验证，程序会自动提示【网站访问受限，请稍后重试】，可稍后再试或改用浏览器阅读。
- **识典古籍**：书籍主页 `/book/{id}` 不输出服务端目录数据，URL 模式下请粘贴**任意章节链接**（程序会自动还原全书目录）；搜索模式不受影响。
- **任意网页**：依赖站点结构启发式识别，遇到结构特殊或校验严格的站点可能解析失败；抓取结果忠实反映站点目录原样，站点自身的数据损坏（乱码标题、重复编号等）不会也无法修正。

## 打包为独立 exe（可选）

```bash
pip install pyinstaller
pyinstaller -F -w -i 图标.ico app.py --name 青竹txt书籍下载
```

打包后 `dist\青竹txt书籍下载.exe` 可直接双击运行，用户无需安装 Python。

## 免责声明

本软件仅用于抓取公有领域、作者授权开放的书籍文本，仅供个人学习研究。禁止未经版权方许可抓取受版权保护作品；禁止将侵权抓取的文本用于二次创作、抖音等平台发布。用户使用本工具产生的一切法律责任由使用者自行承担。
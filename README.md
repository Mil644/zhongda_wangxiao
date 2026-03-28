以下是根据你提供的代码编写的 README.md 文件，详细说明了项目的目的、结构、安装与运行方法，以及注意事项。

```markdown
# 王啸题库爬虫

本项目是一个基于 Scrapy 的爬虫，用于抓取 [王啸题库](https://ks.wangxiao.cn/) 中的题目，并将其保存为本地 Markdown 文件。爬虫会按照课程分类、章节结构组织题目，并下载题目中的图片，替换为本地路径。

## 功能特点

- 模拟登录，使用浏览器 Cookies 保持会话
- 按照一级、二级、三级分类及章节结构递归抓取知识点
- 支持普通题组和材料题两种题型
- 将题目内容格式化为 Markdown 文件，便于阅读和整理
- 自动下载题目中的图片，并替换链接为本地相对路径

## 项目结构

```
wangxiao/
├── wangxiao/
│   ├── spiders/
│   │   └── questions.py      # 爬虫主逻辑
│   ├── pipelines.py          # 数据处理管道（文件写入、图片下载）
│   ├── items.py              # （可选）Item 定义，本例未使用
│   ├── settings.py           # Scrapy 配置文件
│   └── ...
├── scrapy.cfg
└── README.md
```

## 环境要求

- Python 3.6+
- Scrapy 2.5+
- lxml

## 安装与配置

### 1. 安装依赖

```bash
pip install scrapy lxml
```

### 2. 克隆或下载项目

将本仓库克隆到本地，或直接下载代码文件。

### 3. 配置 Cookies

爬虫在 `questions.py` 的 `start` 方法中使用了硬编码的 Cookies。由于 Cookies 具有时效性，在使用前需要更新为最新的登录状态。

- 打开浏览器，登录 [王啸题库](https://ks.wangxiao.cn/)
- 打开开发者工具（F12），进入“网络”标签
- 刷新页面，找到任意请求（如首页），复制请求头中的 `Cookie` 字段
- 将 `questions.py` 中 `cookies` 字典的内容替换为新的 Cookies

### 4. 修改起始 URL（可选）

爬虫的起始 URL 为 `https://ks.wangxiao.cn/`，如需抓取其他分类或页面，可调整 `start_urls` 和解析逻辑。

## 使用方法

### 运行爬虫

在项目根目录下执行：

```bash
scrapy crawl questions
```

### 输出结果

爬虫运行后，会在当前目录下生成以课程分类、章节命名的文件夹，每个知识点生成一个 `.md` 文件。例如：

```
一级分类/二级分类/三级分类/知识点名称.md
```

图片会被下载到每个 `.md` 文件同级的 `images` 文件夹中，Markdown 中的图片链接会被替换为 `./images/图片名` 的相对路径。

## 代码说明

### `questions.py` – 爬虫主逻辑

- **`start()`**  
  使用自定义方法发送带 Cookies 的初始请求。

- **`parse()`**  
  解析首页，提取一级分类和二级分类链接。

- **`parse_second()`**  
  解析二级分类页面，获取三级分类链接。

- **`parse_sub()`**  
  解析知识点列表页，提取章节结构，并根据是否有子知识点构造请求获取题目数据。

- **`parse_questions()`**  
  解析题目接口返回的 JSON，提取题目内容、选项、答案、解析，并格式化为 Markdown 文本，最后通过 Item 传递给管道。

### `pipelines.py` – 数据处理管道

- **`WangxiaoPipeline`**  
  将 Item 中的文件内容和路径写入本地文件，自动创建目录。

- **`WangxiaoImagesPipeline`**  
  继承自 Scrapy 的 `ImagesPipeline`，用于下载图片并替换 Markdown 中的图片链接为本地路径。

## 注意事项

1. **Cookies 有效性**  
   爬虫依赖 Cookies 维持登录状态，若 Cookies 过期，请及时更新。

2. **请求频率控制**  
   为避免对目标网站造成过大压力，可在 `settings.py` 中配置下载延迟（`DOWNLOAD_DELAY`）。

3. **仅处理第一个子分类**  
   当前代码在 `parse` 和 `parse_second` 中使用了 `break`，只处理第一个二级分类和第一个三级分类。如需抓取全部，请移除这些 `break`。

4. **硬编码 URL**  
   部分请求的 URL 是硬编码的（如 `https://ks.wangxiao.cn/TestPaper/list?sign=cfe1&paperType=1`），可能与实际页面不符。请根据实际页面结构调整。

5. **图片下载**  
   `WangxiaoImagesPipeline` 需要启用 `IMAGES_STORE` 设置，并在 `settings.py` 中配置 `ITEM_PIPELINES`，例如：

   ```python
   ITEM_PIPELINES = {
       'wangxiao.pipelines.WangxiaoPipeline': 300,
       'wangxiao.pipelines.WangxiaoImagesPipeline': 400,
   }
   IMAGES_STORE = 'images'
   ```

## 常见问题

### Q: 运行后没有生成任何文件？

- 检查 Cookies 是否有效，是否成功登录。
- 查看控制台输出，确认请求是否返回正常（状态码 200）。
- 检查 XPath 表达式是否与当前页面结构匹配。

### Q: 图片无法下载？

- 确认 `IMAGES_STORE` 设置正确。
- 检查图片 URL 是否可访问。
- 查看 `WangxiaoImagesPipeline` 的 `get_media_requests` 方法是否正确提取了图片链接。

### Q: 如何抓取全部分类？

- 移除 `parse` 和 `parse_second` 中的 `break` 语句，让循环完整执行。

## 许可证

本项目仅供学习交流使用，请勿用于商业或非法用途。使用前请遵守目标网站的 `robots.txt` 及相关法律法规。

## 贡献

欢迎提交 Issue 或 Pull Request 来改进代码。
```

此 README 包含了项目介绍、结构、安装运行指南、代码说明和注意事项，能够帮助用户快速理解和使用该爬虫。

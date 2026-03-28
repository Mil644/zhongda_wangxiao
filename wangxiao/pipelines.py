# Define your item pipelines here
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
import scrapy
from lxml import etree
import os

class WangxiaoPipeline:
    """
    普通管道：用于将爬虫返回的题目内容写入本地 Markdown 文件
    """
    def process_item(self, item):
        # 从 item 中获取文件路径和内容
        path_dirs = item['path_dirs']
        file_content = item['file_content']
        # 提取目录部分（不包含文件名），如果不存在则创建
        dir = '/'.join(path_dirs.split('/')[0:-1])
        if not os.path.exists(dir):
            os.makedirs(dir)
        # 以追加模式写入文件（如果文件已存在则追加）
        with open(item['path_dirs'], 'a', encoding='utf-8') as f:
            f.write(item['file_content'])
        return item

class WangxiaoImagesPipeline(ImagesPipeline):
    """
    图片管道：用于下载题目中的图片，并替换 markdown 中的图片链接为本地路径
    """
    def file_path(self, request, response=None, info=None, item=None):
        """
        定义图片下载后的存储路径
        """
        file_name = request.meta['file_name']          # 从 meta 中获取文件名
        file_content = request.meta['file_content']    # 题目内容（未使用）
        path_dirs = request.meta['path_dirs']          # 原文件路径
        # 在原文件所在目录下创建 images 文件夹
        path = '/'.join(path_dirs.split('/')[0:-1])
        path = path + '/' + 'images'
        if not os.path.exists(path):
            os.makedirs(path)
        # 返回存储路径 + 文件名
        return (path + '/' + file_name)

    def item_completed(self, results, item, info):
        """
        当图片下载完成后，替换 item 中 file_content 的图片 URL 为本地路径
        """
        if results:
            for status, local in results:
                url = local['url']                     # 原图片 URL
                path = local['path']                   # 下载后的本地路径
                # 构造相对路径（相对于 md 文件的 images 文件夹）
                local_path = f'./{'/'.join(path.split("/")[-2:])}'
                # 替换原内容中的 URL 为本地路径，并移除 HTML 标签 <br />
                item['file_content'] = item['file_content'].replace(url, local_path).replace("<br />", "")
        return item

    def get_media_requests(self, item, info):
        """
        从 item 的 file_content 中提取所有图片 URL，并为每个图片生成下载请求
        """
        path_dirs = item['path_dirs']
        file_content = item['file_content']
        # 使用 lxml 解析 HTML 内容，提取所有 img 标签的 src 属性
        herfs = etree.HTML(item['file_content']).xpath('//img/@src')
        for href in herfs:
            file_name = href.split('/')[-1]            # 从 URL 中提取文件名
            # 生成下载请求，并将文件名等信息通过 meta 传递
            yield scrapy.Request(href, meta={'file_name': file_name, 'file_content': file_content, 'path_dirs': path_dirs})
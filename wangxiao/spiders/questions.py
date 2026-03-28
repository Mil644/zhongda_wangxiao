import scrapy
import json

class QuestionsSpider(scrapy.Spider):
    name = "questions"
    allowed_domains = ["ks.wangxiao.cn", 'mtiku.wangxiao.cn', 'img.wangxiao.cn']
    start_urls = ["https://ks.wangxiao.cn/"]

    # 自定义的 start 方法，用于在爬虫启动时发送带 cookies 的初始请求
    async def start(self):
        # 模拟登录所需的 cookies
        cookies = {'cookie_name': 'cookie_value'}
        # 发送带 cookies 的请求，指定回调函数为 parse
        yield scrapy.Request(url=self.start_urls[0], cookies=cookies)

    def parse(self, response):
        """
        解析首页，获取一级分类和二级分类链接
        """
        # 定位一级分类的 li 标签
        main_tags = response.xpath('//ul[@class="first-title"]/li')
        for li in main_tags:
            # 获取一级分类标题
            first_title = li.xpath('./p/span/text()').get()
            # 获取该分类下的二级分类链接
            second_tags = li.xpath('./div[@class="send-title"]/a')
            for a in second_tags:
                second_title = a.xpath('./text()').get()
                second_href = a.xpath('./@href').get()
                second_href = response.urljoin(second_href)
                # 将 URL 中的 'TestPaper' 替换为 'exampoint'，调整到知识点列表页
                second_href = second_href.replace('TestPaper', 'exampoint')
                # 发送请求，注意这里硬编码了一个固定 URL用于测试；实际应该使用 second_href
                # 原代码只处理了第一个二级分类（因为 break），可能是调试用途
                yield scrapy.Request(url='https://ks.wangxiao.cn/TestPaper/list?sign=cfe1&paperType=1',
                                     callback=self.parse_second,
                                     meta={'first_title': first_title, 'second_title': second_title})
                break  # 只处理第一个二级分类

    def parse_second(self, response):
        """
        解析二级分类页面，获取三级分类（子分类）链接
        """
        first_title = response.meta['first_title']
        second_title = response.meta['second_title']
        # 定位筛选区域中的子分类链接
        sub_tags = response.xpath('//div[@class="filter-content"]/div[@class="filter-item"]/a')
        for a in sub_tags:
            sub_title = a.xpath('./text()').get()
            sub_href = a.xpath('./@href').get()
            sub_href = response.urljoin(sub_href)
            # 发送请求到知识点列表页，同样硬编码了固定 URL
            yield scrapy.Request(url='https://ks.wangxiao.cn/exampoint/list?sign=cfe1',
                                 callback=self.parse_sub,
                                 meta={'first_title': first_title, 'second_title': second_title, 'sub_title': sub_title})
            break  # 只处理第一个子分类

    def parse_sub(self, response):
        """
        解析知识点列表页，提取每个章节和知识点的信息，并构造 POST 请求获取题目
        """
        first_title = response.meta['first_title']
        second_title = response.meta['second_title']
        sub_title = response.meta['sub_title']
        # 获取所有章节项
        chapter_tags = response.xpath('//ul[@class="chapter-item"]')
        for cti in chapter_tags:
            # 检查是否存在更细的知识点（section-point-item）
            point_tags = cti.xpath('.//ul[@class="section-point-item"]')
            if point_tags:
                # 存在知识点，遍历每个知识点
                for spi in point_tags:
                    # 构建路径：一级/二级/三级/...（根据祖先标题拼接）
                    path_dir = [first_title, second_title, sub_title]
                    # 获取知识点标题
                    point = spi.xpath('./li[1]//text()').getall()
                    point = ''.join(point).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '')
                    # 向上查找所有章节/小节标题
                    titles = spi.xpath('./ancestor::ul[@class="section-item" or @class="chapter-item"]')
                    for ti in titles:
                        title = ti.xpath('./li[1]//text()').getall()
                        for t in title:
                            title = t.replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('\\', '').replace('/', '')
                            if title != '':
                                path_dir.append(title)
                    # 拼接完整路径（用于保存文件目录）
                    path = '/'.join(path_dir)
                    # 获取请求题目所需的 sign 和 subsign 参数（从 data-* 属性中提取）
                    sign = spi.xpath('./li[3]/span/@data_sign').get()
                    subsign = spi.xpath('./li[3]/span/@data_subsign').get()
                    # 构造 POST 请求体，请求获取该知识点下的题目列表（最多100条）
                    data = {
                        "practiceType": "2",
                        "sign": sign,
                        "subsign": subsign,
                        "examPointType": "",
                        "questionType": "",
                        "top": "100"
                    }
                    yield scrapy.Request(url="https://ks.wangxiao.cn/practice/listQuestions",
                                         callback=self.parse_questions,
                                         method="POST",
                                         body=json.dumps(data),
                                         meta={'path': path, 'title': point})
            else:
                # 没有更细的知识点，则当前章节本身就是最小单位
                path_dir = [first_title, second_title, sub_title]
                title = cti.xpath('./li[1]//text()').getall()
                title = ''.join(title).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '')
                path_dir.append(title)
                path = '/'.join(path_dir)
                sign = cti.xpath('./li[3]/span/@data_sign').get()
                subsign = cti.xpath('./li[3]/span/@data_subsign').get()
                data = {
                    "practiceType": "2",
                    "sign": sign,
                    "subsign": subsign,
                    "examPointType": "",
                    "questionType": "",
                    "top": "100"
                }
                yield scrapy.Request(url="https://ks.wangxiao.cn/practice/listQuestions",
                                     callback=self.parse_questions,
                                     method="POST",
                                     body=json.dumps(data),
                                     meta={'path': path, 'title': title})

    def parse_questions(self, response):
        """
        解析题目接口返回的 JSON 数据，提取题目信息并格式化为 Markdown 内容
        """
        file_content = []  # 存储最终要写入文件的全部内容
        q_json = json.loads(response.text)
        path = response.meta['path']
        title = response.meta['title']

        # 遍历每个题目块（可能包含多个小题或材料题）
        for dic in q_json['Data']:
            materials = dic['materials']
            # 如果没有材料题，则为普通题组
            if not materials:
                questions_content = []
                q_title = dic['paperRule']['title']  # 题组标题
                # 遍历组内每个小题
                for i in range(len(dic['questions'])):
                    q = dic['questions'][i]
                    q_content = q['content']          # 题干内容
                    textAnalysis = q['textAnalysis']  # 解析（答案+解析）
                    q_num = i + 1
                    choice_content = []
                    true_answer = []
                    # 处理选项
                    for c in q['options']:
                        q_choice_name = c['name']     # 选项字母（A,B,C...）
                        q_choice = c['content']       # 选项文字
                        if_right = c['isRight']       # 是否正确答案
                        choice_content.append(q_choice_name + '.' + q_choice + '\n')
                        if if_right:
                            true_answer.append(q_choice_name)
                    choice_content = ''.join(choice_content)
                    # 组合一道题的完整内容
                    questions_info = f'{q_num}.{q_content}\n{choice_content}{true_answer}\n{textAnalysis}\n'
                    questions_content.append(questions_info)
                all_content = ''.join(questions_content)
                contents = f'{q_title}\n{all_content}'
                file_content.append(contents)
            else:
                # 材料题：先处理材料，再处理材料下的多个小题
                q_title = dic['paperRule']['title']
                all_content = []
                for i in range(len(dic['materials'])):
                    materials = dic['materials'][i]
                    material = materials['material']
                    q_content = material['content']    # 材料内容
                    questions_infos = [q_content]
                    q_num = i + 1
                    # 处理该材料下的每个小题
                    for j in range(len(materials['questions'])):
                        q_q = materials['questions'][j]
                        q_q_num = j + 1
                        q_q_content = q_q['content']
                        choice_content = []
                        true_answer = []
                        textAnalysis = q_q['textAnalysis']
                        for c in q_q['options']:
                            q_choice_name = c['name']
                            q_choice = c['content']
                            if_right = c['isRight']
                            choice_content.append(q_choice_name + '.' + q_choice + '\n')
                            if if_right:
                                true_answer.append(q_choice_name)
                        choice_content = ''.join(choice_content)
                        questions_info = f'{q_num}-{q_q_num}.{q_q_content}\n{choice_content}{true_answer}\n{textAnalysis}\n'
                        questions_infos.append(questions_info)
                    questions_infos = ''.join(questions_infos)
                    all_content.append(questions_infos)
                all_content = ''.join(all_content)
                contents = f'{q_title}\n{all_content}'
                file_content.append(contents)

        # 构建完整文件路径和内容
        path_dirs = f'{path}/{title}.md'
        contents = '\n'.join(file_content)

        # 将数据通过 item 传递给 pipeline 处理
        yield {
            'path_dirs': path_dirs,
            'file_content': contents
        }
#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2018/2/12 15:06
# @Author  : CKHo
# @Email   : ckhoidea@hotmail.com
# @File    : UniversalMethod.py
# @Software: PyCharm

from retrying import retry
from QcloudApi.qcloudapi import QcloudApi
from aip import AipNlp
from bosonnlp import BosonNLP
from concurrent.futures import ThreadPoolExecutor
from .DailySentiment import get_today_news_urls, get_content
from functools import reduce
from time import time
import tushare
import json
import datetime


def count_time(func):
    def wrapper(*args):
        start = time()
        r = func(*args)
        end = time()
        print('cost: ', end-start)
        return r
    return wrapper


class RequireError(BaseException):
    pass


class DualThrust(object):
    def __init__(self, code, today, open, n, k1, k2):
        """
        初始化DualThrust类,关于DualThrust，参考：https://www.joinquant.com/post/274

        :param code: 股票代码
        :param today: 字符串格式日期，比如：'2018-02-12'
        :param open: 开盘价，float类型
        :param n: N日
        :param k1: k1，计算前可调整
        :param k2: k2, 计算前可调整
        """
        self.code = code
        self.today = today
        self.open = open
        self.n = n
        self.k1 = k1
        self.k2 = k2
        #  self.what_date_today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.n_day_history_data = get_n_day_history(self.code, self.today, n=n)

    def buyline(self):
        """
        根据当前数据返回买点

        :return:
        """
        HH = max(self.n_day_history_data['high'].values)
        LC = min(self.n_day_history_data['close'].values)
        HC = max(self.n_day_history_data['close'].values)
        LL = min(self.n_day_history_data['low'].values)
        Range = max(HH-LC, HC-LL)
        return round(float(self.open + self.k1 * Range), 2)

    def sellline(self):
        """
        根据当前数据返回卖点

        :return:
        """
        HH = max(self.n_day_history_data['high'].values)
        LC = min(self.n_day_history_data['close'].values)
        HC = max(self.n_day_history_data['close'].values)
        LL = min(self.n_day_history_data['low'].values)
        Range = max(HH - LC, HC - LL)
        return round(float(self.open + self.k2 * Range), 2)

# w = Wenzhi('AKIDA9tOddCwEI7g05OUpukKfkbCYgYBpiZA','SeZEckcDeqnWzDCvmgMnzvc4IH0UjjTy','gz','POST')


class Wenzhi(object):
    def __init__(self, secret_id, secret_key, region, method):
        """
        调用腾讯文智API处理文本的初始化

        :param secret_id: 自己的secretID
        :param secret_key: 自己的secretKey
        :param region: 区域
        :param method: 一般是POST
        """
        self.module = 'wenzhi'
        self.config = {'secretId': secret_id,
                       'secretKey': secret_key,
                       'Region': region,
                       'method': method}
        self.service = QcloudApi(self.module, self.config)

    def text_classify(self, content):
        """
        文本分类API，参考：http://nlp.qq.com/help.cgi#

        :param content: 格式参考文本分类API的文档
            字段	     类型	 说明
            title	 string	 文章标题（选填），编码格式utf8
            content	 string	 正文内容，编码格式utf8( 必填)
            secd_nav string	 二级导航（选填），编码格式utf8
            url	     string	 文章对应的url（选填）
        :return: dict
        """
        action = 'TextClassify'

        # Key check
        keys = content.keys()
        if 'content' not in keys:
            raise KeyError("No param:content")

        result = self.service.call(action, content)
        return json.loads(result)

    def lexical_analysis(self, content):
        """
        分词与命名实体API，参考：http://nlp.qq.com/help.cgi#

        :param content: 格式参考分词与命名实体API的文档，不过content不需要提供code，将使用默认值
            字段	    类型	    说明
            text	string	待词法分析的文本
            code	int	text的编码(0x00200000== utf-8) 目前文智统一输入为utf-8，实际使用中本参数值为：2097152
            type	int	（可选参数，默认为0）
                    0为基础粒度版分词，倾向于将句子切分的更细，在搜索场景使用为佳。
                    1为混合粒度版分词，倾向于保留更多基本短语不被切分开。
        :return: dict
        """
        action = 'LexicalAnalysis'

        # Key check
        keys = content.keys()
        if 'text' not in keys:
            raise KeyError("No param:text")
        if 'code' in keys:
            raise KeyError("No param:code need")

        content['code'] = 2097152
        result = self.service.call(action, content)
        return json.loads(result)

    def text_sentiment(self, content):
        """
        情感分析API，参考：http://nlp.qq.com/help.cgi#

        :param content: 格式参考情感分析API的文档
            字段	    类型	    说明
            content	string	待分析的文本（只能为utf8编码）
            type	int	    （可选参数，默认为4）
                            1：电商；2：APP；3：美食；4：酒店和其他。
        :return: dict
        """
        action = 'TextSentiment'

        # Key check
        keys = content.keys()
        if 'content' not in keys:
            raise KeyError("No param:content in content")

        result = self.service.call(action, content)
        return json.loads(result)

    def text_keywords(self, content):
        """
        关键词提取API，参考：http://nlp.qq.com/help.cgi#

        :param content: 格式参考关键词提取API的文档
            字段	    类型	    说明
            title	string	新闻标题(必填)
            channel	string	新闻频道(选填 不填默认是科技)
                            CHnews_news_sports	体育新闻
                            CHnews_news_ent	娱乐新闻
                            CHnews_news_astro	星座新闻
                            CHnews_news_auto	汽车新闻
                            CHnews_news_cul	文化新闻
                            CHnews_news_digi	数码新闻
                            CHnews_news_finance	财经新闻
                            CHnews_news_game	游戏新闻
                            CHnews_news_house	房产新闻
                            CHnews_news_lad	时尚新闻
                            CHnews_news_mil	军事新闻
                            CHnews_news_ssh	社会新闻
                            CHnews_news_tech	科技新闻
                            CHnews_news_others	其它
            content	string	新闻正文(必填)
        :return: dict
        """
        action = 'TextKeywords'

        # Key check
        keys = content.keys()
        if 'title' not in keys:
            raise KeyError("No param:title")
        if 'content' not in keys:
            raise KeyError("No param:content in content")

        result = self.service.call(action, content)
        return json.loads(result)

    def text_dependency(self, content):
        """
        句法分析API，参考：http://nlp.qq.com/help.cgi#

        :param content: 格式参考句法分析API文档
            字段	    类型	    说明
            content	string	待分析的文本（只能为utf8编码）
        :return: dict
        """
        action = 'TextDependency'

        # Key check
        keys = content.keys()
        if 'content' not in keys:
            raise KeyError("No param:content in content")

        result = self.service.call(action, content)
        return json.loads(result)


def the_date_n_day_before(n, end):
    """
    自动计算指定日期的N天前的日期

    :param n: n天
    :param end: 指定的日期,格式为:'2018-02-12'
    :return: string,格式为date的输入
    """
    # type check
    if n < 0:
        raise RequireError("param:n should be positive number")
    if isinstance(end, str):
        pass
    else:
        raise RequireError("param:date should be string")

    date_from_str_to_datetime = datetime.datetime.strptime(end, '%Y-%m-%d')
    n_days_ago = date_from_str_to_datetime - datetime.timedelta(n)
    return n_days_ago.strftime('%Y-%m-%d')


@retry(stop_max_attempt_number=5)
def get_n_day_history(code, end, n=4):
    """
    从Tushare读取指定日期前N天的历史交易数据；
    比如设定end为2017-09-26，就会获取不含26号的前4天的历史数据

    :param code: 股票代码
    :param end：指定日期，格式为：'2018-02-12'
    :param n: 默认为4
    :return: pandas dataframe
    """
    # type check
    if isinstance(code, str):
        pass
    else:
        raise RequireError("param:code should be string")
    if isinstance(end, str):
        pass
    else:
        raise RequireError("param:end should be string")
    if n < 0:
        raise RequireError("param:n should be greater than zero")

    history_data = tushare.get_k_data(code,
                                      start=the_date_n_day_before(35, end),
                                      end=end)
    if (history_data['date'].tolist())[-1] == end:
        clean_history_data = history_data[:-1]
        return clean_history_data.tail(n)
    else:
        return history_data.tail(n)


@retry(stop_max_attempt_number=5)
def get_sma(code, end, n):
    """
    从tushare获取包含截至日期的均线数据

    :param code: 股票代码
    :param end: 截至日期，格式：'2018-02-12'
    :param n: 获取多少天前的数据
    :return:
    """
    df = tushare.get_hist_data(code, start=the_date_n_day_before(n+15, end), end=end)
    split_by_n = df.head(n)
    ma5_before_reverse = split_by_n['ma5'].values.tolist()
    ma10_before_reverse = split_by_n['ma10'].values.tolist()
    ma5_before_reverse.reverse()  # 列表中前面的元素是较前日期的数据，最后一个元素是end日的均线数据
    ma10_before_reverse.reverse()  # 同MA5
    result = {'ma5': ma5_before_reverse, 'ma10': ma10_before_reverse,
              'comment': "the last element of 'maN' is the latest MA"}  # after reverse
    return result


def delete_data_head(text):
    """
    从网页文本中提取涨跌停统计数据，删去数据头部无用的信息

    :param text: string
    :return: str
    """
    tmppost = list(text).index('v')
    if text[tmppost: tmppost+9] == 'var datas':
        return text[tmppost:]
    else:
        return delete_data_head(text[tmppost+1:])


def delete_data_tail(text):
    """
    从网页文本中提取涨跌停统计数据，删去尾部无用的信息

    :param text: string
    :return: string
    """
    tmppost = list(text).index('v')
    if text[tmppost: tmppost+9] == 'var rates':
        return text[:tmppost+1]
    else:
        return delete_data_tail(text[tmppost+1:])


def judges(config, text):
    """
    通过三个NLP平台分析文本并投票决定情绪,分别调用百度AI，BosonNLP和腾讯文智的API
    :param config: dict
        {'baidu': [APP_ID, API_KEY, SECRET_KEY],
         'boson': [API_TOKEN],
         'tencent': [SECRET_ID, SECRET_KEY]}
    :param text: string
    :return: string
    """
    w = Wenzhi(config['tencent'][0], config['tencent'][1], 'gz', 'POST')
    cli = AipNlp(config['baidu'][0], config['baidu'][1], config['baidu'][2])
    bo = BosonNLP(config['boson'][0])
    pool = ThreadPoolExecutor(max_workers=3)
    candidate1 = pool.submit(w.text_sentiment, {'content': text})
    candidate2 = pool.submit(cli.sentimentClassify, text)
    candidate3 = pool.submit(bo.sentiment, text)
    result = [candidate1.result(), candidate2.result(), candidate3.result()]
    post_votes = [result[0]['positive'], result[1]['items'][0]['positive_prob'], result[2][0][0]]
    nega_votes = [result[0]['negative'], result[1]['items'][0]['negative_prob'], result[2][0][1]]
    # return [post_votes, nega_votes]
    pv = [i for i in post_votes if i > 0.5]
    nv = [x for x in nega_votes if x > 0.5]
    result = None
    if len(pv)/len(post_votes) > 1/3:
        result = 'P'
    else:
        if len(nv)/len(nega_votes) > 1/3:
            result = 'N'
    if result is None:
        return 'N'
    else:
        return result


def all_trading_day(year):
    """
    从tushare读取交易日数据，根据年返回当年所有交易日
    :param year: string,e.g '2018'
    :return: list
    """
    df = tushare.trade_cal()
    days = df['calendarDate'].tolist()
    is_trading = df['isOpen'].tolist()
    thisyear = [i for i in zip(days, is_trading) if year in i[0]]
    thisyear_tradingday = [pair for pair in thisyear if pair[1] == 1]
    thisyear_tradingday = [d[0] for d in thisyear_tradingday]
    return thisyear_tradingday


def findcodes(text):
    """
    从利好新闻中找股票代码
    :param text:
    :return:
    """
    lt = list(text)
    codes = []
    for i in lt:
        current_post = lt.index(i)
        if i == '（':
            codes.append(''.join(lt[current_post+1: current_post+7]))
        lt = lt[current_post:]
    return codes


def aipjudge(text, aipinstance):
    """
    调用百度AI NLP检查文本情绪
    :param text: 本文
    :param aipinstance:  百度AI的NLP实例
    :return: string
    """
    result = aipinstance.sentimentClassify(text)['items'][0]
    if result['positive_prob'] > result['negative_prob']:
        return 'P'
    else:
        return 'N'


def codes_from_positive_news(today, config):
    """
    从当日的利好新闻里获取股票代码
    :param today: string
    :param config: dict
    :return:
    """
    # 基于利好新闻筛选的股票
    news_url = get_today_news_urls(today, 'n')
    contents = [get_content(nurl) for nurl in news_url]
    # 保留有股票代码的段落
    contents = [[p for p in te if '（' in p or '）' in p] for te in contents]
    # 去除特殊字符
    contents = [[''.join(paragraph.split()) for paragraph in c] for c in contents]
    # 去除长度为0的
    contents = [content for content in contents if len(content) > 0]
    # 判断情绪
    sentiment_result = [[judges(config, text) for text in unit] for unit in contents]

    # 从利好新闻里挖掘股票代码
    codes = []
    for i, unit in enumerate(sentiment_result):
        tmp = []
        for u in zip(unit, contents[i]):
            if u[0] == 'P':
                tmp.append(findcodes(u[1]))
            else:
                pass
        codes.append(tmp)

    # 整合
    codes = [reduce(lambda x, y: x + y, l)for l in codes]

    return codes








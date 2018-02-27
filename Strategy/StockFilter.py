#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2018/2/23 18:34
# @Author  : CKHo
# @Email   : ckhoidea@hotmail.com
# @File    : StockFilter.py
# @Software: PyCharm

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Strategy.UniversalMethod import *
import asyncio


def deprecated_warning(func):
    def wrapper(*args):
        print("WARNING: This function is too slow I recommend you use general_ma_filterv2()")
        return func(*args)
    return wrapper


def count_time(func):
    def wrapper(*args):
        start = time()
        r = func(*args)
        end = time()
        print('cost: ', end-start)
        return r
    return wrapper


def ma_down(maN):
    """
    给定一组均线数据，判定是否为下降趋势

    :param maN: 来自get_sma的均线数据，比如ma5或者ma10
    :return: Boolean
    """
    maN.reverse()
    if maN[0] < maN[1]:
        return True
    else:
        return False


class HotSpot(object):
    """
    当日热点挖掘
    """
    def __init__(self, today, timeout, url='http://yuanchuang.10jqka.com.cn/qingbao/'):
        """
        设置获取热点数据的url,采用默认的即可

        :param today: 传入一个交易日的日期，格式为"Y-M-D"
        :param timeout: selenium等待时间
        :param url: 获取热点的url
        """
        self.timeout = timeout
        self.url = url
        self.today = today

    def get_today_hotspot_urls(self, hl):
        """
        使用headless浏览器获取今日热点的url列表

        :param hl: headless browser对象
        :return: list
        """
        container_xpath = '//*[@id="theList"]'
        subelement_in_container_xpath = '//*[@id="theList"]/div'

        # 定位热点新闻元素
        hl.get(self.url)
        container = WebDriverWait(hl, self.timeout).until(EC.presence_of_element_located((By.XPATH, container_xpath)))
        hotspots = container.find_elements_by_xpath(subelement_in_container_xpath)

        # 先找出上一个提供热点信息的交易日的日期
        timelines = container.find_elements_by_class_name('gn-timeline')
        last_trading_day = [timelines[timelines.index(d)+1].text for d in timelines if self.today in d.text][0]

        # 以上一个交易日为界限，获取今日的热点新闻
        today_hotspot = []
        for pot in hotspots:
            if last_trading_day in pot.text:
                break
            else:
                today_hotspot.append(pot)

        # 从热点新闻中提取具体的url
        base_url = 'http://yuanchuang.10jqka.com.cn/qingbao/'
        urls = []
        today_hotspot_without_timelines = today_hotspot[1:]
        for pot in today_hotspot_without_timelines:
            urls.append(base_url+pot.find_element_by_class_name('caption').get_attribute('data-jumpurl'))
        return urls

    def get_today_hotspot(self, url, hl):
        """
        从url中获取推荐个股数据

        :param url: 一个热点的url(注意是一个)
        :param hl: headless browser实例
        :return:
        """
        # hl = headless_initial('C:\gecko\geckodriver', 5)
        recommend_xpath = '//*[@id="ggtj"]/div'
        hl.get(url)
        recommend_stocks_container = WebDriverWait(hl, self.timeout)\
            .until(EC.presence_of_element_located((By.XPATH, recommend_xpath)))
        stock_list = recommend_stocks_container.find_elements_by_tag_name('a')
        # 获取热点相关的股票代码
        stock_codes = [s.get_attribute('href').split('/')[-2] for s in stock_list]
        return stock_codes


class InterDayStrategy(object):
    """
    用于基于日内交易的过滤器

    """
    def __init__(self, code, ltday, n, hot=False):
        """
        初始化类并决定此股能不能买入

        :param code: 股票代码，string
        :param ltday: 上一个交易日的日期，string，格式：'Y-M-D'
        :param n: MA数据的长度
        :param hot: 是否为热点事件
        """
        self.code = code
        self.last_tradingday = ltday
        if n < 3:
            raise ValueError("n must greater than 3")
        else:
            self.nday = n
        self.hot = hot
        self.MA = get_sma(self.code, self.last_tradingday, self.nday)
        # 直接访问buy属性即可
        self.buy = self.__judge()

    def __judge(self):
        # 根据MA判断
        if self.MA['ma5'][-1] > self.MA['ma10'][-1]:
            # 根据MA5的趋势判断
            if ma_down(self.MA['ma5']):
                return False
            else:
                return True
        else:
            # 根据是否为热点判断
            if self.hot:
                return True
            else:
                return False


def ids_func(pair):
    """
    日间规则的函数版

    :param pair: 格式：('600526', '2018-02-23', 3)
    :return: Boolean
    """
    hot = False
    code = pair[0]
    ltday = pair[1]
    n = pair[2]
    MA = get_sma(code, ltday, n)
    if MA['ma5'][-1] > MA['ma10'][-1]:
        # 根据MA5的趋势判断
        if ma_down(MA['ma5']):
            return False
        else:
            return True
    else:
        # 根据是否为热点判断
        if hot:
            return True
        else:
            return False


@deprecated_warning
def general_ma_filter(worker, codes, ltday):
    """
    从市场上剔除ST股后使用日间策略过滤出可能值得介入的股票,100条数据大致花费30秒

    :param worker: 配置多少个进程/线程,int
    :param codes: 股票代码列表
    :param ltday: 上一个交易日，string
    :return: list
    """
    pool = ThreadPoolExecutor(max_workers=worker)
    # pool = ProcessPoolExecutor(max_workers=worker)
    pair_for_map = [(c, ltday, 3) for c in codes]
    # result = pool.map(ids_func, pair_for_map)
    tmp = []
    for i in pair_for_map:
        res = pool.submit(ids_func, i)
        if res.result():
            tmp.append(i)
        else:
            pass
    return tmp


def general_ma_filterv2(worker, codes, ltday):
    """
    从市场上剔除ST股后使用日间策略过滤出可能值得介入的股票,100条数据大致花费15秒,必须将数据分拆为较小的组成再传入此函数，否则会超时

    :param worker: 配置多少个进程/线程,int
    :param codes: 股票代码列表
    :param ltday: 上一个交易日，string
    :return: list
    """
    pool = ThreadPoolExecutor(max_workers=worker)
    pair_for_map = [(c, ltday, 3) for c in codes]
    tmp = []
    for i in pair_for_map:
        tmp.append(pool.submit(ids_func, i))
    result = []
    for i in zip(pair_for_map, tmp):
        # default timeout 5 seconds
        if i[1].result(5):
            result.append(i[0])
        else:
            pass
    return [i[0] for i in result]


@count_time
def benchmark(w, c, l):
    return general_ma_filterv2(w, c, l)


async def ma_filter_sta(arg):
    if ids_func(arg):
        return arg
    else:
        pass


@deprecated_warning
def asyncio_gmf(codes, ltday):
    coros = []
    for i in codes:
        coros.append(ma_filter_sta((i, ltday, 3)))
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(asyncio.gather(*coros))
    res = [i for i in res if i is not None]
    return res























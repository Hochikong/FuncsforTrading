#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2018/2/23 11:33
# @Author  : CKHo
# @Email   : ckhoidea@hotmail.com
# @File    : MarketSentiment.py
# @Software: PyCharm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tushare as ts


def market_signal_decider(rd_sig, indices_sig):
    """
    根据涨跌统计和指数决定此刻大盘信号，规则：看空一票看空，看多全票看多

    :param rd_sig: 来自decide_by_surged_and_decline()的信号
    :param indices_sig: 来自decide_by_indices()的信号
    :return: string
    """
    final = None
    collection = [rd_sig, indices_sig]
    for i in collection:
        if i != 'N' and i != 'P':
            raise TypeError('Wrong signal existence')
    if rd_sig == indices_sig:
        if rd_sig == 'N':
            final = 'N'
        else:
            final = 'P'
    if rd_sig != indices_sig:
        if rd_sig == 'N' or indices_sig == 'N':
            final = 'N'
    return final


def decide_by_surged_and_decline(rd_data):
    """
    根据涨跌/停股数给出信号，规则：如果跌的股数除涨的股数大于0.9，看空，如果跌停的股数除涨停的股数大于0.8，看空，否则看多
    如果前者看多后者看空，则看多，如果后者看多前者看空，则看空

    :param rd_data: 股市涨跌股数与涨跌停股数数据
    :return: string
    """
    # 涨跌数求商
    without_limit = rd_data['without_limit']
    quotient1 = without_limit['drop']/without_limit['rise']
    sig1 = 'N' if quotient1 > 0.9 else 'P'
    # 涨跌停数求商
    with_limit = rd_data['with_limit']
    quotient2 = with_limit['drop']/with_limit['rise']
    sig2 = 'N' if quotient2 > 0.8 else 'P'

    if sig1 == sig2:
        if sig1 == 'N':
            return 'N'
        else:
            return 'P'
    else:
        if sig1 == 'P' and sig2 == 'N':
            return 'P'
        else:
            return 'N'


def decide_by_indices(indices_data):
    """
    根据指数给出信号，规则：指数小于0看空，否则看多；三大指数两个或以上看空则选择看空，否则看多

    :param indices_data: 指数数据
    :return: string
    """
    all_values = indices_data.values()
    # 找出涨幅小于0的指数
    negative_filter = [ind for ind in all_values if type(ind) == float and ind < 0]
    # 信号判断
    if len(negative_filter) <= 1:
        return 'P'
    if len(negative_filter) >= 2:
        return 'N'
    else:
        pass


def fetch_surged_and_decline_data(headless):
    """
    通过Headless类，基于selenium实时获取涨跌股数和涨跌停股数

    :param headless: 一个Headless类实例
    :return: dict
    """
    # 获取涨跌股数统计
    r_and_d_stat = headless.get_surged_and_decline()
    # 获取涨跌停股数统计
    r_and_d_limit_stat = headless.get_surged_and_decline_limit()
    return {'without_limit': r_and_d_stat, 'with_limit': r_and_d_limit_stat}


def fetch_indices_data():
    """
    获取实时三大股指：上证、深证和创业板

    :return:
    """
    df = ts.get_index()
    sh = extract_change(df.iloc[[0]])
    sz = extract_change(df.iloc[[12]])
    cy = extract_change(df.iloc[[17]])
    return {'sh': sh, 'sz': sz, 'cy': cy, 'default unit': 'percent'}


def extract_change(df):
    """
    将Tushare返回的dataframe单行数据提取change的值，值的单位为%

    :param df: dataframe
    :return: int
    """
    change = df['change'].values[0]
    return float(change)


def headless_initial(geckopath, timeout):
    """
    返回headless浏览器实例

    :param geckopath: geckodriver的路径
    :param timeout: 显式设置浏览器等待时间，防止因为元素未被加载而访问失败
    :return: 浏览器实例
    """
    options = webdriver.firefox.options.Options()
    options.add_argument("-headless")
    browser = webdriver.Firefox(executable_path=geckopath, firefox_options=options)
    browser.implicitly_wait(timeout)
    return browser


def raw_string_split(raw_string):
    """
    把通过selenium获取的涨跌统计数据进行分割并提取

    :param raw_string: String
    :return: 包含涨跌股数的统计的dict
    """
    tmp = raw_string.split(" ")
    rise = int((tmp[0].split("："))[1][:-1])
    drop = int((tmp[1].split("："))[1][:-1])
    return {'rise': rise, 'drop': drop}


class Headless(object):
    """
    启动headless firefox用于爬取数据涨跌数据

    """
    def __init__(self, geckopath, timeout, url):
        self.browser = headless_initial(geckopath, timeout)
        self.timeout = timeout
        self.url = url

    def get_surged_and_decline(self):
        """
        获取涨跌股数统计

        :return:
        """
        xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/p"
        self.browser.get(self.url)
        # Wait for the element
        element = WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        raw_string = element.text
        # String Analysis
        result = raw_string_split(raw_string)
        return result

    def get_surged_and_decline_limit(self):
        """
        获取涨跌停股数统计

        :return:
        """
        xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/p"
        # Wait for the element
        element = WebDriverWait(self.browser, self.timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        raw_string = element.text
        # String Analysis
        result = raw_string_split(raw_string)
        return result

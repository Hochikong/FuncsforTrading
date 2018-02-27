#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2018/2/26 20:42
# @Author  : CKHo
# @Email   : ckhoidea@hotmail.com
# @File    : DailySentiment.py
# @Software: PyCharm

import requests
from bs4 import *
from retrying import retry


@retry(stop_max_attempt_number=5)
def get_today_news_urls(today, dtype):
    """
    获取今日(仅限交易日)的评论, today参数不能用距离运行时过久的日期
    :param today: '2018-02-26',string
    :param dtype: c(omment) or n(ews),分别从不同的地址获取
    :return: list
    """
    split_today = today.split('-')
    match_string = "{0}月{1}日".format(split_today[1], split_today[2])
    if dtype == 'c':
        url = 'http://yuanchuang.10jqka.com.cn/djpingpan_list/'
    elif dtype == 'n':
        url = 'http://stock.10jqka.com.cn/tzjh_list/'
    else:
        raise ValueError('Wrong dtype')
    page = requests.get(url, timeout=5).text
    soup = BeautifulSoup(page, 'lxml')
    list_cont = soup.find_all('li')
    news = [i for i in list_cont if i.find(attrs={'class': 'arc-title'})]
    today_news = [n for n in news if match_string in n.get_text()]
    news_url = [news.find('a').get('href') for news in today_news]
    return news_url


@retry(stop_max_attempt_number=5)
def get_content(url):
    """
    从指定的市场评论url中找到正文
    :param url: 新闻url
    :return:
    """
    page = requests.get(url, timeout=5).text
    soup = BeautifulSoup(page, 'lxml')
    news_container = soup.find(attrs={'class':'main-text atc-content'})
    all_paragraph = news_container.find_all('p')
    all_paragraph = [p for p in all_paragraph if len(p.get_text()) > 0]
    content = all_paragraph[:-1]
    paragraph_content = [(i.get_text()).strip() for i in content]
    paragraph_content = [t for t in paragraph_content if len(t) > 0 ]
    return paragraph_content





#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2018/2/25 21:15
# @Author  : CKHo
# @Email   : ckhoidea@hotmail.com
# @File    : RiskControl.py
# @Software: PyCharm


import requests
import json


def get_return_rate(url, token):
    """
    从交易服务器根据指定的token获取用户的收益统计数据

    :param url: 完整的服务器地址，可能需要加上端口号，e.g. http://localhost:5000
    :param token: 用户的trade token
    :return: dict
    """
    header = {'trade_token': token}
    endpoint = url + "/user"
    payload = json.dumps({'query': 'real_time_profit'})
    result = requests.post(endpoint, data=payload, headers=header)
    return_rates = result.json()
    return return_rates


def risk_control(stock_detail):
    """
    把get_return_rate里的stocks_rateR的个股收益等数据拿出来进行止损判断

    :param stock_detail: 详细的股票数据，格式如下：
           {'amount': '800',
            'avgprice': '50.05',
            'code': '002230',
            'current_price': '53.300',
            'current_total': '42640.0',
            'rateR': '0.0649',
            'return': '2600.0'}
    :return: dict
    """
    current_rate = float(stock_detail['rateR'])
    stop_point = 0
    # 判断是盈是亏
    if current_rate > 0:
        if current_rate > 0.1:
            stop_point = current_rate - 0.06
        else:
            if current_rate > 0.05:
                stop_point = current_rate - 0.04
            else:
                stop_point = current_rate - 0.02
        return {'signal': 'wait', 'stop': round(stop_point, 3)}
    else:
        if current_rate > -0.06:
            return {'signal': 'wait'}
        else:
            return {'signal': 'offer'}

#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2018/2/25 12:22
# @Author  : CKHo
# @Email   : ckhoidea@hotmail.com
# @File    : PositionControl.py
# @Software: PyCharm

import requests
import json


def get_balance(url, token):
    """
    从交易服务器根据指定的token获取用户账户余额

    :param url: 完整的服务器地址，可能需要加上端口号，e.g. http://localhost:5000
    :param token: 用户专属的trade token
    :return: dict
    """
    header = {'trade_token': token}
    endpoint = url+"/user"
    payload = json.dumps({'query': 'user'})
    result = requests.post(endpoint, data=payload, headers=header)
    balance = result.json()
    return balance


def balance_split(balance_data):
    """
    根据自己的规则将get_balance返回的数据进行判断，资金划分,只用在创建新账户的时候

    :param balance_data: get_balance的返回数据，dict
    :return: dict
    """
    total = float(balance_data['total'])
    balance = float(balance_data['balance'])
    if total != balance:
        raise ValueError("Balance no equal to Total, you should use this func when after creating a new account once")
    else:
        reserve = total * 0.1
        for_trading = total - reserve
        return {'reserve': reserve, 'for_trading': for_trading}


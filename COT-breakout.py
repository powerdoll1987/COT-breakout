# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 11:28:33 2016
验证假设和推论
假设1：未来会出现的极值和之前极值接近
假设2：价格变动和头寸变动基本正相关
推论：从现在头寸和之前极值的距离可以推测出未来价格变动的幅度
再观察其他一些现象
@author: yiran.zhou
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('..')
import taifook.taifook as tf
import taifook.zigzag_c as zz
import pylab as pl
import matplotlib.pyplot as plt


if __name__ == '__main__':
    
    #*****统计头寸突破幅度的分布（当前极值比上前一个极值，验证假设1）*********************
    pos = pd.read_excel('INPUT COT GCA.xls', sheetname = 'Sheet1 (2)')
    pos.set_index('Date', inplace = True)
    price = pd.read_excel('INPUT COT GCA.xls', sheetname = 'Sheet2')
    
    # 第4列是NCN，最后一列是OI
    netPos = pos.ix[:, 3] / pos.ix[:, -1]
    pivots = zz.peak_valley_pivots2(netPos, 0.1, -0.1)
    zz.plot_pivots(netPos, pivots)
    
    peak = netPos[pivots == 1]
    valley = netPos[pivots == -1]
    
    peakDiff = peak.diff().dropna()
    valleyDiff =valley.diff().dropna()
    
    pl.figure()
    pl.hist(peakDiff)

    #突破之后的价格变化（突破之后的价格变动和突破之前的价格变动比值）
    
    
    #头寸走到极值一半时价格变动占总价格变动的比值（验证假设2）
    
    
    #找出大幅突破的情况，观察之后的价格变动（即分布的右边）
    
    
    #找出不到前一个极值并距离较远的情况，观察之后的价格变动（即分布的左边）
    
    
    #极值出现后，按多头和空头反应分类，看之后价格是否有区别
    
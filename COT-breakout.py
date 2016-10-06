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
from pandas.tseries.offsets import Day


if __name__ == '__main__':
    
#*****统计头寸突破幅度的分布（当前极值比上前一个极值，验证假设1）*********************
    pos = pd.read_excel('INPUT COT GCA.xls', sheetname = 'Sheet1 (2)')
    pos.set_index('Date', inplace = True)
    price = pd.read_excel('INPUT COT GCA.xls', sheetname = 'Sheet2')
    price.set_index('GC1 Comdty', inplace = True)
    
    # 第4列是NCN，最后一列是OI
    netPos = pos.ix[:, 3] / pos.ix[:, -1]
    pivots = zz.peak_valley_pivots2(netPos, 0.1, -0.1)
    zz.plot_pivots(netPos, pivots)
    
    # 画出每次极值和之前一次极值的距离，观察突破或者不及的分布
    peak = netPos[pivots == 1]
    valley = netPos[pivots == -1]
    peakDiff = peak.diff().dropna()
    valleyDiff =valley.diff().dropna()   
    extremeDiff = pd.concat([peakDiff, valleyDiff]).sort_index()
    pl.figure(3)
    pl.hist(extremeDiff, bins = 40)
#    pl.figure(2)
#    pl.hist(peakDiff, bins = 40, color = 'r', alpha = 0.5)
#    pl.figure(2)
#    pl.hist(valleyDiff, bins = 40, color = 'g', alpha = 0.5)
    
    # 观察极值连线（从顶到底和从底到顶）的统计量
    extreme = netPos[(pivots == 1) | (pivots == -1)]
    ext_line = abs(extreme.diff().dropna()).describe()
    
#*****突破之后的价格变化（突破之后的价格变动和突破之前的价格变动比值）***************        
    # 找出第一次突破前一个极值的时间，以及在这个时间点和下一个极值的时间点之间价格的变动, 比较突破大小和价格变动的关系
    # 先找出突破时间
    peakBreakDf = pd.DataFrame(columns = ['peakDiff', 'breakStart','breakEnd', 'prevPeak', 'breakErr', 'priceChg'])
    peakBreakDf.breakEnd = peakDiff[peakDiff >0].index
    peakBreakDf.peakDiff = peakDiff[peakDiff >0].values
    k = 0
    while k < len(peakBreakDf.index):
        prevPeakDt = peak.index[peak.index.get_loc(peakBreakDf.ix[k, 'breakEnd']) - 1]
        peakBreakDf.ix[k, 'prevPeak'] = prevPeakDt
        prevPeak = peak[prevPeakDt]
        i = netPos.index.get_loc(prevPeakDt)
        while 1:
            if netPos[i] > prevPeak:
                break
            i += 1
        breakStartDt = netPos.index[i]
        breakErr = netPos[i] - prevPeak #突破时的仓位和前高的距离
        peakBreakDf.ix[k, ['breakStart','breakErr']] = breakStartDt, breakErr
        k += 1

    # 突破之后的价格变化
    k = 0
    while k < len(peakBreakDf.index):
        breakStartDay = peakBreakDf.ix[k, 'breakStart']
        breakEndDayAdj = peakBreakDf.ix[k, 'breakEnd'] + Day(7)
        startPrice = price.ix[breakStartDay, 'PX_LAST']
        highestPrice = max(price.ix[breakStartDay:breakEndDayAdj, 'PX_HIGH'])
        peakBreakDf.ix[k, 'priceChg'] = (highestPrice - startPrice)/startPrice
        k += 1
#    pl.figure()
#    pl.scatter(peakBreakDf.peakDiff, peakBreakDf.priceChg)
    
    # 对valley重新做一遍
    valleyBreakDf = pd.DataFrame(columns = ['valleyDiff', 'breakStart','breakEnd', 'prevValley', 'breakErr', 'priceChg'])
    valleyBreakDf.breakEnd = valleyDiff[valleyDiff <0].index
    valleyBreakDf.valleyDiff = valleyDiff[valleyDiff <0].values
    k = 0
    while k < len(valleyBreakDf.index):
        prevValleyDt = valley.index[valley.index.get_loc(valleyBreakDf.ix[k, 'breakEnd']) - 1]
        valleyBreakDf.ix[k, 'prevValley'] = prevValleyDt
        prevValley = valley[prevValleyDt]
        i = netPos.index.get_loc(prevValleyDt)
        while 1:
            if netPos[i] < prevValley:
                break
            i += 1
        breakStartDt = netPos.index[i]
        breakErr = -netPos[i] + prevValley #突破时的仓位和前高的距离
        valleyBreakDf.ix[k, ['breakStart','breakErr']] = breakStartDt, breakErr
        k += 1

    # 突破之后的价格变化
    k = 0
    while k < len(valleyBreakDf.index):
        breakStartDay = valleyBreakDf.ix[k, 'breakStart']
        breakEndDayAdj = valleyBreakDf.ix[k, 'breakEnd'] + Day(7)
        startPrice = price.ix[breakStartDay, 'PX_LAST']
        lowestPrice = min(price.ix[breakStartDay:breakEndDayAdj, 'PX_LOW'])
        valleyBreakDf.ix[k, 'priceChg'] = (lowestPrice - startPrice)/startPrice
        k += 1
#    pl.figure()
#    pl.scatter(valleyBreakDf.valleyDiff, valleyBreakDf.priceChg)
    
    # 合并peak和valley作图
    x = peakBreakDf.peakDiff.tolist() + abs(valleyBreakDf.valleyDiff).tolist()
    y = peakBreakDf.priceChg.tolist() + abs(valleyBreakDf.priceChg).tolist()
    pl.figure()
    pl.scatter(x, y)
    
    
#*****头寸变化和价格变化的关系（验证假设2）********************************************
    netPosM = pd.DataFrame(netPos)
    netPosM.columns = ['NP']
    netPosM['pivots'] = pd.Series(pivots, index = netPosM.index)
    
    # 分别找出价格上升和下降过程中的所有net pos
    netPosUptrend = pd.DataFrame(columns = ['NP', 'pivot', 'lastPV'])
    netPosDowntrend = pd.DataFrame(columns = ['NP', 'pivot', 'lastPV'])
    i = 1
    lastPivot = pivots[0]
    lastPV = netPos[0]
    tmp = pd.DataFrame({'NP':netPos[0], 'pivot':pivots[0], 'lastPV':lastPV}, index = [netPos.index[0]])
    netPosUptrend = pd.concat([netPosUptrend, tmp]) if lastPivot == 1 else netPosUptrend
    netPosDowntrend = pd.concat(netPosDowntrend, tmp) if lastPivot == -1 else netPosDowntrend      
    while i < len(netPos.index):
        tmp = pd.DataFrame({'NP':netPos[i], 'pivot':pivots[i], 'lastPV':lastPV}, index = [netPos.index[i]])
        if lastPivot == 1:         
            netPosDowntrend = pd.concat([netPosDowntrend, tmp])
            lastPivot = -1 if pivots[i] == -1 else lastPivot
            lastPV = netPos[i] if pivots[i] == -1 else lastPV
        elif lastPivot == -1:
            netPosUptrend = pd.concat([netPosUptrend, tmp])
            lastPivot = 1 if pivots[i] == 1 else lastPivot   
            lastPV = netPos[i] if pivots[i] == 1 else lastPV
        i += 1

    # 找出之前和之后的顶点和底点，计算其所处的位置
    i = len(netPosUptrend.index) - 1
    netPosUptrend.reindex(columns = netPosUptrend.columns.tolist() + ['nextPV'])
    nextPV = netPosUptrend.ix[-1, 'NP']
    while i >= 0:   
        nextPV = netPosUptrend.ix[i, 'NP'] if netPosUptrend.ix[i, 'pivot'] == 1 else nextPV
        netPosUptrend.ix[i, 'nextPV'] = nextPV
        i -= 1
        
    i = len(netPosDowntrend.index) - 1
    netPosDowntrend.reindex(columns = netPosDowntrend.columns.tolist() + ['nextPV'])
    nextPV = netPosDowntrend.ix[-1, 'NP']
    while i >= 0:   
        nextPV = netPosDowntrend.ix[i, 'NP'] if netPosDowntrend.ix[i, 'pivot'] == -1 else nextPV
        netPosDowntrend.ix[i, 'nextPV'] = nextPV
        i -= 1
        
        
        
        
    #找出大幅突破的情况，观察之后的价格变动（即分布的右边）
    
    
    #找出不到前一个极值并距离较远的情况，观察之后的价格变动（即分布的左边）
    
    
    #极值出现后，按多头和空头反应分类，看之后价格是否有区别
    
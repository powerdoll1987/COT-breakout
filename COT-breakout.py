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
from scipy import stats


if __name__ == '__main__':
    
#*****统计头寸突破幅度的分布（当前极值比上前一个极值，验证假设1）*********************
    pos = pd.read_excel('INPUT COT TYA.xls', sheetname = 'Sheet1 (2)')
    pos.set_index('Date', inplace = True)
    price = pd.read_excel('INPUT COT TYA.xls', sheetname = 'Sheet2')
    price.set_index('TY1 Comdty', inplace = True)
    
    # 第4列是NCN，最后一列是OI
    netPos = pos.ix[:, 3] / pos.ix[:, -1]
    pivots = zz.peak_valley_pivots2(netPos, 0.07, -0.07)
    zz.plot_pivots(netPos, pivots)
    
    # 画出每次极值和之前一次极值的距离，观察突破或者不及的分布
    peak = netPos[pivots == 1]
    valley = netPos[pivots == -1]
    peakDiff = peak.diff().dropna()
    valleyDiff =valley.diff().dropna()   
    extremeDiff = pd.concat([peakDiff, valleyDiff]).sort_index()
    pl.figure(3)
    pl.title('Breakout distribution')
    pl.hist(extremeDiff, bins = 40)
#    pl.figure(2)
#    pl.hist(peakDiff, bins = 40, color = 'r', alpha = 0.5)
#    pl.figure(2)
#    pl.hist(valleyDiff, bins = 40, color = 'g', alpha = 0.5)
    
    # 观察极值连线（从顶到底和从底到顶）的统计量
    extreme = netPos[(pivots == 1) | (pivots == -1)]
    ext_line = abs(extreme.diff().dropna()).describe()
    print(ext_line)
    
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
    pl.title('Breakout and subsequent price move')
    pl.scatter(x, y)
    slope, intercept, r_value, p_value, slope_std_error = stats.linregress(x, y)
    xa = np.array(x)
    predict_y = intercept + slope * xa
    pl.plot(xa, predict_y, 'k-')
    print('1. slope: %.3f, intercept: %.3f, r-squared: %.3f'%(slope, intercept, r_value**2))
    
    
#*****头寸变化和价格变化的关系（验证假设2）********************************************
    netPosM = pd.DataFrame(netPos)
    netPosM.columns = ['NP']
    netPosM['pivots'] = pd.Series(pivots, index = netPosM.index)
    
    # 分别找出价格上升和下降过程中的所有net pos
    netPosUptrend = pd.DataFrame(columns = ['NP', 'pivot', 'lastPV', 'lastPVDt'])
    netPosDowntrend = pd.DataFrame(columns = ['NP', 'pivot', 'lastPV', 'lastPVDt'])
    i = 1
    lastPivot = pivots[0]
    lastPV = netPos[0]
    lastPVDt = netPos.index[0]
    tmp = pd.DataFrame({'NP':netPos[0], 'pivot':pivots[0], 'lastPV':lastPV, 'lastPVDt':lastPVDt}, index = [netPos.index[0]])
    netPosUptrend = pd.concat([netPosUptrend, tmp]) if lastPivot == 1 else netPosUptrend
    netPosDowntrend = pd.concat([netPosDowntrend, tmp]) if lastPivot == -1 else netPosDowntrend      
    while i < len(netPos.index):
        tmp = pd.DataFrame({'NP':netPos[i], 'pivot':pivots[i], 'lastPV':lastPV, 'lastPVDt':lastPVDt}, index = [netPos.index[i]])
        if lastPivot == 1:         
            netPosDowntrend = pd.concat([netPosDowntrend, tmp])
            if pivots[i] == -1:
                lastPivot = -1
                lastPV = netPos[i]
                lastPVDt = netPos.index[i]
        elif lastPivot == -1:
            netPosUptrend = pd.concat([netPosUptrend, tmp])
            if pivots[i] == 1:
                lastPivot = 1
                lastPV = netPos[i]
                lastPVDt = netPos.index[i]
        i += 1

    # 找出之前和之后的顶点和底点，计算其所处的位置
    i = len(netPosUptrend.index) - 1
    netPosUptrend = netPosUptrend.reindex(columns = netPosUptrend.columns.tolist() + ['nextPV', 'nextPVDt'])
    nextPV = netPosUptrend.ix[-1, 'NP']
    nextPVDt = netPosUptrend.index[-1]
    while i >= 0:   
        if netPosUptrend.ix[i, 'pivot'] == 1:
            nextPV = netPosUptrend.ix[i, 'NP']
            nextPVDt = netPosUptrend.index[i]
        netPosUptrend.ix[i, ['nextPV','nextPVDt']] = [nextPV, nextPVDt]
        i -= 1
        
    i = len(netPosDowntrend.index) - 1
    netPosDowntrend = netPosDowntrend.reindex(columns = netPosDowntrend.columns.tolist() + ['nextPV', 'nextPVDt'])
    nextPV = netPosDowntrend.ix[-1, 'NP']
    nextPVDt = netPosDowntrend.index[-1]
    while i >= 0:   
        if netPosDowntrend.ix[i, 'pivot'] == -1:
            nextPV = netPosDowntrend.ix[i, 'NP']
            nextPVDt = netPosDowntrend.index[i]
        netPosDowntrend.ix[i, ['nextPV', 'nextPVDt']] = [nextPV, nextPVDt]
        i -= 1
        
    netPosUptrend['npPct'] = (netPosUptrend['NP'] - netPosUptrend['lastPV'])/(netPosUptrend['nextPV'] - netPosUptrend['lastPV'])
    netPosDowntrend['npPct'] = (netPosDowntrend['NP'] - netPosDowntrend['lastPV'])/(netPosDowntrend['nextPV'] - netPosDowntrend['lastPV'])
   
    # 找出对应的价格,MAX/MIN用的是头寸极值点附近的价格
    netPosUptrend = netPosUptrend.reindex(columns = netPosUptrend.columns.tolist() + ['priceChg'])
    i = 0
    while i < len(netPosUptrend.index):
        priceNow = price.ix[netPosUptrend.index[i], 'PX_LAST']
        priceMin = min(price.ix[netPosUptrend.ix[i, 'lastPVDt'] -Day(7):netPosUptrend.ix[i, 'lastPVDt'] +Day(7), 'PX_LOW'])
        priceMax = max(price.ix[netPosUptrend.ix[i, 'nextPVDt'] -Day(7):netPosUptrend.ix[i, 'nextPVDt'] +Day(7), 'PX_HIGH'])
        priceChg = (priceNow-priceMin) / (priceMax- priceMin)
        netPosUptrend.ix[i, 'priceChg'] = priceChg
        i += 1
        
    netPosDowntrend = netPosDowntrend.reindex(columns = netPosDowntrend.columns.tolist() + ['priceChg'])
    i = 0
    while i < len(netPosDowntrend.index):
        priceNow = price.ix[netPosDowntrend.index[i], 'PX_LAST']
        priceMax = max(price.ix[netPosDowntrend.ix[i, 'lastPVDt'] -Day(7):netPosDowntrend.ix[i, 'lastPVDt'] +Day(7), 'PX_LOW'])
        priceMin = min(price.ix[netPosDowntrend.ix[i, 'nextPVDt'] -Day(7):netPosDowntrend.ix[i, 'nextPVDt'] +Day(7), 'PX_HIGH'])
        priceChg = (priceNow-priceMax) / (priceMin- priceMax)
        netPosDowntrend.ix[i, 'priceChg'] = priceChg
        i += 1
        
    netPosUptrend = netPosUptrend.dropna()
    netPosDowntrend = netPosDowntrend.dropna()
    
    # 把价格变化和头寸变化作图
    pl.figure()
    pl.title('position and price (uptrend)')
    pl.scatter(netPosUptrend.npPct, netPosUptrend.priceChg)  
    
    pl.figure()
    pl.title('position and price (downtrend)')
    pl.scatter(netPosDowntrend.npPct, netPosDowntrend.priceChg)  
    
    netPosUptrendAdj = netPosUptrend[(netPosUptrend.priceChg >= 0) & (netPosUptrend.priceChg <= 1)]
    netPosUptrendAdj = netPosUptrendAdj[(netPosUptrendAdj.npPct >= 0) & (netPosUptrendAdj.npPct <= 1)]
    pl.figure()
    pl.title('position and price adjusted (uptrend)')
    pl.scatter(netPosUptrendAdj.npPct, netPosUptrendAdj.priceChg)  
    slope2, intercept2, r_value2, p_value2, slope_std_error2 = stats.linregress(netPosUptrendAdj.npPct.tolist(), netPosUptrendAdj.priceChg.tolist())
    predict_y2 = intercept2 + slope2 * netPosUptrendAdj.npPct
    pl.plot(netPosUptrendAdj.npPct, predict_y2, 'k-')
    print('2. slope: %.3f, intercept: %.3f, r-squared: %.3f'%(slope2, intercept2, r_value2**2))
    
    netPosDowntrendAdj = netPosDowntrend[(netPosDowntrend.priceChg >= 0) & (netPosDowntrend.priceChg <= 1)]
    netPosDowntrendAdj = netPosDowntrendAdj[(netPosDowntrendAdj.npPct >= 0) & (netPosDowntrendAdj.npPct <= 1)]    
    pl.figure()
    pl.title('position and price adjusted (downtrend)')
    pl.scatter(netPosDowntrendAdj.npPct, netPosDowntrendAdj.priceChg)
    slope3, intercept3, r_value3, p_value3, slope_std_error3 = stats.linregress(netPosDowntrendAdj.npPct.tolist(), netPosDowntrendAdj.priceChg.tolist())
    predict_y3 = intercept3 + slope3 * netPosDowntrendAdj.npPct
    pl.plot(netPosDowntrendAdj.npPct, predict_y3, 'k-')
    print('3. slope: %.3f, intercept: %.3f, r-squared: %.3f'%(slope3, intercept3, r_value3**2))
        
        
        
        
        
    #找出大幅突破的情况，观察之后的价格变动（即分布的右边）
    
    
    #找出不到前一个极值并距离较远的情况，观察之后的价格变动（即分布的左边）
    
    
    #极值出现后，按多头和空头反应分类，看之后价格是否有区别
    
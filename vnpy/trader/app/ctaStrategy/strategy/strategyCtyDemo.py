# encoding: UTF-8

"""
这里的Demo是一个最简单的策略实现，并未考虑太多实盘中的交易细节，如：
1. 委托价格超出涨跌停价导致的委托失败
2. 委托未成交，需要撤单后重新委托
3. 断网后恢复交易状态
4. 等等
这些点是作者选择特意忽略不去实现，因此想实盘的朋友请自己多多研究CTA交易的一些细节，
做到了然于胸后再去交易，对自己的money和时间负责。
也希望社区能做出一个解决了以上潜在风险的Demo出来。
"""

from __future__ import division

from vnpy.trader.vtObject import VtBarData,KeyTickData
from vnpy.trader.vtConstant import EMPTY_STRING, EMPTY_FLOAT
from vnpy.trader.app.ctaStrategy.ctaTemplate import CtaTemplate
from vnpy.cty.tools import *
from datetime import datetime, time
import numpy as np
import talib as ta
import math

########################################################################
class CtyEmaDemoStrategy(CtaTemplate):
    """双指数均线策略Demo"""
    className = 'CtyEmaDemoStrategy'
    author = u'Tianyang.Cao'
    
    # 策略参数
    fastK = 20                     # 快速EMA参数
    slowK = 60                    # 慢均线倍数    慢均线 = fastK * slowKRate
    maxHoldPos = 4                # 最大持仓手数，仓位
    # 策略变量
    bar = None
    barMinute = EMPTY_STRING

    closeHistory = []             # 缓存最新价的数组
    closeArray = []               # 缓存最新价的数组
    lowHistory = []               # 缓存最低价的数组
    highHistory = []              # 缓存最低价的数组
    fastHistory = []              # 短均线数组
    slowHistory = []              # 长均线数组
    holdTimes = []                # 持仓时间
    minHistory = 50              # 最少缓存60根开始计算
    maxHistory = 121              # 最多缓存120根

    fastMa0 = EMPTY_FLOAT         # 当前最新的快速EMA
    fastMa1 = EMPTY_FLOAT         # 上一根的快速EMA
    slowMa0 = EMPTY_FLOAT         # 当前最新的慢速EMA
    slowMa1 = EMPTY_FLOAT         # 上一根的慢速EMA

    topPrice = EMPTY_FLOAT        # 开仓前最高价
    lowPrice = EMPTY_FLOAT        # 开仓后最低价
    highPrice = EMPTY_FLOAT       # 观测区最高价
    stopPrice = EMPTY_FLOAT       # 固定止损价
    addPrice = EMPTY_FLOAT        # 加仓价

    shortATR = EMPTY_FLOAT        # 短期ATR
    profitPrice = EMPTY_FLOAT     # 止盈价
    lastOrderType = 'None'        # 最近一次下单动作 K开仓 J加仓 P平仓 Z 止盈

    kcFlag = False                # 开仓监控标志位
    kcMonitorCount = 1            # 开仓监控次数
    orderList = []                # 保存委托代码的列表
    cycle = 20                    # 周期感觉最终要的

    kCount = 0                    # 开仓次数
    jCount = 0                    # 加仓次数
    gkCount = 0                   # 高开次数
    zdCount = 0                   # Atr过大次数
    mCount = 0                    # 移动次数
    dkPCount = 0                  # 暴跌平仓次数
    moveStopTime = 0              # 挪动止损线次数

    lastProfit = 0                # 开仓盈利次数
    lastLoss = 0                  # 开仓亏损次数

    holdScore = 0                 # 持仓评分
    kcScore = 0                   # 开仓评分
    holdBars = 0                  # 持仓周期


    holiday = ['2015/2/13', '2015/4/3', '2015/4/30', '2015/6/19', '2015/9/2', '2015/9/25', '2015/12/31',
               '2016/2/5', '2016/3/29', '2016/4/29', '2016/6/8', '2016/9/14', '2016/9/30', '2016/12/30',
               '2017/1/26', '2017/2/3', '2017/3/31', '2017/4/28', '2017/5/26,', '2017/9/29', '2017/12/29']
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'fastK',
                 'slowK',
                 'maxHoldPos',
                 'openRatio',
                 'stopRatio',
                 'cycle']
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'fastMa0',
               'fastMa1',
               'slowMa0',
               'slowMa1']  

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(CtyEmaDemoStrategy, self).__init__(ctaEngine, setting)
        
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）
        self.pos = 0
        self.closeHistory = []  # 缓存最新价的数组
        self.closeArray = []  # 缓存最新价的数组
        self.lowHistory = []  # 缓存最低价的数组
        self.highHistory = []  # 缓存最低价的数组
        self.fastHistory = []
        self.slowHistory = []
        self.holdTimes = []
        self.orderList = []
        #----------------------------------------------------------------------
    def __del__(self, ctaEngine, setting):
        """析构函数"""
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'初始化')
        #initData = self.loadBar(self.initDays)
        #for tick in initData:
        #    self.onTick(tick)
        self.closeHistory = []  # 缓存最新价的数组
        self.lowHistory = []  # 缓存最低价的数组
        self.highHistory = []  # 缓存最低价的数组
        self.fastHistory = []
        self.slowHistory = []
        self.holdTimes = []
        self.orderList = []
        self.closeArray = []
        self.putEvent()
        self.holdBars = 0

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'双EMA演示策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        print('暴跌平仓：%d,开仓：%d ,移动开仓：%d 高开：%d,剧震：%d，加仓：%d' % (self.dkPCount, self.kCount, self.mCount, self.gkCount, self.zdCount,self.jCount))
        self.writeCtaLog(u'双EMA演示策略停止')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        # 计算K线
        tickMinute = tick.datetime.minute

        if tickMinute != self.barMinute:
            if self.bar:
                self.onBar(self.bar)

            bar = VtBarData()
            bar.vtSymbol = tick.vtSymbol
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange

            bar.open = tick.openPrice
            bar.high = tick.highPrice
            bar.low = tick.lowPrice
            bar.close = tick.lastPrice

            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime  # K线的时间设为第一个Tick的时间

            # 实盘中用不到的数据可以选择不算，从而加快速度
            # bar.volume = tick.volume
            # bar.openInterest = tick.openInterest

            self.bar = bar  # 这种写法为了减少一层访问，加快速度
            self.barMinute = tickMinute  # 更新当前的分钟

        else:  # 否则继续累加新的K线
            bar = self.bar  # 写法同样为了加快速度

            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.datetime = tick.datetime
            bar.close = tick.lastPrice
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        if self.bar and self.bar.date != bar.date:
            """当日期变化时触发相应的处理"""
            self.newDay(bar)
        for orderID in self.orderList:
            self.cancelOrder(orderID)
            self.orderList = []

        # 排除高开对均线的影响
        '''
        if self.bar and self.pos == 0:
            high = bar.open - self.bar.close
            if (high / bar.open) * 100 > 1:
                self.gkCount += 1
                self.onInit()
                #print ("排除低开 时间:%s,价差:%f" % (self.bar.datetime.strftime('%Y%m%d-%H%M'), bar.open - self.bar.close))
        '''
        if self.bar and self.pos == 0:
            high = abs(bar.open - bar.close)
            if (high / bar.close) * 100 > 1:
                self.gkCount += 1
                return
                # self.onInit()
        if bar.symbol == 'NI' and validateNI(bar):
            pass
        elif (bar.symbol == 'RB' or bar.symbol == 'RB0000') and validateRB(bar):
            pass
        elif bar.symbol == 'J' and validateJ(bar):
            pass
        elif bar.symbol == 'MA' and validateMA(bar):
            pass
        elif bar.symbol == 'IF0000' and validateIF(bar):
            pass
        else:
            return
        self.bar = bar
        '''准备数据'''
        self.closeHistory.append(float(bar.close))
        self.lowHistory.append(float(bar.low))
        self.highHistory.append(float(bar.high))
        '''至少需要minHistory根'''
        if len(self.closeHistory) < self.minHistory:
            return
        if len(self.closeHistory) > self.maxHistory:
            self.closeHistory.pop(0)
            self.lowHistory.pop(0)
            self.highHistory.pop(0)

        closeArray = np.array(self.closeHistory)
        lowArray = np.array(self.lowHistory)
        highArray = np.array(self.highHistory)

        # 计算快慢均线
        fastSMA = ta.SMA(closeArray, timeperiod=self.fastK)
        slowSMA = ta.SMA(closeArray, timeperiod=self.slowK)
        self.fastMa0 = fastSMA[-1]
        self.slowMa0 = slowSMA[-1]
        self.fastMa1 = fastSMA[-2]
        self.slowMa1 = slowSMA[-2]
        self.shortATR = ta.ATR(highArray[self.cycle * -1:-2], lowArray[self.cycle * -1:-2], closeArray[self.cycle * -1:-2])[
            -1]

        #self.lowPrice = ta.MIN(np.array(self.closeHistory), timeperiod=len(self.closeHistory))[-2]
        #self.highPrice = ta.MAX(np.array(self.closeHistory), timeperiod=len(self.closeHistory))[-2]
        closeArray.sort()
        #除噪音
        self.lowPrice = (closeArray[0]+closeArray[1])/2
        self.highPrice = (closeArray[-1]+closeArray[-2])/2
        qiedian = bar.datetime.strftime('%Y%m%d-%H%M')
        if qiedian == '20170712-1050':
            print bar.datetime.weekday()

        '''生成开仓，平仓，加仓，止损移动标志位'''
        openFlag = False
        closeFlag = False
        if self.pos == 0 and not self.kcFlag:
            '''开仓信号识别'''
            self.monitorQuote()
        elif self.pos > 0:
            self.closeArray.append(float(bar.close))
            '''平仓信号识别'''
            closeFlag = self.monitorPOS()
        elif self.kcFlag:
            '''是否开仓'''
            openFlag = self.kcATR()
            self.kcMonitorCount = self.kcMonitorCount + 1
        if self.kcMonitorCount == 10:
            self.kcFlag = False
            self.kcMonitorCount = 1

        if len(self.orderList) == 0:
            # 开仓
            if openFlag and self.pos == 0:
                print openFlag
                self.buyCheck(bar)
            #elif openFlag and 0 < self.pos < self.maxHoldPos and bar.close >= self.profitPrice:
            #    self.buyCheck(bar)
                #print ("多头开仓 f2s夹角:%f,开仓价:%f,min:%s" % (f2sjj, bar.close, bar.datetime.strftime('%H:%M:%S')))
            # 平仓
            if abs(self.pos) > 0 and closeFlag:
                orderID = self.sell(bar.close, abs(self.pos))
                self.orderList.append(orderID)
                self.lastOrderType = 'P'
        if self.pos > 0 and closeFlag:
            self.moveProfitPrice()
        self.putEvent()
        # tickD = copy.deepcopy(tick)
        # saveEntityToMysql(tickD, 'tradeUrl')
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass
    #----------------------------------------------------------------------
    def newDay(self, bar):
        """自然日切换"""
        # 主力合约切换日，重新缓存
        niDay = ['2016/08/03', '2016/11/30', '2017/04/05', '2017/08/07']
        rbDay = ['2016/8/17', '2016/11/28', '2017/3/22', '2017/8/7']
        jDay = ['2016/8/15', '2016/12/1', '2017/3/30', '2017/8/2']
        maDay = ['2016/8/9', '2016/12/1', '2017/4/7', '2017/8/4']
        if bar.symbol == 'NI' and bar.date in niDay:
            self.onInit()
            self.closeHistory = []  # 缓存最新价的数组
            self.output(u'NI自然日切换:'+bar.date)
        elif bar.symbol == 'RB' and bar.date in rbDay:
            self.onInit()
            self.closeHistory = []  # 缓存最新价的数组
            #self.output(u'RB自然日切换:' + bar.date)
        elif bar.symbol == 'J' and bar.date in jDay:
            self.onInit()
            self.closeHistory = []  # 缓存最新价的数组
            self.output(u'J自然日切换:' + bar.date)
        elif bar.symbol == 'MA' and bar.date in maDay:
            self.onInit()
            self.closeHistory = []  # 缓存最新价的数组
            self.output(u'MA自然日切换:' + bar.date)
    # ----------------------------------------------------------------------
    def buyCheck(self, bar):
        """特殊交易日只平仓，不开仓"""
        #最后交易日
        niDay = ['2016/8/3', '2016/11/29', '2017/3/31', '2017/8/4']
        rbDay = ['2016/8/16', '2016/11/25', '2017/3/21', '2017/8/4']
        jDay = ['2016/8/12', '2016/11/30', '2017/3/29', '2017/8/1']
        maDay = ['2016/8/8', '2016/11/30', '2017/4/6', '2017/8/3']
        stopTime = ['0859', '0900', '0901', '0902', '0903', '0904', '0905', '0905',
                  '1445', '1446', '1447', '1448', '1449', '1450', '1451', '1452', '1453', '1454', '1455', '1456', '1457', '1458', '1459',
                  '1115','1116', '1117', '1118', '1119', '1120','1121','1122','1123', '1124','1125', '1126', '1127', '1128', '1129',
                  '1000','1001','1002', '1003', '1004', '1005', '1006', '1007', '1008','1009', '1010', '1011', '1012', '1013', '1014', '1015',
                  '2059', '2100', '2101', '2102', '2103', '2104', '2105', '2105']
        rbStopTime = ['2245', '2246', '2247', '2248', '2249', '2250', '2251', '2252', '2253', '2254', '2255', '2256', '2257', '2258', '2259']
        niStopTime = ['0045', '0046', '0047', '0048', '0049', '0050', '0051', '0052', '0053', '0054', '0055', '0056','0057', '0058', '0059']
        maStopTime = ['2315','2316', '2317', '2318', '2319', '2320','2321','2322','2323', '2324','2325', '2326', '2327', '2328', '2329']
        jStopTime = ['2315', '2316', '2317', '2318', '2319', '2320', '2321', '2322', '2323', '2324', '2325', '2326','2327', '2328', '2329']
        nightHour = ['21','22','23','00']
        mint = bar.datetime.strftime('%H%M')
        xq = bar.datetime.weekday()
        hour = bar.datetime.strftime('%H')

        if bar.date in self.holiday:
            isHoliday = True
        elif bar.symbol == 'NI':
            if bar.date in niDay or mint in niStopTime or mint in stopTime:
                isHoliday = True
            elif xq == 4 and (hour in nightHour):
                isHoliday = True
            else:
                isHoliday = False
        elif bar.symbol == 'RB' or bar.symbol == 'RB0000':
            if bar.date in rbDay or mint in rbStopTime or mint in stopTime:
                isHoliday = True
            elif xq == 4 and (hour in nightHour):
                isHoliday = True
                # self.output('周五：' + bar.datetime.strftime('%Y%m%d-%H%M'))
            else:
                isHoliday = False
        elif bar.symbol == 'J':
            if bar.date in jDay or mint in jStopTime or mint in stopTime:
                isHoliday = True
            elif xq == 4 and (hour in nightHour):
                isHoliday = True
            else:
                isHoliday = False
        elif bar.symbol == 'MA':
            if bar.date in maDay or mint in maStopTime or mint in stopTime:
                isHoliday = True
            elif xq == 4 and (hour in nightHour):
                isHoliday = True
            else:
                isHoliday = False
        elif bar.symbol == 'IF0000':
            if mint in stopTime:
                isHoliday = True
            elif xq == 4 and (hour in nightHour):
                isHoliday = True
            else:
                isHoliday = False

        if not isHoliday:
            orderID = self.buy(bar.close, 1)
            self.orderList.append(orderID)
            self.lastOrderType = 'K'
        # else:
            #self.output('before holiday'+bar.date)

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        if self.lastOrderType == 'K' and self.pos == 1:
            self.openPrice = float(trade.price)  # 锚定开仓价
            self.kCount += 1
            #self.onInit()
            self.kcFlag = False
            self.holdScore = 0
        elif self.lastOrderType == 'P':
            #print ("多头止损成功 开仓价:%f,平仓价%f,min:%s, pos:%d" % (self.openPrice, trade.price, trade.tradeTime, trade.volume))
            if float(trade.price)-self.shortATR <= self.openPrice:
                self.lastLoss += 1
                self.lastProfit = 0
            else:
                self.lastProfit += 1
                self.lastLoss = 0
            self.onInit()
            self.openPrice = EMPTY_FLOAT
            self.holdScore = 0
            self.stopPrice = EMPTY_FLOAT
            self.addPrice = EMPTY_FLOAT
            self.profitPrice = EMPTY_FLOAT
            self.lastOrderType = 'None'
            self.pauseTime = self.cycle
            self.supportPrice = EMPTY_FLOAT
            self.topPrice = EMPTY_FLOAT
            self.lowCount = 0

    # ----------------------------------------------------------------------
    def monitorQuote(self):
        '''长期处于加个底部'''
        #closeArray = np.array(self.closeHistory)
        #fastSMA = ta.SMA(closeArray, timeperiod=self.fastK)
        #k1 = fastSMA[-1] - fastSMA[-2]
        #k2 = fastSMA[-2] - fastSMA[-3]
        '''处于加个顶部'''
        # self.lowPrice = ta.MIN(np.array(self.closeHistory), timeperiod=self.fastK)[-1]
        # self.highPrice = ta.MAX(np.array(self.closeHistory), timeperiod=self.fastK)[-1]
        # diff = self.shortATR * 5
        if float(self.bar.close) == self.lowPrice:
            posleve = 999
        else:
            posleve = abs(self.highPrice - float(self.fastMa0)) / abs(float(self.fastMa0) - self.lowPrice)
        if posleve < 1/9:
            self.kcFlag = True
        #if (self.highPrice - float(self.bar.close)) < self.shortATR and self.highPrice - self.lowPrice > diff:
        #    self.kcFlag = True
    #----------------------------------------------------------------------
    def kcATR(self):
        """进行开仓信号判断"""
        closeArray = np.array(self.closeHistory)

        lastCyc = (self.cycle + 1) * (-1)
        preCyc = (self.cycle * 2 + 1) * (-1)
        # 计算快慢均线
        fastSMA = ta.SMA(closeArray, timeperiod=self.fastK)
        lastCycMax = ta.MAX(fastSMA[lastCyc:-1], timeperiod=self.cycle)[-1]
        preCycMax = ta.MAX(fastSMA[preCyc:lastCyc], timeperiod=self.cycle)[-1]
        lastCycMin = ta.MIN(fastSMA[lastCyc:-1], timeperiod=self.cycle)[-1]
        preCycMin = ta.MIN(fastSMA[preCyc:lastCyc], timeperiod=self.cycle)[-1]
        openFlag = False
        #if lastCycMax > preCycMax and lastCycMin > preCycMin and (self.bar.close - self.bar.open) > self.shortATR:
        if self.highPrice - self.lowPrice > 5*self.shortATR and self.bar.close > self.highPrice:
            openFlag = True
        '''
        if self.lastLoss > 1 and openFlag:
            if (lastCycMax - preCycMax) > self.shortATR * self.lastLoss and (lastCycMin - preCycMin) > self.shortATR * self.lastLoss:
                openFlag = True
            else:
                openFlag = False
        '''
        if openFlag:
            self.topPrice = ta.MAX(closeArray,timeperiod=len(self.closeHistory))[-1]
        return openFlag

    # ----------------------------------------------------------------------
    def monitorPOS(self):
        """持仓监控 持仓健康度"""
        closeArray = np.array(self.closeHistory)
        lastCyc = (self.cycle + 1) * (-1)
        preCyc = (self.cycle * 2 + 1) * (-1)
        self.holdBars += 1
        # 计算快慢均线
        fastSMA = ta.SMA(closeArray, timeperiod=self.fastK)
        lastCycMax = ta.MAX(fastSMA[lastCyc:-1], timeperiod=self.cycle)[-1]
        preCycMax = ta.MAX(fastSMA[preCyc:lastCyc], timeperiod=self.cycle)[-1]
        lastCycMin = ta.MIN(fastSMA[lastCyc:-1], timeperiod=self.cycle)[-1]
        preCycMin = ta.MIN(fastSMA[preCyc:lastCyc], timeperiod=self.cycle)[-1]
        # 趋势分数
        barScore = 0
        if lastCycMax < preCycMax and lastCycMin < preCycMin:
            barScore = barScore - 10
        if lastCycMax > preCycMax and lastCycMin > preCycMin:
            barScore = barScore + 10
        # 盈利分数
        diff1 = fastSMA[-1] - self.openPrice
        #rat = diff1 / self.openPrice * 100 * 10
        barScore = barScore + diff1
        #if self.openPrice > self.bar.close:
        #    barScore = barScore + 10
        # 价格位置分数
        if float(self.fastMa0) == self.lowPrice:
            posleve = 999
        else:
            posleve = abs(self.highPrice - self.fastMa0)/abs(self.fastMa0 - self.lowPrice)
        # 价格超过开仓支撑位分数
        if self.fastMa0 > self.topPrice:
            barScore = barScore + 10
        if self.highPrice-self.lowPrice > 4*self.shortATR:
            if posleve <= 1/19:
                barScore = barScore + 40
            if 1/19 <posleve <= 1/9:
                barScore = barScore + 30
            if 1/9 <posleve <= 1/4:
                barScore = barScore + 20
            if 1/4 < posleve <= 1/2:
                barScore = barScore + 10
            if 1/2 < posleve <= 1:
                barScore = barScore
            if 1 < posleve <= 2:
                barScore = barScore - 20
            if 2 < posleve <= 3:
                barScore = barScore - 30
            if posleve == 999:
                barScore = barScore - 40
        # 价格速度分数
        k1 = fastSMA[-1] - fastSMA[-2]
        k2 = fastSMA[-2] - fastSMA[-3]
        if k2 < 0 and k1 < 0 and k1 < k2-1:
            barScore = barScore - 10
        if self.lastLoss > 1:
            barScore = barScore - 10
        if self.lastProfit > 1:
            barScore = barScore + 10
        if self.holdBars > 60:
            barScore = barScore + 10

        closeFlag = False
                #print ("时间:%s,价差:%f,%f,atr:%f" % (self.bar.datetime.strftime('%Y%m%d-%H%M'), diff,self.holdScore,rat))
        if self.holdScore - barScore > 30:
            closeFlag = True
        self.holdScore = barScore
        if self.holdScore < 0:
            closeFlag = True
        if closeFlag and self.holdBars > 1:
            print ("平仓:%s,位置:%f,分数：%f,价差:%f,持仓周期:%d" % (
                self.bar.datetime.strftime('%Y%m%d-%H%M'), posleve, self.holdScore, diff1, self.holdBars))
            print ("最高:%f,最低：%f,开仓:%f,平仓:%f" % (
                self.highPrice, self.lowPrice, self.openPrice, self.bar.close))
            #print ("平仓时间:%s,位置:%f,分数：%f,开仓价差:%f,持仓周期:d" % (
            #    self.bar.datetime.strftime('%Y%m%d-%H%M'), posleve, self.holdScore, rat, self.holdBars))
        #else:
        #    print ("时间:%s,位置:%f,分数：%f,atr:%f" % (
        #        self.bar.datetime.strftime('%Y%m%d-%H%M'), posleve, self.holdScore, rat))
            # 导数由正变负
        """
        if not closeFlag and self.lastLoss >= 2:
            if self.bar.close < self.openPrice:
                closeFlag = True
        if k1 < 0 and k2 > 0:
            self.lowCount = self.lowCount + 1
            if fastSMA[-1] > self.topPrice:
                self.topPrice = fastSMA[-1]
        """
        return closeFlag
    # ----------------------------------------------------------------------
    def moveProfitPrice(self):
        """持仓监控"""
        # 有持仓的日常维护
        # 长假前清仓
        if self.bar.date in self.holiday and abs(self.pos) > 0 and self.lastOrderType is None:
            if self.bar.high >= self.profitPrice:
                orderID = self.sell(self.bar.close, abs(self.pos))
                self.orderList.append(orderID)
                self.lastOrderType = 'P'
                # print ("长假盈利清仓 时间:%s,价差:%f" % (self.bar.datetime.strftime('%Y%m%d-%H%M'), float(bar.close) - self.openPrice))
            elif self.bar.datetime.strftime('%H%M') == '1449':
                orderID = self.sell(self.bar.close, abs(self.pos))
                self.orderList.append(orderID)
                self.lastOrderType = 'P'
                # print ("长假亏损清仓 时间:%s,价差:%f" % (self.bar.datetime.strftime('%Y%m%d-%H%M'), float(bar.close) - self.openPrice))
        """
        if self.bar.close > self.profitPrice:
            self.moveStopTime += 1
            if self.moveStopTime < 4:
                self.stopPrice = self.stopPrice + 4 * self.lastTAR
            elif 10 > self.moveStopTime >= 4:
                self.stopPrice = self.stopPrice + 2 * self.lastTAR
            elif self.moveStopTime >= 10:
                self.stopPrice = self.stopPrice + 1 * self.lastTAR
            self.profitPrice = self.profitPrice + 4 * self.lastTAR
        """
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass

    def output(self, content):
        """输出内容"""
        print str(datetime.now()) + "\t" + content

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
    initDays = 10   # 初始化数据所用的天数


    #slowK = 10     # 慢速EMA参数
    #offsetK = 50  # 平仓EMA参数
    fastK = 5  # 快速EMA参数
    slowK = 10   # 慢均线倍数    慢均线 = fastK * slowKRate
    profitRate = 20  # 止盈倍数 止盈价 = 1 + moveBase * profitRate * margin * self.contractSize
    offsetRate = 1  # 止损倍数 止损价 = 1 - moveBase * offsetRate * margin * self.contractSize
    addRate = 2
    moveBase = 0.01  # 移动基数
    maxHoldPos = 4  # 最大持仓手数，仓位
    margin = 0.1  # 品种的保证金比例
    # 策略变量
    bar = None
    barMinute = EMPTY_STRING

    closeHistory = []             # 缓存最新价的数组
    lowHistory = []                # 缓存最低价的数组
    highHistory = []  # 缓存最低价的数组
    fastHistory = []
    slowHistory = []
    bidVolumeHistory = []           # 买量
    posMa = []   # 开仓后均线
    holdTimes = 0   # 持仓时间


    minHistroy = 120  # 最少缓存11根开始计算
    maxHistroy = 130  # 最多缓存60根

    fastMa0 = EMPTY_FLOAT   # 当前最新的快速EMA
    fastMa1 = EMPTY_FLOAT   # 上一根的快速EMA

    slowMa0 = EMPTY_FLOAT
    slowMa1 = EMPTY_FLOAT

    volumeFast = 0
    volumeSlow = 0
    #需要重置
    lastOpenPrice = EMPTY_FLOAT
    openPrice = EMPTY_FLOAT  # 开仓价
    stopPrice = EMPTY_FLOAT  # 固定止损价
    pipStopPrice = EMPTY_FLOAT  # 通道止损价
    addPrice = EMPTY_FLOAT  # 加仓价
    lastTAR = EMPTY_FLOAT      # 震荡范围
    preTAR = EMPTY_FLOAT      # 震荡范围
    profitPrice = EMPTY_FLOAT  # 止盈价

    isHoldPos = False        # 持仓标识
    posDirection = None   # 持仓方向
    lastOrderType = 'None'  # 最近一次下单动作 K开仓 J加仓 P平仓 Z 止盈
    orderList = []                      # 保存委托代码的列表
    bigjj = 30
    smalljj = 10
    stopjj = 3

    #策略参数
    kCount = 0  # 开仓次数
    jCount = 0  # 加仓次数
    pCount = 0  # 止损次数
    zCount = 0  # 止盈次数
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'fastK',
                 'slowK',
                 'profitRate',
                 'offsetRate',
                 'addRate',
                 'maxHoldPos',
                 'bigjj',
                 'smalljj',
                 'stopjj',
                 'margin']
    
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
        self.lowHistory = []  # 缓存最低价的数组
        self.highHistory = []  # 缓存最低价的数组
        self.fastHistory = []
        self.slowHistory = []
        self.bidVolumeHistory = []
        self.posMa = []
        #----------------------------------------------------------------------
    def __del__(self, ctaEngine, setting):
        """析构函数"""
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'双EMA演示策略初始化')

        initData = self.loadBar(self.initDays)
        for tick in initData:
            self.onTick(tick)
        #for bar in initData:
        #    self.onBar(bar)

        self.putEvent()

    # ----------------------------------------------------------------------
    def validate(self, bar):
        """数据检验"""
        DAY_START1 = time(9, 01)  # 日盘启动和停止时间
        DAY_END1 = time(10, 14)
        DAY_START2 = time(10, 31)  # 日盘启动和停止时间
        DAY_END2 = time(11, 29)
        DAY_START3 = time(13, 31)  # 日盘启动和停止时间
        DAY_END3 = time(14, 59)

        NIGHT_START = time(21, 01)  # 夜盘启动和停止时间
        NIGHT_END = time(23, 29)

        quoteH = bar.datetime.strftime('%H')
        quoteMin = bar.datetime.strftime('%M')

        bartime = time(int(quoteH), int(quoteMin))
        if self.bar:
            lastbartime = time(int(self.bar.datetime.strftime('%H')), int(self.bar.datetime.strftime('%M')))
            secondDiff = (bar.datetime - self.bar.datetime).seconds
            #if secondDiff > 960:
            #    print ('非序列的数据 %s' % secondDiff)
        if ((bartime >= DAY_START1 and bartime <= DAY_END1) or
                (bartime >= DAY_START2 and bartime <= DAY_END2) or
                (bartime >= DAY_START3 and bartime <= DAY_END3) or
                (bartime >= NIGHT_START) and(bartime <= NIGHT_END)):
            if bar.volume > 150:
                return True
        else:
            #print ('非交易时间的数据 %s' % bar.datetime)
            return False
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'双EMA演示策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        print('开仓：%d ,加仓：%d ,止盈: %d ,止损: %d' % (self.kCount, self.jCount, self.zCount, self.pCount))
        self.writeCtaLog(u'双EMA演示策略停止')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 计算K线
        # 1分钟之内挂单有效期间不做新的判断，避免重复下单
        '''
        if len(self.orderList) == 0:
            if abs(self.pos) < self.maxHoldPos and abs(self.pos) > 0 :
                if self.posDirection == 'D' and self.pos > 0:
                    if tick.lastPrice > self.addPrice:
                        orderID = self.buy(tick.lastPrice, 1)
                        self.orderList.append(orderID)
                        self.lastOrderType = 'J'
                        #print ("多头下加仓单 开仓价:%f,加仓价%f,min:%s" % (self.openPrice, tick.lastPrice, tick.datetime.strftime('%H:%M:%S')))
            # 平仓
            if (tick.lastPrice < self.stopPrice):
                if self.pos > 0:
                    orderID = self.sell(tick.lastPrice, abs(self.pos))
                    self.orderList.append(orderID)
                    self.lastOrderType = 'P'
                    #print ("多头下平仓单 开仓价:%f,平仓价%f,min:%s, pos:%d" % (self.openPrice, tick.lastPrice, tick.datetime.strftime('%H:%M:%S'), self.pos))
            elif tick.lastPrice > self.profitPrice:
                if self.pos == self.maxHoldPos:
                    orderID = self.sell(tick.lastPrice, abs(self.pos))
                    self.orderList.append(orderID)
                    self.lastOrderType = 'Z'
            elif tick.lastPrice < self.offsetMa0:
                if self.pos > 0:
                    orderID = self.sell(tick.lastPrice, abs(self.pos))
                    self.orderList.append(orderID)
                    self.lastOrderType = 'P'
                    print ("多头50日均线下平仓单")
            '''
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
            bar.datetime = tick.datetime    # K线的时间设为第一个Tick的时间
            bar.volume = bar.volume+tick.bidVolume1
            # 实盘中用不到的数据可以选择不算，从而加快速度
            #bar.volume = tick.volume
            #bar.openInterest = tick.openInterest

            self.bar = bar                  # 这种写法为了减少一层访问，加快速度
            self.barMinute = tickMinute     # 更新当前的分钟
        else:                               # 否则继续累加新的K线
            bar = self.bar                  # 写法同样为了加快速度
            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            #bar.datetime = tick.datetime
            bar.close = tick.lastPrice
            bar.volume = bar.volume + tick.bidVolume1
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        for orderID in self.orderList:
            self.cancelOrder(orderID)
            self.orderList = []
        isValidate = self.validate(bar)
        if not isValidate:
            return
        self.bar = bar
        '''准备数据'''
        self.closeHistory.append(float(bar.close))
        self.lowHistory.append(float(bar.low))
        self.highHistory.append(float(bar.high))
        self.bidVolumeHistory.append(float(bar.volume))
        if len(self.closeHistory) < self.minHistroy:
            return
        if len(self.closeHistory) > self.maxHistroy:
            self.closeHistory.pop(0)
            self.lowHistory.pop(0)
            self.highHistory.pop(0)
            self.bidVolumeHistory.pop(0)


        closeArray = np.array(self.closeHistory)
        lowArray = np.array(self.lowHistory)
        highArray = np.array(self.highHistory)
        volumeArray = np.array(self.bidVolumeHistory)

        # 计算快慢均线
        fastSMA = ta.SMA(closeArray, timeperiod=self.fastK)
        slowSMA = ta.SMA(closeArray, timeperiod=self.slowK)

        # 如果有持仓重新记录均线
        lastCyc = (self.fastK+1)*(-1)
        preCyc = (self.fastK*2+1)*(-1)
        lastCycMax = ta.MAX(slowSMA[lastCyc:-1], timeperiod=self.fastK)[-1]
        preCycMax = ta.MAX(slowSMA[preCyc:lastCyc], timeperiod=self.fastK)[-1]
        lastCycMin = ta.MIN(slowSMA[lastCyc:-1], timeperiod=self.fastK)[-1]
        preCycMin = ta.MIN(slowSMA[preCyc:lastCyc], timeperiod=self.fastK)[-1]

        self.lastTAR = ta.ATR(highArray[lastCyc:-1], lowArray[lastCyc:-1], closeArray[lastCyc:-1])[-1]
        self.preTAR = ta.ATR(highArray[preCyc:lastCyc], lowArray[preCyc:lastCyc], closeArray[preCyc:lastCyc])[-1]

        self.fastMa0 = fastSMA[-1]
        self.fastMa1 = fastSMA[-2]
        self.slowMa0 = slowSMA[-1]
        self.slowMa1 = slowSMA[-2]
        '''生成指标'''

        # 上涨趋势
        upQ = closeArray[-1] > closeArray[-2]

        preDiff = self.fastMa1 - self.slowMa1
        curDiff = self.fastMa0 - self.slowMa0
        '''生成开仓，平仓，加仓，止损移动标志位'''
        if self.slowMa0 > self.slowMa1 and self.fastMa0 > self.fastMa1:
            # 斜率
            fastk1 = 1 / (self.fastMa0 - fastSMA[-2])
            # fastk2 = 1 / (self.fastMa1 - fastSMA[-3])
            slwok1 = 1 / (self.slowMa0 - slowSMA[-2])
            # slwok2 = 1 / (self.slowMa1 - slowSMA[-3])
            # 正切值
            # f2ftanx = abs((fastk1 - fastk2)/(1 + fastk1 * fastk2))
            # s2stanx = abs((slwok1 - slwok2)/(1 + slwok1 * slwok2))
            f2stanx = abs((slwok1 - fastk1)/(1 + slwok1 * fastk1))
            # 反正切求夹角
            # f2fjj = round(math.atan(f2ftanx) * 180 / math.pi, 2)
            # s2sjj = round(math.atan(s2stanx) * 180 / math.pi, 2)
            f2sjj = round(math.atan(f2stanx) * 180 / math.pi, 2)

            openFlag = (f2sjj > self.smalljj and f2sjj < self.bigjj and fastk1 > slwok1
                        and self.lastTAR > self.preTAR
                        and lastCycMax > preCycMax and lastCycMin > preCycMin
                        )
        else:
            openFlag = False
        if self.pos > 0:
            if self.fastMa0 == self.fastMa1 and self.slowMa0 != self.slowMa1:
                slwok1 = 1 / (self.slowMa0 - slowSMA[-2])
                f2sjj = round(math.atan(slwok1) * 180 / math.pi, 2)
            elif self.slowMa0 == self.slowMa1 and self.fastMa0 != self.fastMa1:
                fastk1 = 1 / (self.fastMa0 - fastSMA[-2])
                f2sjj = round(math.atan(fastk1) * 180 / math.pi, 2)
            elif self.slowMa0 == self.slowMa1 and self.fastMa0 == self.fastMa1:
                f2sjj = 0
            else:
                # 斜率
                fastk1 = 1 / (self.fastMa0 - fastSMA[-2])
                slwok1 = 1 / (self.slowMa0 - slowSMA[-2])
                f2stanx = abs((slwok1 - fastk1) / (1 + slwok1 * fastk1))
                f2sjj = round(math.atan(f2stanx) * 180 / math.pi, 2)
            closeFlag = bar.close < self.stopPrice and (f2sjj < self.stopjj)
            '''
            closeFlag = (bar.close < self.stopPrice or
                         (lastCycMax < preCycMax and lastCycMin < preCycMin and
                            self.fastMa0 < self.fastMa1)
                         )
            '''
            moveUpPriceFlag = bar.close > self.profitPrice or self.fastMa0 > self.profitPrice
        else:
            closeFlag = False
            moveUpPriceFlag = False

        # 开仓
        if len(self.orderList) == 0:
            # 开仓
            if openFlag and self.pos < self.maxHoldPos:
                orderID = self.buy(bar.close, 1)
                self.orderList.append(orderID)
                self.lastOrderType = 'K'
                #print ("多头开仓 f2s夹角:%f,开仓价:%f,min:%s" % (f2sjj, bar.close, bar.datetime.strftime('%H:%M:%S')))
            '''
            if abs(self.pos) < self.maxHoldPos and abs(self.pos) > 0 :
                if self.posDirection == 'D' and self.pos > 0:
                    if (bar.close > self.addPrice
                            and upQ
                            and not crossDown
                            #and not tGreen
                            and (curDiff >= preDiff)
                            and jU):
                        orderID = self.buy(bar.close, 1)
                        self.orderList.append(orderID)
                        self.lastOrderType = 'J'
                        #print ("2多头下加仓单 开仓价:%f,加仓价%f,min:%s" % (self.openPrice, bar.close, bar.datetime.strftime('%H:%M:%S')))
            '''
            # 平仓
            if abs(self.pos) > 0 and closeFlag and not openFlag:
                orderID = self.sell(bar.close, abs(self.pos))
                self.orderList.append(orderID)
                self.lastOrderType = 'P'
                # print ("1多头下平仓单 开仓价:%f,平仓价%f,min:%s, pos:%d" % (self.openPrice, bar.close, bar.datetime.strftime('%H:%M:%S'), self.pos))
            # 移动止损，止盈
            if moveUpPriceFlag:
                self.stopPrice = self.stopPrice + 4*self.lastTAR
                self.profitPrice = self.profitPrice + 4*self.lastTAR
        # 有持仓的日常维护
            if self.pos > 0:
                self.pipStopPrice = closeArray[-2] - self.lastTAR * 1.5  # 设置止损价
        # 止盈
        # 发出状态更新事件
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        if self.lastOrderType == 'K':
            self.lastOpenPrice = trade.price
            self.posDirection = 'D'
            self.isHoldPos = True
            self.lastOpenPrice = float(trade.price)
            self.openPrice = float(trade.price)  # 锚定开仓价
            #self.stopPrice = float(trade.price) * (1 - self.moveBase * self.offsetRate * self.margin)   # 设置止损价
            self.pipStopPrice = float(trade.price) - self.lastTAR * 1.5  # 设置止损价
            self.stopPrice = float(trade.price) - self.lastTAR * 3  # 设置止损价
            self.addPrice = float(trade.price) * (1 + self.moveBase * self.margin * self.addRate)  # 设置加仓价
            self.kCount += 1
            self.profitPrice = float(trade.price) + self.lastTAR * 4  # 止盈价设定
            #print ("多头开仓成功  开仓价:%f , 加仓价:%f, 平仓价:%f, fast:%f ,slow:%f,  min:%s" % (self.openPrice, self.addPrice, self.stopPrice, self.fastMa0, self.slowMa0, trade.tradeTime))
        elif self.lastOrderType == 'J' and self.pos < self.maxHoldPos:
            self.addPrice = float(trade.price) * (1 + self.moveBase * self.margin * self.addRate)  # 移动加仓价
            addRate = (float(trade.price) - self.lastOpenPrice)/self.lastOpenPrice /self.margin
            if addRate > self.moveBase * self.addRate * 2:
                self.stopPrice = float(trade.price) * (1 - self.moveBase * self.offsetRate * self.margin)  # 移动止损价
            else:
                self.stopPrice = (float(trade.price)*0.6+float(self.lastOpenPrice)*0.4) * (1 - self.moveBase * self.offsetRate * self.margin )  # 移动止损价
            self.lastOpenPrice = float(trade.price)
            self.jCount += 1
            #print ("多头加仓成功  加仓价:%f,下一加仓价:%f, 当前平仓价:%f, min:%s" % (trade.price, self.addPrice, self.stopPrice,trade.tradeTime))
        elif self.lastOrderType == 'J' and self.pos == self.maxHoldPos:
            self.addPrice = (float(trade.price) + self.lastOpenPrice) * 0.5 * (1 + 1.004)  # 移动加仓价
            addRate = (float(trade.price) - self.lastOpenPrice) / self.lastOpenPrice / self.margin
            if addRate > self.moveBase * self.addRate * 2:
                self.stopPrice = round((float(trade.price) * 0.8 + float(self.lastOpenPrice) * 0.2) * (
                    1 - self.moveBase * self.offsetRate * self.margin))+1  # 移动止损价
            elif addRate < self.moveBase * self.addRate:
                self.stopPrice = round((float(trade.price) * 0.55 + float(self.lastOpenPrice) * 0.45) * (
                    1 - self.moveBase * self.offsetRate * self.margin))+1  # 移动止损价
            else:
                self.stopPrice = round((float(trade.price) * 0.65 + float(self.lastOpenPrice) * 0.35) * (
                1 - self.moveBase * self.offsetRate * self.margin))+1  # 移动止损价
            self.profitPrice = float(trade.price) * (1 + self.moveBase * self.profitRate * self.margin)  # 止盈价设定
            #print ("前一开仓价:%f, 加仓价:%f, 止损平仓价:%f,addRate:%f, min:%s" % (self.lastOpenPrice, trade.price, self.stopPrice, addRate, trade.tradeTime))
            self.lastOpenPrice = float(trade.price)
            self.jCount += 1
        elif self.lastOrderType == 'P':
            #print ("多头止损成功 开仓价:%f,平仓价%f,min:%s, pos:%d" % (self.openPrice, trade.price, trade.tradeTime, trade.volume))
            self.posDirection = ''
            self.openPrice = EMPTY_FLOAT
            self.stopPrice = EMPTY_FLOAT
            self.addPrice = EMPTY_FLOAT
            self.profitPrice = EMPTY_FLOAT
            self.isHoldPos = False
            self.pCount += 1
            self.lastOpenPrice = EMPTY_FLOAT
            self.lastOrderType = 'None'
            self.posMa = []
        elif self.lastOrderType == 'Z':
            self.zCount += 1
            #print ("多头止盈成功 开仓价:%f,平仓价%f,min:%s, pos:%d" % (self.openPrice, trade.price, trade.tradeTime, trade.volume))
            self.posDirection = ''
            self.openPrice = EMPTY_FLOAT
            self.stopPrice = EMPTY_FLOAT
            self.addPrice = EMPTY_FLOAT
            self.profitPrice = EMPTY_FLOAT
            self.lastOpenPrice = EMPTY_FLOAT
            self.isHoldPos = False
            self.lastOrderType = 'None'
            self.posMa = []
        pass

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass

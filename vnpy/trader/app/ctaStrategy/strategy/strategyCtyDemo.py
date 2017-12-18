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
import numpy as np
import talib as ta

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
    slowKRate = 2   # 慢均线倍数    慢均线 = fastK * slowKRate
    profitRate = 20  # 止盈倍数 止盈价 = 1 + moveBase * profitRate * margin
    offsetRate = 1  # 止损倍数 止损价 = 1 - moveBase * offsetRate * margin
    moveBase = 0.02  # 移动基数
    maxHoldPos = 4  # 最大持仓手数，仓位
    margin = 0.1  # 品种的保证金比例

    # 策略变量
    bar = None
    barMinute = EMPTY_STRING

    closeHistory = []             # 缓存最新价的数组
    fastHistory = []
    slowHistory = []
    bidVolumeHistory = []           # 买量

    minHistroy = 11  # 最少缓存11根开始计算
    maxHistroy = 60  # 最多缓存60根

    fastMa0 = EMPTY_FLOAT   # 当前最新的快速EMA
    fastMa1 = EMPTY_FLOAT   # 上一根的快速EMA

    slowMa0 = EMPTY_FLOAT
    slowMa1 = EMPTY_FLOAT

    volumeFast = 0
    volumeSlow = 0
    #需要重置
    lastOpenPrice = EMPTY_FLOAT
    openPrice = EMPTY_FLOAT  # 开仓价
    stopPrice = EMPTY_FLOAT  # 止损价
    addPrice = EMPTY_FLOAT  # 加仓价
    profitPrice = EMPTY_FLOAT  # 止盈价

    isHoldPos = False        # 持仓标识
    posDirection = None   # 持仓方向
    lastOrderType = 'None'  # 最近一次下单动作 K开仓 J加仓 P平仓 Z 止盈
    orderList = []                      # 保存委托代码的列表

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
                 'slowKRate',
                 'profitRate',
                 'offsetRate',
                 'moveBase',
                 'maxHoldPos',
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
        self.closeHistory = []
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

        self.closeHistory.append(float(bar.close))
        self.bidVolumeHistory.append(float(bar.volume))
        if len(self.closeHistory) < self.minHistroy:
            return
        if len(self.closeHistory) > self.maxHistroy:
            self.closeHistory.pop(0)
            self.bidVolumeHistory.pop(0)

        closeArray = np.array(self.closeHistory)
        volumeArray = np.array(self.bidVolumeHistory)
        # 计算快慢均线
        fastSMA = ta.SMA(closeArray, self.fastK)
        slowSMA = ta.SMA(closeArray, self.fastK*self.slowKRate)

        self.volumeFast = ta.MA(volumeArray, self.fastK)[-1]
        self.volumeSlow = ta.MA(volumeArray, self.fastK*self.slowKRate)[-1]

        self.fastMa0 = fastSMA[-1]
        self.fastMa1 = fastSMA[-2]
        self.slowMa0 = slowSMA[-1]
        self.slowMa1 = slowSMA[-2]
        # 判断买卖
        # 37.93% 4,244.9，-3,130.81 29笔 开仓：17 ,加仓：12 ,止盈: 5 ,止损: 11  盈利了。。。加仓步长 +0.002 止盈 +0.02
        #crossOver = self.fastMa0 > self.slowMa0 and self.fastMa1 < self.slowMa1 and float(bar.volume) > self.volumeSlow
        # 36% 2,813.45 	-2,885.53 25笔 开仓：15 ,加仓：10 ,止盈: 4 ,止损: 10   盈利了
        #crossOver = self.fastMa0 > self.slowMa30t and self.fastMa1 < self.slowMa30y and bar.volume > self.volumeFast and self.volumeFast > self.volumeSlow
        # 29% 2,050.74 -3,482.14 31笔 开仓：20 ,加仓：11 ,止盈: 4 ,止损: 15
        crossOver = self.fastMa0 > self.slowMa0 and self.fastMa1 < self.slowMa1 and bar.close > self.fastMa0 and float(bar.volume) > self.volumeFast and self.volumeFast > self.volumeSlow
        # 32.14% 2,407.31，-3,409.74 28笔  开仓：19 ,加仓：9 ,止盈: 4 ,止损: 14
        #crossOver = self.fastMa0 > self.slowMa0 and self.fastMa1 < self.slowMa1 and bar.volume > self.volumeFast and self.volumeFast > self.volumeSlow
        crossDown = self.fastMa0 < self.slowMa0 and self.fastMa1 > self.slowMa1 and bar.close < self.fastMa0 and float(bar.volume) < self.volumeFast and self.volumeFast < self.volumeSlow

        # 开仓
        if crossOver:
            # 如果金叉时手头没有持仓，则直接做多
            if self.pos == 0:
                orderID = self.buy(bar.close, 1)
                self.orderList.append(orderID)
                self.lastOrderType = 'K'

        if len(self.orderList) == 0:
            if abs(self.pos) < self.maxHoldPos and abs(self.pos) > 0:
                if self.posDirection == 'D' and self.pos > 0:
                    if bar.close > self.addPrice:
                        orderID = self.buy(bar.close, 1)
                        self.orderList.append(orderID)
                        self.lastOrderType = 'J'
                        # print ("多头下加仓单 开仓价:%f,加仓价%f,min:%s" % (self.openPrice, tick.lastPrice, tick.datetime.strftime('%H:%M:%S')))
            # 平仓
            if (bar.close < self.stopPrice):
                if self.pos > 0:
                    orderID = self.sell(bar.close, abs(self.pos))
                    self.orderList.append(orderID)
                    self.lastOrderType = 'P'
                    # print ("多头下平仓单 开仓价:%f,平仓价%f,min:%s, pos:%d" % (self.openPrice, tick.lastPrice, tick.datetime.strftime('%H:%M:%S'), self.pos))
            elif bar.close > self.profitPrice:
                if self.pos == self.maxHoldPos:
                    orderID = self.sell(bar.close, abs(self.pos))
                    self.orderList.append(orderID)
                    self.lastOrderType = 'Z'
            elif crossDown:
                if self.pos > 0:
                    orderID = self.sell(bar.close, abs(self.pos))
                    self.orderList.append(orderID)
                    self.lastOrderType = 'P'
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
            self.lastOpenPrice = trade.price
            self.openPrice = trade.price  # 锚定开仓价
            self.stopPrice = trade.price * (1 - self.moveBase * self.offsetRate * self.margin)   # 设置止损价
            self.addPrice = trade.price * (1 + self.moveBase * self.offsetRate * self.margin*2)  # 设置加仓价
            self.kCount += 1
            #print ("多头开仓成功  开仓价:%f , 加仓价:%f, 平仓价:%f, fast:%f ,slow:%f,  min:%s" % (self.openPrice, self.addPrice, self.stopPrice, self.fastMa0, self.slowMa0, trade.tradeTime))
        elif self.lastOrderType == 'J' and self.pos < self.maxHoldPos:
            self.addPrice = trade.price * (1 + self.moveBase * self.margin*2)  # 移动加仓价
            self.stopPrice = trade.price * (1 - self.moveBase * self.offsetRate * self.margin)  # 移动止损价
            self.lastOpenPrice = trade.price
            self.jCount += 1
            #print ("多头加仓成功  加仓价:%f,下一加仓价:%f, 当前平仓价:%f, min:%s" % (trade.price, self.addPrice, self.stopPrice,trade.tradeTime))
        elif self.lastOrderType == 'J' and self.pos == self.maxHoldPos:
            self.addPrice = (trade.price + self.lastOpenPrice) * 0.5 * (1 + 1.004)  # 移动加仓价
            self.stopPrice = trade.price * (1 - self.moveBase * self.offsetRate * self.margin)  # 移动止损价
            self.profitPrice = trade.price * (1 + self.moveBase * self.profitRate * self.margin)  # 止盈价设定
            self.lastOpenPrice = trade.price
            self.jCount += 1
            #print ("多头加仓成功  加仓价:%f, 止损平仓价:%f, min:%s" % (trade.price, self.stopPrice, trade.tradeTime))
        elif self.lastOrderType == 'P':
            #print ("多头止损成功 开仓价:%f,平仓价%f,min:%s, pos:%d" % (self.openPrice, trade.price, trade.tradeTime, trade.volume))
            self.posDirection = ''
            self.openPrice = EMPTY_FLOAT
            self.stopPrice = EMPTY_FLOAT
            self.addPrice = EMPTY_FLOAT
            self.profitPrice = EMPTY_FLOAT
            self.isHoldPos = False
            self.pCount += 1
        elif self.lastOrderType == 'Z':
            self.zCount += 1
            #print ("多头止盈成功 开仓价:%f,平仓价%f,min:%s, pos:%d" % (self.openPrice, trade.price, trade.tradeTime, trade.volume))
            self.posDirection = ''
            self.openPrice = EMPTY_FLOAT
            self.stopPrice = EMPTY_FLOAT
            self.addPrice = EMPTY_FLOAT
            self.profitPrice = EMPTY_FLOAT
            self.isHoldPos = False
        self.lastOrderType = 'None'
        pass

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
    
    

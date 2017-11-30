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
    fastK = 5     # 快速EMA参数
    slowK = 10     # 慢速EMA参数
    offsetK = 30  # 平仓EMA参数
    initDays = 10   # 初始化数据所用的天数
    
    # 策略变量
    bar = None
    barMinute = EMPTY_STRING

    posDirection = None              #持仓方向
    closeHistory = []             # 缓存最新价的数组
    fastHistory = []
    slowHistory = []
    minHistroy = 11  # 最少缓存11根开始计算
    maxHistroy = 40  # 最多缓存40根
    fastMa0 = EMPTY_FLOAT   # 当前最新的快速EMA
    fastMa1 = EMPTY_FLOAT   # 上一根的快速EMA

    slowMa0 = EMPTY_FLOAT
    slowMa1 = EMPTY_FLOAT

    slowMa30t = EMPTY_FLOAT
    slowMa30y = EMPTY_FLOAT
    lastOpenPrice = EMPTY_FLOAT
    openPrice = EMPTY_FLOAT  # 开仓价
    stopPrice = EMPTY_FLOAT  # 止损价
    isHoldPos = False        # 持仓标识
    orderList = []                      # 保存委托代码的列表
    
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'fastK',
                 'slowK']    
    
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
        for bar in initData:
            self.onBar(bar)

        self.putEvent()
        
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'双EMA演示策略启动')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'双EMA演示策略停止')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
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
            bar.datetime = tick.datetime    # K线的时间设为第一个Tick的时间
            
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
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        for orderID in self.orderList:
            self.cancelOrder(orderID)
        self.orderList = []
        self.closeHistory.append(float(bar.close))

        if len(self.closeHistory) < self.minHistroy:
            return
        if len(self.closeHistory) > self.maxHistroy:
            self.closeHistory.pop(0)
        closeArray = np.array(self.closeHistory)
        # 计算快慢均线
        fastSMA = ta.SMA(closeArray, self.fastK)
        slowSMA = ta.SMA(closeArray, self.slowK)
        offsetSMA = ta.SMA(closeArray, self.offsetK)
        self.fastMa0 = fastSMA[-1]
        self.fastMa1 = fastSMA[-2]
        self.slowMa0 = slowSMA[-1]
        self.slowMa1 = slowSMA[-2]
        self.slowMa30t = offsetSMA[-1]
        self.slowMa30y = offsetSMA[-2]
        # 判断买卖
        trendsdown = False
        trendsUP = False
        trendsOver = False
        crossOver = self.fastMa0 > self.slowMa30t and self.fastMa1 < self.slowMa30y     # 金叉上穿
       #crossBelow = self.fastMa0 < self.slowMa30t and self.fastMa1 > self.slowMa30y    # 死叉下穿
        if self.posDirection == 'D':
            trendsUP = self.fastMa0 > self.fastMa1   #趋势向上
            if (self.fastMa0 < self.slowMa30t) or ((self.lastOpenPrice - self.fastMa0) > 5):
                trendsOver = True
        elif self.posDirection =='K':
            trendsdown = self.fastMa0 < self.fastMa1 #趋势向下
            trendsOver = self.fastMa0 > self.slowMa30t
        #开仓
        if crossOver:
            # 如果金叉时手头没有持仓，则直接做多
            if self.pos == 0:
                orderID = self.buy(bar.close, 1)
                self.orderList.append(orderID)
                self.lastOpenPrice = bar.close
                self.posDirection = 'D'
                print ("多头开仓  fast:%f ,slow:%f,  min:%s" % (self.fastMa0, self.slowMa0, bar.datetime))
            elif self.pos < 0:
                trendsOver = True
        '''
        # 死叉和金叉相反
        elif crossBelow:
            if self.pos == 0:
                orderID = self.short(bar.close, 1)
                self.orderList.append(orderID)
                self.posDirection = 'K'
                print ("空头开仓 pos == 0  fast:%f ,slow:%f,  min:%s, pos:%d" % (self.fastMa0, self.slowMa0, bar.datetime, self.pos))
            elif self.pos > 0:
                trendsOver = True
        '''
        #加仓
        if abs(self.pos) < 10 and abs(self.pos)>0:
            if trendsUP and self.posDirection == 'D' and self.pos > 0:
                if bar.close > self.lastOpenPrice+2:
                    orderID = self.buy(bar.close, 1)
                    self.orderList.append(orderID)
                    self.lastOpenPrice = bar.close
                #print ("多头加仓 pos > 0  fast:%f ,slow:%f,  min:%s, pos:%d" % (self.fastMa0, self.slowMa0, bar.datetime, self.pos))
            elif trendsdown and self.posDirection == 'K' and self.pos < 0:
                orderID = self.short(bar.close, 1)
                self.orderList.append(orderID)
                #print ("空头加仓 pos < 0  fast:%f ,slow:%f,  min:%s, pos:%d" % (self.fastMa0, self.slowMa0, bar.datetime, self.pos))
        #平仓
        if trendsOver:
            self.posDirection == ''
            if self.pos > 0:
                orderID = self.sell(bar.close, abs(self.pos))
                self.orderList.append(orderID)
                print ("多头平仓 pos > 0  fast:%f ,slow60:%f,  min:%s, pos:%d" % (self.fastMa0, self.slowMa30t, bar.datetime, self.pos))
            elif self.pos < 0:
                orderID = self.cover(bar.close, abs(self.pos))
                self.orderList.append(orderID)
                print ("空头平仓 pos < 0  fast:%f ,slow60:%f,  min:%s, pos:%d" % (self.fastMa0, self.slowMa30t, bar.datetime, self.pos))
        # 金叉和死叉的条件是互斥
        # 所有的委托均以K线收盘价委托（这里有一个实盘中无法成交的风险，考虑添加对模拟市价单类型的支持）
        '''
        if crossOver:
            # 如果金叉时手头没有持仓，则直接做多
            if self.pos == 0:
                self.buy(bar.close, 1)
                self.posDirection = 'D'
                print ("多头开仓  fast:%f ,slow:%f,  min:%s" % (self.fastMa0, self.slowMa0, bar.datetime))
            # 如果有空头持仓，则先平空，再做多
            elif self.pos < 0:
                self.cover(bar.close, abs(self.pos))
                print ("空头平仓反多  fast:%f ,slow:%f,  min:%s, pos:%d" % (self.fastMa0, self.slowMa0, bar.datetime, self.pos))
                self.buy(bar.close, 1)
                self.posDirection = 'K'
            #keyTick = KeyTickData()
            #keyTick.datetime = bar.datetime
            #keyTick.lastPrice = bar.close
            #keyTick.exchange = 'keyQuote crossOver'
            #saveEntityToMysql(keyTick, 'BTI')
            #print ("crossOver  fast:%f ,slow:%f,  min:%s" % (self.fastMa0, self.slowMa0, bar.datetime))
        # 死叉和金叉相反
        elif crossBelow:
            if self.pos == 0:
                self.short(bar.close, 1)
                self.posDirection = 'K'
                print ("空头开仓 pos == 0  fast:%f ,slow:%f,  min:%s, pos:%d" % (self.fastMa0, self.slowMa0, bar.datetime, self.pos))
            elif self.pos > 0:
                self.sell(bar.close, abs(self.pos))
                print ("多头平仓反空 pos > 0  fast:%f ,slow:%f,  min:%s, pos:%d" % (self.fastMa0, self.slowMa0, bar.datetime, self.pos))
                self.posDirection = 'D'
                #self.short(bar.close, 1)
                #keyTick = KeyTickData()
            #keyTick.datetime = bar.datetime
            #keyTick.lastPrice = bar.close
            #keyTick.exchange = 'keyQuote crossBelow'
            #saveEntityToMysql(keyTick, 'BTI')
            #print ("crossBelow  fast:%f ,slow:%f,  min:%s" % (self.fastMa0, self.slowMa0, bar.datetime))
        if abs(self.pos) < 10:
            if trendsUP:
                if self.pos > 0 and self.posDirection == 'D':
                    self.buy(bar.close, 1)
                    print ("多头加仓 pos > 0  fast:%f ,slow:%f,  min:%s, pos:%d" % (self.fastMa0, self.slowMa0, bar.datetime, self.pos))
            elif trendsdown:
                if self.pos < 0 and self.posDirection == 'K':
                    self.short(bar.close, 1)
                    print ("空头加仓 pos > 0  fast:%f ,slow:%f,  min:%s, pos:%d" % (self.fastMa0, self.slowMa0, bar.datetime, self.pos))
        # 发出状态更新事件
        '''
        # print(self.pos)
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
        pass
    
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
    
    

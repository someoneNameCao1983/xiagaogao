# encoding: UTF-8

"""
展示如何执行参数优化。
"""

from __future__ import division
from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, OptimizationSetting
from time import time


if __name__ == '__main__':
    from vnpy.trader.app.ctaStrategy.strategy.strategyCtyDemo import CtyEmaDemoStrategy
    start = time()

    # 创建回测引擎
    engine = BacktestingEngine()
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.TICK_MODE)
    # engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期 tick data no need initDay
    engine.setStartDate('20170901', initDays=1)
    # engine.setStartDate('20100101', initDays=1)
    # 设置产品相关参数
    engine.setSlippage(0.2)  # 滑点
    engine.setRate(5 / 10000)  # 万5
    engine.setSize(10)  # 合约大小
    engine.setPriceTick(1)  # 股指最小价格变动
    # 设置使用的历史数据库
    engine.setDatabase(TICK_DB_NAME, 'rb18012')
    # engine.setDatabase(TICK_DB_NAME, 'rb1801')
    # engine.setDatabase(MINUTE_DB_NAME, 'IF0000')
    # 跑优化
    setting = OptimizationSetting()  # 新建一个优化任务设置对象
    setting.setOptimizeTarget('capital')  # 设置优化排序的目标是策略净盈利
    setting.addParameter('fastK', 9)  # 增加第一个优化参数atrLength，起始12，结束20，步进2
    setting.addParameter('profitRate', 20, 50, 2)  # 增加第二个优化参数atrMa，起始20，结束30，步进5
    setting.addParameter('slowKRate', 2)  # 增加一个固定数值的参数
    # 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    # 测试时还跑着一堆其他的程序，性能仅供参考
    # 运行单进程优化函数，自动输出结果，耗时：359秒
    # engine.runOptimization(AtrRsiStrategy, setting)

    # 多进程优化，耗时：89秒
    engine.runParallelOptimization(CtyEmaDemoStrategy, setting)

    print u'运算完毕，耗时：%s' % (time() - start)
#!/usr/bin/python
# -*- coding: utf-8 -*-
#controller.py
import copy, datetime
import dataListener, strategyActuator
from DataApi_32 import CDataProcess
#载入策略
import signalStrategy, multipleStrategy
#-----------------------
#定义全局变量
#-----------------------
#数据监听对象
g_listenerList = []			#总共3个对象
#策略执行器对象列表
g_StrategyActuatorDict = {}	#每个股票一个对象
#订阅股票列表
g_subStocks = []
#信号堆栈
g_messageBox = []
#订阅单策略
SUB_SIGNALS = ["baseSignal"]
#订阅多策略
SUB_MULTIPLES = ["baseMultiple"]
#-----------------------
#注册策略
#-----------------------
#单只股票策略对象池
g_SSDict = {}
g_SSDict["baseSignal"] = signalStrategy.CBaseSignal
#多只股票策略对象池
g_MSDict = {}
g_MSDict["baseMultiple"] = multipleStrategy.CBaseMultiple
#-----------------------
#实现函数
#-----------------------
#读取设置参数
execfile("config.ini")
#读取订阅股票
def loadSubStocks():
	global g_subStocks
	_fileReader  = open("./subStock.csv","r")
	while 1:
		line = _fileReader.readline()
		line = line.replace("\n","")
		if not line:
			break
		g_subStocks.append(line)
#创建策略对象
def creatStrategyObject(needSignal, stock):
	strategyObjDict = {}
	if needSignal:	#单信号策略
		if not SUB_SIGNALS:		#如果没有订阅
			return False
		for signalName in SUB_SIGNALS:
			strategyObjDict[signalName] = g_SSDict[signalName](stock, g_messageBox)
		return strategyObjDict
	else:			#多信号策略
		if not SUB_MULTIPLES:	#如果没有订阅
			return False
		for multipeName in SUB_MULTIPLES:
			strategyObjDict[multipeName] = g_MSDict[multipeName]("Multiple", g_messageBox)
			strategyObjDict[multipeName].getActuatorDict(g_StrategyActuatorDict)
		return strategyObjDict
#创建监听对象
def creatListener(bufferStack):
	global g_listenerList
	listenersNum = 1
	if len(g_subStocks) >= listenersNum:
		perListenerStocksNum = len(g_subStocks)/listenersNum
		for i in xrange(listenersNum):
			if listenersNum - i == 1:
				actuatorDict = creatActuators(g_subStocks[i*perListenerStocksNum:], bufferStack, True)
				listener = dataListener.CDataListerner(g_subStocks[i*perListenerStocksNum:], actuatorDict, bufferStack)
				listener.start()
			else:
				actuatorDict = creatActuators(g_subStocks[i*perListenerStocksNum:i*perListenerStocksNum+perListenerStocksNum], bufferStack, False)
				listener = dataListener.CDataListerner(g_subStocks[i*perListenerStocksNum:i*perListenerStocksNum+perListenerStocksNum], actuatorDict, bufferStack)
				listener.start()
			g_listenerList.append(listener)
	else:
		actuatorDict = creatActuators(g_subStocks, bufferStack, True)
		listener = dataListener.CDataListerner(g_subStocks, actuatorDict, bufferStack)
		listener.start()
		g_listenerList.append(listener)
#创建监听对象
def creatActuators(stocks, bufferStack, isLast):
	global g_StrategyActuatorDict
	actuatorDict = {}
	#单股票策略监听
	for stock in stocks:
		strategyObjDict = creatStrategyObject(True, stock)
		if strategyObjDict:
			newActuator						= strategyActuator.CStrategyActuator(bufferStack[stock])
			newActuator.getSignalStrategyObj(strategyObjDict)
			g_StrategyActuatorDict[stock]	= newActuator
			actuatorDict[stock] 			= newActuator
	if isLast:	#多股票策略监听
		strategyObjDict = creatStrategyObject(False, "Multiple")
		if strategyObjDict:
			newActuator							= strategyActuator.CStrategyActuator(bufferStack["Multiple"])
			newActuator.getmultipleStrategyObj(strategyObjDict)
			g_StrategyActuatorDict["Multiple"]	= newActuator
			actuatorDict["Multiple"] 			= newActuator
	return actuatorDict
#主入口
def main(messageBox):
	global g_messageBox
	g_messageBox = messageBox
	#注册策略
	#载入订阅股票代码
	loadSubStocks()
	#创建数据连接对象
	dataServerInstance = CDataProcess(
		HOST,PORT,
		SUB_ALL_STOCK, g_subStocks,
		REQUEST_TYPE,
		REQUEST_FLAG,
		datetime.datetime.strptime(START_TIME,"%Y-%m-%d %H:%M:%S"),
		datetime.datetime.strptime(END_TIME,"%Y-%m-%d %H:%M:%S"))
	#创建数据监听器
	creatListener(dataServerInstance.bufferStack)
	dataServerInstance.run()
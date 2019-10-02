# -*- coding: utf-8 -*-
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
open_= pd.to_datetime("9:05:00")                                               #设定开盘价，收盘价的时间
close_ = pd.to_datetime("15:00:00")
all_close,all_high,all_low = {},{},{}
data_file_content = pd.read_csv('D:/5min-tick-2016-01-06-rb0001.csv')          
data_file_content['Date'] = [datetime.strptime(dateTimeStr, '%Y.%m.%d %H:%M:%S') for dateTimeStr in
                                     (data_file_content.Date + ' ' + data_file_content.Time)]
data_file_content.drop(['Time'], axis=1, inplace=True)
data_file_content.rename(columns={'Date': 'Datetime'}, inplace=True)
time_frame = data_file_content['Datetime'].tolist
data_file_content.set_index(data_file_content['Datetime'],inplace=True)
data_file_content['profit'] = 0
break_buy,observe_sell,reverse_sell,reverse_buy,observe_buy,break_sell = {}, {}, {}, {}, {}, {},          #构造六项突破指标
for i in data_file_content['Datetime']:    
    Pivot= (data_file_content.loc[i]['High']+ data_file_content.loc[i]['Low']+ data_file_content.loc[i]['Close'])/3
    break_buy[i] = data_file_content.loc[i]['High']+2*(Pivot- data_file_content.loc[i]['Low'])
    observe_sell[i]=Pivot+ data_file_content.loc[i]['High']- data_file_content.loc[i]['Low']
    reverse_sell[i]=2*Pivot- data_file_content.loc[i]['Low']
    reverse_buy[i]=2*Pivot- data_file_content.loc[i]['High']
    observe_buy[i]=Pivot- data_file_content.loc[i]['High']+ data_file_content.loc[i]['Low']
    break_sell[i]= data_file_content.loc[i]['Low']+2*( data_file_content.loc[i]['High']-Pivot)       #将每日的六项指标转化为dataframe格式，便于之后调用
break_buy = pd.Series(break_buy)
observe_sell = pd.Series(observe_sell)
reverse_sell = pd.Series(reverse_sell)
reverse_buy = pd.Series(reverse_buy)
observe_buy =pd.Series(observe_buy)
break_sell = pd.Series(break_sell)
index_data= pd.concat([break_buy,observe_sell,reverse_sell,reverse_buy,observe_buy,break_sell],axis = 1)
index_data.columns = ['break_buy','observe_sell','reverse_sell','reverse_buy','observe_buy','break_sell']                            #六项指标构造完成
sell_rate = 1
buy_rate = 1
withdraw_rate = 0.4
total_proift = []
minute_proift = {}
money = 1e+6
stock_number = 0
base_price = 100000                                            #数据回测函数，假定交易成本为万分之一
observe = 'Wait'                                                          #初始观察状态为wait
for i in range(9981):
    observe = 'Wait'
    if data_file_content.iloc[i+1].loc['Close'] >= index_data.iloc[i].loc['break_buy']:
        stock_number += int(money*buy_rate/index_data.iloc[i].loc['break_buy']/(1+0.0001))
        money -= int(money*buy_rate/(index_data.iloc[i].loc['break_buy']/(1+0.0001)))*(index_data.iloc[i].loc['break_buy']*(1+0.0001))
    elif data_file_content.iloc[i+1].loc['Close'] <= index_data.iloc[i].loc['break_sell']:           #突破时卖出，同时观察状态变为wait
        observe = 'Wait' 
        money += sell_rate*stock_number*(index_data.iloc[i].loc['break_sell']*(1-0.0001))
        stock_number = (1-sell_rate)*stock_number
    elif observe == 'Buy':                                                 #在观察区间的时候，如果是买入观察期，那么超过翻转买入就买，如果同时突破了观察卖出指标，观察状态改为sell
        if data_file_content.iloc[i+1].loc['Close'] >= index_data.iloc[i].loc['reverse_buy']:
            if data_file_content.iloc[i+1].loc['Close'] >= index_data.iloc[i].loc['observe_sell']:
                observe = 'Sell'
                stock_number += int(money*buy_rate/index_data.iloc[i].loc['reverse_buy']/(1+0.0001))
                money -= int(money*buy_rate/(index_data.iloc[i].loc['reverse_buy']/(1+0.0001)))*(index_data.iloc[i].loc['reverse_buy']*(1+0.0001))
            else:
                observe = 'Wait'
                stock_number = stock_number + int(money*buy_rate/(index_data.iloc[i].loc['reverse_buy']/(1+0.0001)))
                money -= int(money*buy_rate/(index_data.iloc[i].loc['reverse_buy']/(1+0.0001)))*(index_data.iloc[i].loc['reverse_buy']*(1+0.003))
        else:
            continue  
    elif observe == 'Sell':                                                #在观察区间的时候，如果是卖出观察期，那么超过翻转卖出就卖，如果同时突破了观察买入指标，观察状态改为buy
        if data_file_content.iloc[i+1].loc['Close'] <= index_data.iloc[i].loc['reverse_sell']:
            if data_file_content.iloc[i+1].loc['Close'] <= index_data.iloc[i].loc['observe_buy']:
                observe = 'Buy'
                money += sell_rate*stock_number*(index_data.iloc[i].loc['reverse_sell']*(1-0.0001))
                stock_number = stock_number*(1-sell_rate)
            else:
                observe = 'Wait'
                money += sell_rate*stock_number*(index_data.iloc[i].loc['reverse_sell']*(1-0.0001))
                stock_number = stock_number*(1-sell_rate)    
        else:
            continue 
    elif observe == 'Wait':                                                #没直接买入卖出而又不处于观察期的时候，判断是否能够进入观察期
        if data_file_content.iloc[i+1].loc['Close'] <= index_data.iloc[i].loc['observe_buy']:
            observe = 'Buy'
        elif data_file_content.iloc[i+1].loc['Close'] >= index_data.iloc[i].loc['observe_sell']:
            observe = 'Sell'
        else:
            continue
    else:
        continue    
    profit = money + stock_number*data_file_content.iloc[i+1].loc['Close'] 
    data_file_content.iloc[i+1][4] = profit                                #每天的交易如果立刻结算后的价格
#print(minute_proift)
#minute_proift_frame = pd.DataFrame(minute_proift,fill_value=None)
#money += stock_number*2259*(1-0.001)
print('总资金：'+str(money)+'总持仓量：' + str(stock_number))                   #打印总资产          #突破时买入,同时观察状态变为wait      
data_file_content.plot()
#a = plt.scatter(data_file_content['Datetime'],data_file_content['profit'],s=5,color='blue',alpha=0.5)
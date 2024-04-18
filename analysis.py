import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from _datetime import datetime
plt.style.use('ggplot')
plt.rcParams['font.sans-serif'] = ['SimHei']

columns = ['user_id','order_dt','order_products','order_amount']
df = pd.read_table('CDNOW_master.txt', names=columns, sep='\s+')

df['order_data'] = pd.to_datetime(df['order_dt'], format='%Y%m%d')
df['month'] = df['order_data'].astype('datetime64[M]')

'''
#用户整体消费分析（按月份）
#按月份统计产品购买数量、消费金额、消费次数、消费人数
plt.figure(figsize=(15,10))
#每月的产品购买数量
plt.subplot(221)
df.groupby(by='month')['order_products'].sum().plot()
plt.title('每月的产品购买数量')
#每月的消费金额
plt.subplot(222)
df.groupby(by='month')['order_amount'].sum().plot()
plt.title('每月的消费金额')
#每月的消费次数
plt.subplot(223)
df.groupby(by='month')['user_id'].sum().plot()
plt.title('每月的消费次数')
#每月的消费人数（去重统计，再计算个数）
plt.subplot(224)
df.groupby(by='month')['user_id'].apply(lambda x:len(x.drop_duplicates())).plot()
plt.title('每月的消费人数')
plt.show()
'''

'''
#用户个体消费分析
#1.用户消费金额，消费次数描述统计
user_grouped = df.groupby(by='user_id').sum()
print(user_grouped.describe())
print('用户数量:',len(user_grouped))

#绘制每个用户的产品购买量和消费金额散点图
df.plot(kind='scatter', x='order_products',y='order_amount')
plt.show()
'''

'''
#用户消费分布图
plt.figure(figsize=(12,4))
plt.subplot(121)
plt.xlabel('每个订单的消费金额')
df['order_amount'].plot(kind='hist',bins=50)

plt.subplot(122)
plt.xlabel('每个用户购买的数量')
df.groupby(by='user_id')['order_products'].sum().plot(kind='hist',bins=50)
plt.show()
'''

'''
#用户个体消费分析
user_cumsum = df.groupby(by='user_id')['order_amount'].sum().sort_values().reset_index()
user_cumsum['amount_cumsum'] = user_cumsum['order_amount'].cumsum()

amount_total = user_cumsum['amount_cumsum'].max()
user_cumsum['prop'] = user_cumsum.apply(lambda x:x['amount_cumsum']/amount_total,axis=1)
user_cumsum['prop'].plot()
plt.show()
'''

'''
#用户消费行为分析
#df.groupby(by='user_id')['order_data'].min().value_counts().plot()

df.groupby(by='user_id')['order_data'].max().value_counts().plot()
plt.show()
'''

'''
#构建RFM模型
rfm = df.pivot_table(index='user_id',
                     values=['order_products','order_amount','order_data'],
                     aggfunc={
                        'order_data':'max',#最后一次购买
                        'order_products':'sum',#购买产品的总数量
                        'order_amount':'sum'
                     })
rfm['R'] = -(rfm['order_data']-rfm['order_data'].max())/np.timedelta64(1,'D')
rfm.rename(columns={'order_products':'F','order_amount':'M'},inplace=True)

def frm_func(x):
    level = x.apply(lambda x:'1' if x>=1 else '0')
    label = level['R']+level['F']+level['M']
    d = {
        '111':'重要价值客户',
        '011':'重要保持客户',
        '101':'重要发展客户',
        '001':'重要挽留客户',
        '110':'一般价值客户',
        '010':'一般保持客户',
        '100':'一般发展客户',
        '000':'一般挽留客户'

    }
    result = d[label]
    return result

rfm['label'] = rfm[['R','F','M']].apply(lambda x:x-x.mean()).apply(frm_func,axis=1)
print(rfm)
#rfm可视化
for label,grouped in rfm.groupby(by='label'):
    x = grouped['F']
    y = grouped['R']
    plt.scatter(x,y,label=label)
plt.legend()
plt.xlabel('F')
plt.ylabel('R')
plt.show()
'''

'''
#基于rfm模型进行用户回流分析
pivoted_counts = df.pivot_table(
    index = 'user_id',
    columns = 'month',
    values = 'order_dt',
    aggfunc = 'count'
).fillna(0)
df_purchase = pivoted_counts.applymap(lambda x:1 if x>0 else 0)

def active_status(data):
    status = []   #负责存储18个月的状态
    for i in range(18):
        if data[i] == 0:
            if len(status) == 0:
                status.append('unreg')
            else:
                if status[i-1] == 'unreg':
                    status.append('unreg')
                else:
                    status.append('unactive')
            pass
        else:
            if len(status) == 0:
                status.append('new')
            else:
                if status[i-1] == 'unactive':
                    status.append('return')
                elif status[i-1] == 'unreg':
                    status.append('new')
                else:
                    status.append('active')
    return pd.Series(status,df_purchase.columns)
purchase_status = df_purchase.apply(active_status, axis=1)
purchase_status_ct = purchase_status.replace('unreg',np.NaN).apply(lambda x:pd.value_counts(x))
#purchase_status_ct.T.fillna(0).plot.area()
#回流用户占比
rate = purchase_status_ct.T.fillna(0).apply(lambda x: x/x.sum() ,axis=1)

plt.plot(rate['return'],label='return')
plt.plot(rate['active'],label='active')
plt.legend()
plt.show()
'''

'''
#计算用户购买周期
order_diff = df.groupby(by='user_id').apply(lambda x:x['order_data']-x['order_data'].shift())
#print(order_diff.describe())
(order_diff/np.timedelta64(1,'D')).hist(bins = 20)
plt.show()
'''

'''
#计算用户生命周期
user_life = df.groupby('user_id')['order_data'].agg(['min','max'])
(user_life['max']==user_life['min']).value_counts().plot.pie(autopct='%1.1f%%')
plt.legend(['仅消费一次','多次消费'])
#print((user_life['max']-user_life['min']).describe())
plt.figure(figsize=(12,6))
plt.subplot(121)
((user_life['max']-user_life['min'])/np.timedelta64(1,'D')).hist(bins=15)
plt.title('所有用户生命周期直方图')
plt.xlabel('生命周期天数')
plt.ylabel('用户人数')

plt.subplot(122)
u_1 = (user_life['max']-user_life['min']).reset_index()[0]/np.timedelta64(1,'D')
u_1[u_1>0].hist(bins=15)
plt.title('多次消费的用户生命周期直方图')
plt.xlabel('生命周期天数')
plt.ylabel('用户人数')
plt.show()
'''


#复购率分析
pivoted_counts = df.pivot_table(
    index = 'user_id',
    columns = 'month',
    values = 'order_dt',
    aggfunc = 'count'
).fillna(0)
purchase_r = pivoted_counts.applymap(lambda x:1 if x>1 else np.NaN if x==0 else 0)
#print(purchase_r)
#(purchase_r.sum()/purchase_r.count()).plot(figsize=(12,6))
#plt.show()


#回购率分析
pivoted_counts = df.pivot_table(
    index = 'user_id',
    columns = 'month',
    values = 'order_dt',
    aggfunc = 'count'
).fillna(0)
df_purchase = pivoted_counts.applymap(lambda x:1 if x>0 else 0)

def purchase_back(data):
    status = []
    #1:回购用户  0：非回购用户（当月消费了，下个月未消费）    NaN：当前月份未消费
    for i in range(17):
        if data[i] == 1:
            if data[i+1]==1:
                status.append(1)  #h回购用户
            elif data[i+1] == 0:
                status.append(0)
        else:
            status.append(np.NaN)
    status.append(np.NaN)
    return pd.Series(status,df_purchase.columns)

purchase_b = df_purchase.apply(purchase_back,axis=1)
plt.figure(figsize=(10,5))
#(purchase_b.sum()/purchase_b.count()).plot(label='回购率')
#(purchase_r.sum()/purchase_r.count()).plot(label='复购率')
#plt.legend()
#plt.ylabel('百分比%')
#plt.title('用户回购率和复购率对比图')

plt.plot(purchase_b.sum(),label='回购人数')
plt.plot(purchase_b.count(),label='购物总人数')
plt.xlabel('month')
plt.ylabel('人数')
plt.legend()
plt.show()

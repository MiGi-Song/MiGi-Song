import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
#import datetime # 加天數 酷! datetime.timedelta(days=1) 但本篇不會用到!!!資料並沒有連續每一天都有!!!交易日也有休市日QQ

### 7/9.波動度高低無法作動量策略!
### f,h : 在看 re 和 std 時，應該可以各自使用不同 f ? 值得嘗試
### 也許可以做 把公司所有會計數據資料做成動量策略 ?

df = pd.read_excel("C:/Users/User/Desktop/台股總報酬.xlsx")  # file path is the data we have collected before.
# print(df) # df也就是下面的資料，每隻台灣各股的每日收盤價報酬
#          Date      1101      1102      1103      1104      1108      1109  ...      9942      9943      9944      9945      9946      9955      9958
#0   2017-01-04  0.002845 -0.005660 -0.004592  0.000000 -0.002186  0.000000  ... -0.006024  0.001961 -0.009524  0.002721  0.009346  0.000000 -0.001036
#1   2017-01-05  0.000000  0.005693  0.001153  0.002032  0.006572 -0.002000  ... -0.007273 -0.001957  0.009615  0.001357  0.004630  0.012579  0.005187
#2   2017-01-06  0.000000  0.000000 -0.003456 -0.006085 -0.004353  0.002004  ...  0.018315 -0.003922 -0.009524  0.005420  0.000000  0.012422 -0.006192
..         ...       ...       ...       ...       ...       ...       ...  ...       ...       ...       ...       ...       ...       ...       ...
#724 2019-12-26 -0.001160  0.001058  0.033654 -0.007792  0.008783  0.002660  ...  0.000000  0.004219  0.002916 -0.001106 -0.011029  0.008086 -0.006887
#725 2019-12-27  0.004646  0.008457  0.023256  0.007853  0.009950  0.010610  ...  0.001429  0.002801  0.002907  0.005537  0.001859 -0.005348  0.000000
#726 2019-12-30  0.009248  0.009434  0.034091  0.005195  0.054187  0.099738  ...  0.000000 -0.001397  0.000000  0.002203  0.011132  0.008064  0.002774

# 先創造dataframe，以方便之後清晰處理我們計算的數據。
dfre = pd.DataFrame(df['Date'])  # 用來存取形成期報酬的平均
dfstd = pd.DataFrame(df['Date']) # 用來存取形成期報酬的標準差
factors_re = pd.DataFrame(df['Date']) # 用來存取篩選後的投組報酬

col = df.columns
col = list(col)
del col[0] # 因為col[0]是'Date'

f = 20  # formation period 形成期
h = 5  # holding period 持有期
b = 0.3 # break: b=0.1的話，取整體排序後的前十分之一及後十分之一作為買賣投組
for i in col:
    dfre[f'{i}']=df[f'{i}'].rolling(window=f).mean() # 計算滾動報酬平均
    dfstd[f'{i}']=df[f'{i}'].rolling(window=f).std() # 計算滾動報酬標準差

del dfre['Date']  # 因為在 下面的迴圈排序時，Date資料也會被抓取進入排序(ERROR)，所以先刪掉Date 
del dfstd['Date']
end = len(dfre)+1
for i in range(f-1,end-h):
    sorted_re = dfre.loc[i].sort_values().dropna().index  # 這裡，會抓整個列(同一時間的報酬做排序)
    sorted_std = dfstd.loc[i].sort_values().dropna().index
    num = int(len(sorted_re)*b) # 買賣投組的各自股票數量，b=0.1為前十分之一與後十分之一的概念
    low_re = sorted_re[0:num] # 取出排序後的前面與後面的股票代碼
    high_re = sorted_re[len(sorted_re)-num:]
    low_std = sorted_std[0:num]
    high_std = sorted_std[len(sorted_std)-num:]
    # 交集，可能有交集會是0，
    lr_ls = set(low_re) & set(low_std) # 取股票代碼有交集的
    lr_hs = set(low_re) & set(high_std)
    hr_ls = set(high_re) & set(low_std)
    hr_hs = set(high_re) & set(high_std)
    factors = {'low_re': low_re, 'high_re': high_re, 'low_std': low_std, 'high_std': high_std, 'lr_ls':lr_ls, 'lr_hs':lr_hs, 'hr_ls':hr_ls, 'hr_hs':hr_hs} 
    for x in factors.keys(): # 把每個投組在每個時間點都計算報酬
        ret = df[factors[f'{x}']].iloc[i+1:i+1+h]
        ret_sum = ret.sum()
        total_re = ret_sum.mean()
        factors_re.at[i,f'{x}'] = total_re
#print(len(lr_ls),len(lr_hs),len(hr_ls),len(hr_hs)) # 可以看投組裡有幾家公司
# 零成本投組 : 買 high 賣 low，
factors_re['zero_re'] = factors_re['high_re']-factors_re['low_re']
#factors_re['zero_std'] = factors_re['high_std']-factors_re['low_std'] # 很爛
factors_re['zero_hrhs_lrhs'] = factors_re['hr_hs']-factors_re['lr_hs'] # 挺強的

# 大盤表現: 
import yfinance as yf
tw = yf.download('0050.TW',interval='1d',start='2017-01-01',end='2019-12-31') #這裡時間要跟隨當初台股橫切面的data period
t = tw.Close
tr = t /t.shift(1) - 1
tr = tr.dropna()
tr.name='0050'
for i in range(f-1,end-h):
    ttre = tr[i+1:i+1+h]
    tt = ttre.sum()
    factors_re.at[i,'0050'] = tt

# 做累積報酬率
port =list(factors_re.columns)
del port[0] # similarly, remove the 'Date', cause we need the list 'port' to run the roop.
n = len(factors_re)
for p in port:
    for i in range(0,n):
        cum_re = factors_re[p].iloc[0:i+1]
        factors_re.at[i,f'{p}_cum']=cum_re.sum()
        
# 設日期為索引，等一下製圖時，橫軸才為日期。
factors_re.set_index(pd.to_datetime(factors_re['Date'],format='%Y/%m%d'),inplace=True)
#factors_re = factors_re.dropna()  # 看需求，不刪除缺失值對後續製圖也沒影響。

# 畫累積報酬率圖 做比較: 
plt.figure(figsize=(12,5))
plt.plot(factors_re['0050_cum'], 'r', label='0050_cum')
plt.plot(factors_re['zero_re_cum'], 'b',label='zero_re_cum') # 'b'為藍色；其他還有'r',k','y','m','c'。
plt.plot(factors_re['zero_hrhs_lrhs_cum'], 'k', label='zero_hrhs_lrhs_cum')
#plt.plot(factors_re['high_std_cum'], 'k', label='high_std_cum')
#plt.plot(factors_re['low_std_cum'], 'y', label='low_std_cum')
#plt.plot(factors_re['lr_ls_cum'], 'k', label='lr_ls_cum')
#plt.plot(factors_re['lr_hs_cum'], 'y', label='lr_hs_cum')
#plt.plot(factors_re['hr_ls_cum'], 'm', label='hr_ls_cum')
#plt.plot(factors_re['hr_hs_cum'], 'c', label='hr_hs_cum')
#plt.xticks(factors_re.index,rotation='vertical') # vertical使時間的數字以垂直方式顯示在圖表上，才不會擠在一起
plt.title(f'MOM_f{f}h{h}_b{b}')
plt.legend(loc = 'lower left') #圖例在左下方
plt.show()

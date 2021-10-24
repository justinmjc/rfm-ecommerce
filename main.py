import pandas as pd
import numpy as np
import os
import warnings
import missingno as msno
from pyecharts.charts import Grid, Pie, Bar
from pyecharts import options as opts

warnings.filterwarnings('ignore')

def readdata():
    data = pd.read_csv('dataset/data.csv',encoding = 'ISO-8859-1',sep=',')
    # print(data.info())
    # 将客户ID修改成字符型
    data['CustomerID'] = pd.DataFrame(data['CustomerID'], dtype=np.object)
    # 将日期修改成日期格式
    data['InvoiceDate'] = pd.to_datetime(data['InvoiceDate'], format='%m/%d/%Y %H:%M')
    # 删除客户ID为空的行
    data = data.dropna(subset=['CustomerID'])
    # print(data.info())
    data['Price'] = data['Quantity'] * data['UnitPrice']
    data['Year'] = data['InvoiceDate'].dt.year
    data['Month'] = data['InvoiceDate'].dt.month
    data['Day'] = data['InvoiceDate'].dt.day
    data['Week'] = data['InvoiceDate'].dt.dayofweek
    rfmmodel(data)



def rfmmodel(data):
    # 数据集最后的开票日期：
    end_Time = max(data['InvoiceDate'].unique())
    # 截止日期格式化
    end_Time = pd.to_datetime(end_Time, format='%m/%d/%Y %H:%M')
    # F计算
    df_F = data.groupby('CustomerID')['InvoiceNo'].agg([('Frequency', 'count')])
    # M计算
    df_M = data.groupby('CustomerID')['Price'].agg([('Monetary', sum)])

    # 计算每个客户的最近一次消费日期
    df_R = data.groupby('CustomerID')['InvoiceDate'].agg([('最近一次消费', max)])
    # 增加一列截止日期
    df_R['截止日期'] = end_Time
    # 计算截止日期与最后一次消费的天数
    df_R['Recency'] = (df_R['截止日期'] - df_R['最近一次消费']).apply(lambda x: x.days)
    # 重命名字段
    df_R = pd.DataFrame(df_R, columns=['Recency'])

    # 合并df
    df1 = pd.merge(df_R, df_F, how='left', on='CustomerID')
    df_RFM = pd.merge(df1, df_M, how='left', on='CustomerID')

    # 给R打分
    labels = [5, 4, 3, 2, 1]
    df_RFM['R'] = pd.qcut(df_RFM['Recency'], 5, labels=labels)
    # F打分
    labels = [1, 2, 3, 4, 5]
    df_RFM['F'] = pd.qcut(df_RFM['Frequency'], 5, labels=labels)
    # M打分
    labels = [1, 2, 3, 4, 5]
    df_RFM['M'] = pd.qcut(df_RFM['Monetary'], 5, labels=labels)

    # 只取3列
    RFM_Model = df_RFM.filter(items=['R', 'F', 'M'])

    RFM_Model['RFM'] = RFM_Model.apply(rfm, axis=1)

    # 离散化分箱
    bins = RFM_Model.RFM.quantile(q=np.linspace(0, 1, num=9), interpolation='nearest')
    labels = ['流失客户', '一般维持客户', '新客户', '潜力客户', '重要挽留客户', '重要深耕客户', '重要唤回客户', '重要价值客户']
    RFM_Model['Label of Customer'] = pd.cut(RFM_Model.RFM, bins=bins, labels=labels, include_lowest=True)
    print(RFM_Model)
    tmp = RFM_Model.groupby('Label of Customer').size()
    t = [list(z) for z in zip(tmp.index.values.tolist(), tmp.values.tolist())]
    # 绘制饼图
    pie = (
        Pie()
            .add('', t,
                 radius=['30%', '75%'],
                 rosetype='radius',
                 label_opts=opts.LabelOpts(is_show=True))
            .set_global_opts(title_opts=opts.TitleOpts(title='消费者分层结构', pos_left='center'),
                             toolbox_opts=opts.ToolboxOpts(is_show=True),
                             legend_opts=opts.LegendOpts(orient='vertical', pos_right='2%', pos_top='30%'))
            .set_series_opts(label_opts=opts.LabelOpts(formatter='{b}:{d}%')))
    pie.render("pie.html")

    new_RFM = RFM_Model.join(df_M)
    filter_list = ['流失客户', '新客户', '潜力客户', '重要挽留客户', '重要深耕客户', '重要唤回客户', '重要价值客户']
    new_RFM = new_RFM[new_RFM['Label of Customer'].astype('<U').isin(filter_list)]
    new_RFM['Label of Customer'] = new_RFM['Label of Customer'].astype('<U')
    tmp = new_RFM.groupby('Label of Customer').Monetary.sum()
    tmp = tmp.sort_values()
    from pyecharts.charts import Bar
    yindex = []
    for i in list(tmp.values):
        yindex.append(int(i))
    # 绘制柱状图
    bar = (Bar(init_opts=opts.InitOpts(theme='white', bg_color='#ffd8a6'))
           .add_xaxis(list(tmp.index.values))
           .add_yaxis('消费者分层', yindex, color='lightcoral', category_gap='70%')
           .set_global_opts(title_opts=opts.TitleOpts(title='不同分层消费者消费总额', pos_left='center',
                                                      title_textstyle_opts=opts.TextStyleOpts(color='lightcoral')),
                            legend_opts=opts.LegendOpts(pos_top='bottom'),
                            toolbox_opts=opts.ToolboxOpts(is_show=True),
                            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(formatter='{value}')))
           )
    bar.render("bar.html")


# 定义权重函数
def rfm(x):
    return x.iloc[0] * 3 + x.iloc[1] * 4 + x.iloc[2] * 3
def main():
    readdata()


if __name__ == '__main__':
    main()


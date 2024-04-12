import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from datetime import datetime, timedelta

# 读取数据
data = pd.read_csv('1.csv', encoding='gbk')

# 数据预处理
data['日期'] = pd.to_datetime(data['日期'])
data = data.sort_values(['分拣中心', '日期'])

# 建立空的 DataFrame 存储所有分拣中心的预测结果
all_forecast_results = pd.DataFrame(columns=['分拣中心', '日期', '预测'])

# 遍历不同的分拣中心
for center, center_data in data.groupby('分拣中心'):
    # 拆分数据
    train_size = int(len(center_data) * 0.8)
    train, test = center_data[:train_size], center_data[train_size:]

    # 计算货量的5%和90%分位数
    q5, q90 = train['货量'].quantile(0.05), train['货量'].quantile(0.90)

    # 只保留位于5%到90%分位数之间的数据
    train = train[(train['货量'] >= q5) & (train['货量'] <= q90)]

    # 建立 SARIMA 模型
    model = SARIMAX(train['货量'], order=(5, 1, 0), seasonal_order=(1, 1, 1, 12))
    model_fit = model.fit()

    # 预测12月1日到12月31日每天的货量
    start_date = datetime(2023, 12, 1)
    end_date = datetime(2023, 12, 31)
    forecast_index = pd.date_range(start=start_date, end=end_date, freq='D')
    forecast = model_fit.forecast(steps=len(forecast_index))

    # 模拟十一月销量的影响，假设为十一月销量均值的70%波动
    november_effect = train['货量'].mean() * 0.7
    forecast += november_effect

    # 模拟促销活动前后的影响，假设促销活动持续15天
    promo_start_date = datetime(2023, 12, 15)
    promo_end_date = promo_start_date + timedelta(days=15)
    promo_effect = train[(train['日期'] >= promo_start_date) & (train['日期'] <= promo_end_date)]['货量'].mean() * 0.2
    forecast[(forecast_index >= promo_start_date) & (forecast_index <= promo_end_date)] += promo_effect

    # 创建包含预测结果的 DataFrame
    forecast_df = pd.DataFrame({'分拣中心': center,
                                '日期': forecast_index,
                                '预测': forecast})

    # 将预测结果添加到总的 DataFrame 中
    all_forecast_results = pd.concat([all_forecast_results, forecast_df], ignore_index=True)

# 将结果保存为CSV文件
all_forecast_results.to_csv('forecast_results.csv', encoding='utf-8', index=False)

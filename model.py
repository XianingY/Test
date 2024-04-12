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
    train_filtered = train[(train['货量'] >= q5) & (train['货量'] <= q90)]

    # 建立 SARIMA 模型，包括十一月的数据
    model = SARIMAX(train_filtered['货量'], order=(5, 1, 0), seasonal_order=(1, 1, 1, 12))
    model_fit = model.fit()

    # 预测12月1日到12月31日每天的货量
    start_date = datetime(2023, 12, 1)
    end_date = datetime(2023, 12, 31)
    forecast_index = pd.date_range(start=start_date, end=end_date, freq='D')
    forecast = model_fit.forecast(steps=len(forecast_index))

    # 获取十一月的数据
    november_data = train[train['日期'].dt.month == 11]

    # 计算十一月数据的影响，假设为平均值
    november_influence = november_data['货量'].mean()

    # 在十二月初添加十一月的影响
    forecast[:10] += november_influence

    # 创建包含预测结果的 DataFrame
    forecast_df = pd.DataFrame({'分拣中心': center,
                                '日期': forecast_index,
                                '预测': forecast})

    # 将预测结果添加到总的 DataFrame 中
    all_forecast_results = pd.concat([all_forecast_results, forecast_df], ignore_index=True)

# 将结果保存为CSV文件
all_forecast_results.to_csv('forecast_results.csv', encoding='utf-8', index=False)

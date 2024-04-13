import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
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
    # 归一化数据
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(center_data['货量'].values.reshape(-1, 1))

    # 准备训练数据
    def create_dataset(data, time_steps=1):
        X, y = [], []
        for i in range(len(data) - time_steps):
            X.append(data[i:(i + time_steps), 0])
            y.append(data[i + time_steps, 0])
        return np.array(X), np.array(y)

    time_steps = 30  # 时间步长
    X, y = create_dataset(scaled_data, time_steps)

    # 将数据重塑为LSTM的输入格式 [samples, time steps, features]
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))

    # 建立LSTM模型
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], 1)))
    model.add(LSTM(units=50))
    model.add(Dense(units=1))

    # 编译模型
    model.compile(optimizer='adam', loss='mean_squared_error')

    # 拟合模型
    model.fit(X, y, epochs=100, batch_size=32)

    # 预测未来30天每天的货量
    forecast = []
    last_sequence = scaled_data[-time_steps:]
    for i in range(30):
        X_forecast = np.array(last_sequence[-time_steps:]).reshape(1, time_steps, 1)
        predicted_value = model.predict(X_forecast)
        forecast.append(predicted_value[0, 0])
        last_sequence = np.append(last_sequence, predicted_value)[1:]

    # 反归一化预测结果
    forecast = scaler.inverse_transform(np.array(forecast).reshape(-1, 1))

    # 创建包含预测结果的 DataFrame
    start_date = center_data['日期'].max() + timedelta(days=1)
    forecast_index = pd.date_range(start=start_date, periods=30)

    #输出获取天数的范围
    print(
        f"Center: {center}, Forecast shape: {forecast.shape}, Forecast start date: {forecast_index[0]}, Forecast end date: {forecast_index[-1]}")

    forecast_df = pd.DataFrame({'分拣中心': center,
                                '日期': forecast_index,
                                '预测': forecast.flatten()})

    # 将预测结果添加到总的 DataFrame 中
    all_forecast_results = pd.concat([all_forecast_results, forecast_df], ignore_index=True)

    # 将结果保存为CSV文件
    all_forecast_results.to_csv('lstm_forecast_results.csv', encoding='utf-8', index=False)

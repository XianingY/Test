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

# 创建函数，从时间序列数据中创建序列
def create_sequences(data, seq_length):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:(i + seq_length)])
        y.append(data[i + seq_length])
    return np.array(X), np.array(y)

# 定义序列长度（回溯的时间步数）
seq_length = 10

# 存储预测结果
all_forecast_results = pd.DataFrame(columns=['分拣中心', '日期', '预测'])

# 遍历不同的分拣中心
for center, center_data in data.groupby('分拣中心'):
    # 数据缩放
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(center_data['货量'].values.reshape(-1, 1))

    # 创建序列
    X, y = create_sequences(scaled_data, seq_length)

    # 分割数据为训练集和测试集
    train_size = int(len(X) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    # 为 LSTM 重塑输入数据 [样本数，时间步数，特征数]
    X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
    X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

    # 构建 LSTM 模型
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(LSTM(units=50))
    model.add(Dense(units=1))

    model.compile(optimizer='adam', loss='mean_squared_error')

    # 训练 LSTM 模型
    model.fit(X_train, y_train, epochs=100, batch_size=32)

    # 生成预测
    forecast = model.predict(X_test)
    forecast = scaler.inverse_transform(forecast)

    # 预测时间范围
    forecast_index = pd.date_range(start=center_data['日期'].iloc[-1] + timedelta(days=1), periods=len(forecast),
                                   freq='D')

    forecast_df = pd.DataFrame({'分拣中心': np.full(len(forecast_index), center),
                                '日期': forecast_index,
                                '预测': forecast.flatten()})

    # 将预测结果添加到总的 DataFrame 中
    all_forecast_results = pd.concat([all_forecast_results, forecast_df], ignore_index=True)

# 将结果保存为 CSV 文件
all_forecast_results.to_csv('forecast_results_lstm.csv', encoding='utf-8', index=False)

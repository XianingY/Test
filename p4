User
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.io import loadmat
from scipy.optimize import linprog


# Load MATLAB data
mat_data = loadmat('SC60.mat')
a = mat_data['a']
data2 = loadmat('data2.mat')
sortedData2 = data2['sortedData2']

# 约束1：完成货量处理
b1 = a
A1 = np.zeros((30, 36180))
xindex = 0
yindex = 36000
for i in range(30):
    A1[i, yindex:yindex + 6] = 160
    yindex += 6

data = np.zeros((30, 36000))
data[0, :6] = 200

for row in range(30):
    shift_distance = row * 6
    for j in range(0, data.shape[1], 180):
        data[row, j + shift_distance:j + shift_distance + 6] = data[0, j:j + 6]

replicated_A = np.tile(data[:, :180], (1, 200))
new_matrix = np.concatenate((replicated_A, np.zeros((30, 180))), axis=1)
A1[:, :36180] = new_matrix

# 约束2：出勤率小于0.85
b2 = 0.85 * 30 * np.ones((1200, 1))
A2 = np.zeros((1200, 36180))
A2_c = np.zeros((6, 180))
for i in range(6):
    A2_c[i, i:6:180] = 1

repeated_matrix = np.tile(A2_c, (200, 1))
big_matrix = np.zeros((1200, 36000))

for i in range(200):
    big_matrix[i * 6:(i + 1) * 6, i * 180:(i + 1) * 180] = repeated_matrix[i * 6:(i + 1) * 6, :]

A2[:, :36000] = big_matrix

# 约束3：连续出勤不超过7天
b3 = 7 * np.ones((1200, 1))
A3 = np.zeros((1200, 36180))
A3_c = np.zeros((6, 180))
for i in range(6):
    A3_c[i, i:6:49] = 1

repeated_matrix = np.tile(A3_c, (200, 1))
big_matrix = np.zeros((1200, 36000))

for i in range(200):
    big_matrix[i * 6:(i + 1) * 6, i * 180:(i + 1) * 180] = repeated_matrix[i * 6:(i + 1) * 6, :]

A3[:, :36000] = big_matrix

# 约束4：每天出勤一个班次
beq = np.ones((6000, 1))
Aeq = np.zeros((6000, 36180))

for i in range(6000):
    start_col = i * 6
    end_col = (i + 1) * 6
    Aeq[i, start_col:end_col] = 1

# 合并约束条件
A = np.vstack((-A1, A2, A3))
b = np.vstack((-b1, b2, b3))

# Load data2
xc = np.ones((200, 30, 6))
yc = np.ones((30, 6))
xc1 = xc.reshape(-1, 1)
yc1 = yc.reshape(-1, 1)
f = np.vstack((xc1, yc1))

intcon = list(range(1, len(f) + 1))
lb = np.zeros((len(xc1) + len(yc1), 1))
ub = np.vstack((np.ones((len(xc1), 1)), np.inf * np.ones((len(yc1), 1))))

# Solve integer linear programming problem
res = linprog(c=f.flatten(), A_ub=A, b_ub=b.flatten(), A_eq=Aeq, b_eq=beq.flatten(), bounds=list(zip(lb.flatten(), ub.flatten())), method='highs')

# Output results
print("Optimal Solution:")
print(res.x)
print("Objective Function Value:")
print(res.fun)
print("Exit Flag:")
print(res.status)

# Generate additional data for writing to Excel
banci = ['00:00-08:00', '05:00-13:00', '08:00-16:00', '12:00-20:00', '14:00-22:00', '16:00-24:00']
date_range = pd.date_range(start='2023-12-01', end='2023-12-30')
date_str = date_range.strftime('%Y/%m/%d').tolist()

# Generate writing matrix
write_matrix = []


if res is not None and res.x is not None:
    for i in range(180):
        n = int(np.sum(res.x[:200, i]))
        for j in range(n):
            write_matrix.append([sortedData2[50][i, 0], date_str[i], banci[i // 30]])
else:
    print("Linear programming solver failed to provide a valid solution.")
    if res is None:
        print("res is None.")
    elif res.x is None:
        print("res.x is None.")

# Write to CSV file
df = pd.DataFrame(write_matrix, columns=['分拣中心', '日期', '班次'])
df.to_csv('r6.csv', index=False)

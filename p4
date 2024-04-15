import numpy as np
import pandas as pd
import pulp as pp
from tqdm import tqdm

# 读取预测数据
hourly_prediction = pd.read_csv('r4.csv')

# 选择特定分拣中心
target_center = 'SC60'


def solve_optimization(center, example_data, num_regular_workers, num_days=30):
    # 定义班次时间
    shifts = {
        1: '00:00-08:00',
        2: '05:00-13:00',
        3: '08:00-16:00',
        4: '12:00-20:00',
        5: '14:00-22:00',
        6: '16:00-24:00'
    }

    # 创建变量
    x = {i: pp.LpVariable(f"正式工班次{i}", lowBound=0, cat="Binary") for i in range(1, 7)}
    y = {i: pp.LpVariable(f"临时工班次{i}", lowBound=0, cat="Integer") for i in range(1, 7)}

    # 创建线性规划问题
    mylp = pp.LpProblem(f"{center}_lp", pp.LpMinimize)

    # 目标函数：最小化总人天数
    mylp += pp.lpSum(x.values()) + pp.lpSum(y.values())

    # 添加约束条件
    for day in range(num_days):
        # 每名正式工出勤率不能高于85%
        mylp += pp.lpSum(x[i] for i in range(1, 7)) <= 0.85 * num_regular_workers * num_days

        # 连续出勤天数不能超过7天
        for i in range(1, num_days - 6):
            # 确保范围保持在字典 'x' 的键内
            mylp += pp.lpSum(x[j] for j in range(i, min(i + 7, 7))) <= 7

        # 每天的货量处理完成的基础上，安排的人天数尽可能少
        mylp += pp.lpSum(x[i] * 25 + y[i] * 20 for i in range(1, 7)) >= example_data.iloc[day]['预测货量']

    # 求解模型
    mylp.solve(pp.PULP_CBC_CMD(msg=0))


    # 获取结果
    result_list = []
    for i in range(1, 7):
        result_dict = {}
        result_dict['分拣中心'] = center
        result_dict['日期'] = example_data.iloc[i - 1]['日期']
        result_dict['班次'] = shifts[i]
        if x[i].varValue == 1:
            result_dict['出勤员工'] = f"正式工{i}"
        else:
            result_dict['出勤员工'] = f"临时工{i}"
        result_list.append(result_dict)

    return result_list


# 创建一个空的 DataFrame 来存储结果
results = []

# 获取目标分拣中心的预测数据和正式工数量
target_data = hourly_prediction[hourly_prediction['分拣中心'] == target_center]
num_regular_workers = 200  # 假设分拣中心SC60当前有200名正式工

# 解决优化问题并汇总结果
results = solve_optimization(target_center, target_data, num_regular_workers)

# 将结果转换为 DataFrame
results_df = pd.DataFrame(results)

# 将结果保存为 CSV 文件
results_df.to_csv('r6.csv', index=False)

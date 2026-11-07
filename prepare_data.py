import pandas as pd
import numpy as np
import os

def load_file_csv_to_panda_dataframe(data_dir='./data/'):
  # 1. Đọc 3 bảng thông tin và khảo sát
    general_df = pd.read_csv(os.path.join(data_dir, 'general_data.csv'))
    emp_survey_df = pd.read_csv(os.path.join(data_dir, 'employee_survey_data.csv'))
    mgr_survey_df = pd.read_csv(os.path.join(data_dir, 'manager_survey_data.csv'))

    # 2. Đọc bảng chấm công (in_time và out_time)
    in_time = pd.read_csv(os.path.join(data_dir, 'in_time.csv'))
    out_time = pd.read_csv(os.path.join(data_dir, 'out_time.csv'))

# Chuẩn hóa tên cột mã nhân viên ở bảng chấm công
    in_time.rename(columns={in_time.columns[0]: 'EmployeeID'}, inplace=True)
    out_time.rename(columns={out_time.columns[0]: 'EmployeeID'}, inplace=True)

    # Chuyển đổi các cột ngày tháng sang kiểu datetime của pandas
    date_cols = [c for c in in_time.columns if c != 'EmployeeID']
    in_time[date_cols] = in_time[date_cols].apply(pd.to_datetime)
    out_time[date_cols] = out_time[date_cols].apply(pd.to_datetime)

    # 3. Tính giờ làm việc mỗi ngày = (Giờ ra - Giờ vào)[cite: 2]
    work_hours = (out_time[date_cols] - in_time[date_cols]).apply(lambda x: x.dt.total_seconds() / 3600)

    # Tạo bảng tóm tắt chỉ số chấm công
    attendance_summary = pd.DataFrame()
    attendance_summary['EmployeeID'] = in_time['EmployeeID']
    attendance_summary['AvgWorkHours'] = work_hours.mean(axis=1)               # Giờ làm trung bình
    attendance_summary['OvertimeDays'] = (work_hours > 8.0).sum(axis=1)         # Số ngày làm thêm
    attendance_summary['TotalLeaveDays'] = work_hours.isna().sum(axis=1)       # Số ngày vắng mặt

    # 4. Gộp (Merge) tất cả các DataFrame lại với nhau qua cột khóa 'EmployeeID'
    df_merged = general_df.merge(emp_survey_df, on='EmployeeID', how='left')
    df_merged = df_merged.merge(mgr_survey_df, on='EmployeeID', how='left')
    df_merged = df_merged.merge(attendance_summary, on='EmployeeID', how='left')

    print(f"Hoàn thành! DataFrame tổng hợp có kích thước: {df_merged.shape}")
    return df_merged

# Thực thi hàm
df_final = load_file_csv_to_panda_dataframe('./data/')

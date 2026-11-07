
import pandas as pd
from pathlib import Path

# Tự động xác định thư mục project
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "archive"

# Đọc dữ liệu
df_general = pd.read_csv(DATA_DIR / "general_data.csv")

df_employee = pd.read_csv(DATA_DIR / "employee_survey_data.csv")

df_manager = pd.read_csv(DATA_DIR / "manager_survey_data.csv")

df4 = pd.read_csv(DATA_DIR / "in_time.csv")

df5 = pd.read_csv(DATA_DIR / "out_time.csv")

print("General Data:", df_general.shape)
print("Employee Survey:", df_employee.shape)
print("Manager Survey:", df_manager.shape)

print(df_general.head())
print(df_employee.head())
print(df_manager.head())




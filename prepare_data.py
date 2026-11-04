
import pandas as pd
import numpy as np
import os
from pathlib import Path


def clean_column_names(df):
    """Standardize column names."""
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(' ', '_')
    )
    return df


def clean_employee_id(df):
    """Standardize EmployeeID."""
    df['EmployeeID'] = (
        df['EmployeeID']
        .astype('string')
        .str.strip()
    )
    return df


def remove_duplicates(df, name):
    """Remove duplicate employee records."""
    duplicate_count = df['EmployeeID'].duplicated().sum()

    if duplicate_count > 0:
        print(f"{name}: {duplicate_count} duplicate records found.")

        df = df.drop_duplicates(
            subset='EmployeeID',
            keep='first'
        )

    return df


def report_missing_values(df, name):
    """Display missing value statistics."""
    missing = df.isna().sum()
    missing = missing[missing > 0]

    print(f"\nMissing values in {name}:")

    if missing.empty:
        print("No missing values.")
    else:
        print(missing)


def load_all_csv_to_dataframe(data_dir='./data/'):

    data_dir = Path(data_dir)

    # ==========================================
    # 1. LOAD DATA
    # ==========================================

    general_df = pd.read_csv(data_dir / 'general_data (1).csv')
    emp_survey_df = pd.read_csv(data_dir / 'employee_survey_data (1).csv')
    mgr_survey_df = pd.read_csv(data_dir / 'manager_survey_data (1).csv')

    in_time = pd.read_csv(data_dir / 'in_time.csv')
    out_time = pd.read_csv(data_dir / 'out_time.csv')

    # ==========================================
    # 2. CLEAN COLUMN NAMES
    # ==========================================

    datasets = [
        general_df,
        emp_survey_df,
        mgr_survey_df,
        in_time,
        out_time
    ]

    for df in datasets:
        clean_column_names(df)

    # ==========================================
    # 3. STANDARDIZE EMPLOYEE ID
    # ==========================================

    for df in datasets:

        # Attendance files use the first column as EmployeeID
        if 'EmployeeID' not in df.columns:
            df.rename(
                columns={df.columns[0]: 'EmployeeID'},
                inplace=True
            )

        clean_employee_id(df)

    # Remove records without EmployeeID
    for i, df in enumerate(datasets):

        df.dropna(subset=['EmployeeID'], inplace=True)

        # Remove empty EmployeeID
        df.drop(
            df[df['EmployeeID'].str.strip() == ''].index,
            inplace=True
        )

    # ==========================================
    # 4. REMOVE DUPLICATES
    # ==========================================

    general_df = remove_duplicates(general_df, 'General Data')
    emp_survey_df = remove_duplicates(emp_survey_df, 'Employee Survey')
    mgr_survey_df = remove_duplicates(mgr_survey_df, 'Manager Survey')

    in_time = remove_duplicates(in_time, 'In Time')
    out_time = remove_duplicates(out_time, 'Out Time')

    # ==========================================
    # 5. PROCESS ATTENDANCE DATA
    # ==========================================

    date_cols = [
        c for c in in_time.columns
        if c != 'EmployeeID'
    ]

    # Ensure both attendance files have the same dates
    common_dates = [
        c for c in date_cols
        if c in out_time.columns
    ]

    # Convert date/time values
    in_time[common_dates] = in_time[common_dates].apply(
        pd.to_datetime, errors='coerce'
    )

    out_time[common_dates] = out_time[common_dates].apply(
        pd.to_datetime, errors='coerce'
    )

    # Match employees between two attendance datasets
    in_time = in_time.set_index('EmployeeID')
    out_time = out_time.set_index('EmployeeID')

    # Align employees and dates
    in_time = in_time.reindex(
        index=sorted(set(in_time.index) & set(out_time.index)),
        columns=common_dates
    )

    out_time = out_time.reindex(
        index=in_time.index,
        columns=common_dates
    )

    # Calculate working hours
    time_difference = out_time - in_time

    work_hours = (
        time_difference
        .map(lambda x: x.total_seconds() / 3600)
    )

    # Invalid working hours
    # Negative hours are invalid
    work_hours = work_hours.mask(work_hours < 0)

    # ==========================================
    # 6. ATTENDANCE SUMMARY
    # ==========================================

    attendance_summary = pd.DataFrame(index=in_time.index)

    attendance_summary['AvgWorkHours'] = work_hours.mean(axis=1)

    attendance_summary['OvertimeDays'] = (
        work_hours > 8
    ).sum(axis=1)

    # Days with valid attendance information
    attendance_summary['RecordedDays'] = (
        work_hours.notna()
    ).sum(axis=1)

    # Missing attendance records
    attendance_summary['MissingAttendanceDays'] = (
        work_hours.isna()
    ).sum(axis=1)

    attendance_summary['TotalLeaveDays'] = (
        attendance_summary['MissingAttendanceDays']
    )

    attendance_summary = attendance_summary.reset_index()

    # ==========================================
    # 7. MERGE DATASETS
    # ==========================================

    df_merged = general_df.merge(
        emp_survey_df,
        on='EmployeeID',
        how='left',
        validate='one_to_one'
    )

    df_merged = df_merged.merge(
        mgr_survey_df,
        on='EmployeeID',
        how='left',
        validate='one_to_one'
    )

    df_merged = df_merged.merge(
        attendance_summary,
        on='EmployeeID',
        how='left',
        validate='one_to_one'
    )

    # ==========================================
    # 8. HANDLE MISSING DATA
    # ==========================================

    # Numeric columns
    numeric_cols = df_merged.select_dtypes(
        include=np.number
    ).columns

    # Categorical columns
    categorical_cols = df_merged.select_dtypes(
        include=['object', 'string', 'category']
    ).columns

    # Fill numeric missing values with median
    for col in numeric_cols:

        if df_merged[col].isna().any():
            median_value = df_merged[col].median()

            if pd.notna(median_value):
                df_merged[col] = df_merged[col].fillna(
                    median_value
                )

    # Fill categorical missing values with mode
    for col in categorical_cols:

        if df_merged[col].isna().any():

            mode_value = df_merged[col].mode()

            if not mode_value.empty:
                df_merged[col] = df_merged[col].fillna(
                    mode_value.iloc[0]
                )

    # ==========================================
    # 9. FINAL DATA VALIDATION
    # ==========================================

    print("\n========== DATA CLEANING REPORT ==========")

    print("Final dataset shape:", df_merged.shape)

    print(
        "Duplicate EmployeeID:",
        df_merged['EmployeeID'].duplicated().sum()
    )

    report_missing_values(df_merged, 'Final Dataset')

    print("\nData types:")
    print(df_merged.dtypes)

    print("\nData cleaning completed!")

    return df_merged


# ==========================================
# 10. EXECUTE
# ==========================================

data_set = load_all_csv_to_dataframe('./data/')

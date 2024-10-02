import pandas as pd


workouts_df = pd.read_excel('C:/Users/63956/Downloads/Workouts Spreadsheet.xlsx')
workouts_df.columns = workouts_df.columns.str.strip()  # This will remove any leading/trailing spaces from column names
print(workouts_df.columns)



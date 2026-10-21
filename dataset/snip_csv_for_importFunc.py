import pandas as pd

# Define file paths
input_file = 'university_library_crowd.csv'
output_file = 'file_to_import.csv'

# Specify the names of the columns you want to delete
columns_to_remove = ['day_of_week', 'is_holiday', 'is_exam_period', 'days_to_exam', 'rainfall_mm', 'temperature_c', 'is_semester_break', 'library_capacity']

# Load the CSV file into a DataFrame
df = pd.read_csv(input_file)

# Drop the specified columns without altering the original DataFrame structure in memory
# axis=1 specifies that we are dropping columns, not rows
new_df = df.drop(columns=columns_to_remove)

# Save the filtered data to a new CSV file
new_df.to_csv(output_file, index=False)

print(f"Success! Cleaned data saved to {output_file}")

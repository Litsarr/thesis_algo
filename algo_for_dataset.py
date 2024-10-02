import pandas as pd
import random

# Load the workouts and demographics spreadsheets
workouts_df = pd.read_excel('C:/Users/63956/Downloads/Workouts Spreadsheet.xlsx')
workouts_df.columns = workouts_df.columns.str.strip()  # Remove leading/trailing spaces from column names
demographics_df = pd.read_excel('C:/Users/63956/Downloads/gym recommendation.xlsx')
demographics_df.columns = demographics_df.columns.str.strip()  # Remove leading/trailing spaces from column names

# Limit the operation to the first 50 rows
demographics_df = demographics_df.head(10)

# Create a mapping of exercises to machines
exercise_machine_mapping = {}
for index, row in workouts_df.iterrows():
    exercise_name = row['Exercises']
    machine_name = row.get('Equipments/Machine', 'No Machine')

    if exercise_name not in exercise_machine_mapping:
        exercise_machine_mapping[exercise_name] = []
    exercise_machine_mapping[exercise_name].append(machine_name)

# Function to select unique exercises, with filtering for weight loss restrictions
def select_unique_exercises(workouts_df, exercise_type, count, is_weight_loss=False):
    relevant_exercises = workouts_df[workouts_df['Classification'] == exercise_type]

    # Filter out exercises with '-' in weight loss columns for weight loss clients
    if is_weight_loss:
        relevant_exercises = relevant_exercises[
            (relevant_exercises['WL Below Average'] != '-') &
            (relevant_exercises['WL Average'] != '-') &
            (relevant_exercises['WL Above Average'] != '-')
        ]

    # Drop duplicates based on exercise name to avoid overlap
    unique_exercises = relevant_exercises.drop_duplicates(subset=['Exercises'])

    # Randomly select the required number of exercises
    if len(unique_exercises) >= count:
        return unique_exercises.sample(count)
    else:
        return unique_exercises

# Function to get the appropriate weight based on fitness score and fitness goal
def get_appropriate_weight(row, fitness_goal, fitness_score):
    if fitness_goal == 'Muscle Building':
        if fitness_score >= 4 and fitness_score <= 6:
            return row['MB Below Average']
        elif fitness_score >= 7 and fitness_score <= 9:
            return row['MB Average']
        elif fitness_score >= 10 and fitness_score <= 12:
            return row['MB Above Average']
    else:  # Weight Loss
        if fitness_score >= 4 and fitness_score <= 6:
            return row['WL Below Average']
        elif fitness_score >= 7 and fitness_score <= 9:
            return row['WL Average']
        elif fitness_score >= 10 and fitness_score <= 12:
            return row['WL Above Average']

# Assign workouts for a specific day, handling weight loss restrictions and appending cardio
# Assign workouts for a specific day, handling weight loss restrictions and appending cardio
def assign_workouts_for_day(user_data, workouts_df, day_type):
    is_weight_loss = user_data['Fitness Goal'] == 'Weight Loss'
    fitness_score = user_data['Fitness Score']

    if day_type == 'push':
        push_exercises = select_unique_exercises(workouts_df, 'push', 4, is_weight_loss)
        core_exercises = select_unique_exercises(workouts_df, 'core', 2, is_weight_loss)
        exercises = pd.concat([push_exercises, core_exercises], ignore_index=True)
    elif day_type == 'pull':
        pull_exercises = select_unique_exercises(workouts_df, 'pull', 4, is_weight_loss)
        core_exercises = select_unique_exercises(workouts_df, 'core', 2, is_weight_loss)
        exercises = pd.concat([pull_exercises, core_exercises], ignore_index=True)
    elif day_type == 'knee':
        knee_exercises = select_unique_exercises(workouts_df, 'knee', 6, is_weight_loss)
        exercises = knee_exercises.reset_index(drop=True)
    elif day_type == 'hip':
        hip_exercises = select_unique_exercises(workouts_df, 'hips', 6, is_weight_loss)
        exercises = hip_exercises.reset_index(drop=True)
    else:
        exercises = pd.DataFrame()

    # Append cardio exercises to the day's workout if the goal is weight loss
    if is_weight_loss:
        cardio_exercise = select_unique_exercises(workouts_df, 'cardio', 1)
        exercises = pd.concat([exercises, cardio_exercise], ignore_index=True)

    workout_plan = []
    used_exercises = set()  # Track exercises used for the day

    # Now we loop over the selected exercises
    for idx, row in exercises.iterrows():
        exercise_name = row['Exercises']

        # Step 1: Filter for the selected exercise and the available machines
        machines = exercise_machine_mapping.get(exercise_name, ['No Machine'])
        available_rows = workouts_df[(workouts_df['Exercises'] == exercise_name) & (workouts_df['Equipments/Machine'].isin(machines))]

        # Step 2: Randomly choose one row (exercise with a machine)
        chosen_row = available_rows.sample(1).iloc[0]

        # Debugging: Print the chosen row for verification
        print(f"Selected row for {exercise_name}:")
        print(chosen_row)

        # Step 3: Fetch the correct weight based on the fitness goal and fitness score
        weight = get_appropriate_weight(chosen_row, user_data['Fitness Goal'], fitness_score)

        # Handle missing or incorrect weights
        if weight is None or weight == '-':
            print(f"Error: No valid weight found for {exercise_name} on {chosen_row['Equipments/Machine']}")
        else:
            # Check if it's a cardio exercise, and remove only sets and reps, but keep the weight
            if chosen_row['Classification'] == 'cardio':
                exercise = {
                    'Exercise': exercise_name,
                    'Machine': chosen_row['Equipments/Machine'],
                    'Target Muscle': chosen_row['Classification'],
                    'Weight': weight
                }
            else:
                exercise = {
                    'Exercise': exercise_name,
                    'Machine': chosen_row['Equipments/Machine'],
                    'Target Muscle': chosen_row['Classification'],
                    'Reps': chosen_row['MB Reps'] if user_data['Fitness Goal'] == 'Muscle Building' else chosen_row['WL Reps'],
                    'Sets': chosen_row['Sets'],
                    'Weight': weight
                }

            # Ensure the same exercise isn't repeated in the workout plan for that day
            if exercise_name not in used_exercises:
                workout_plan.append(exercise)
                used_exercises.add(exercise_name)

    return workout_plan

# Generate a 7-day workout plan based on the user's muscle group selection
def generate_7_day_plan(user_data, workouts_df):
    plan = {}
    muscle_group = user_data['Muscle Groups']

    if muscle_group == 'Upper':
        plan['Day 1'] = assign_workouts_for_day(user_data, workouts_df, 'push')
        plan['Day 4'] = assign_workouts_for_day(user_data, workouts_df, 'push')
        plan['Day 2'] = assign_workouts_for_day(user_data, workouts_df, 'pull')
        plan['Day 5'] = assign_workouts_for_day(user_data, workouts_df, 'pull')
        plan['Day 3'] = plan['Day 6'] = plan['Day 7'] = 'Rest Day'

    elif muscle_group == 'Lower':
        plan['Day 1'] = assign_workouts_for_day(user_data, workouts_df, 'knee')
        plan['Day 4'] = assign_workouts_for_day(user_data, workouts_df, 'knee')
        plan['Day 2'] = assign_workouts_for_day(user_data, workouts_df, 'hip')
        plan['Day 5'] = assign_workouts_for_day(user_data, workouts_df, 'hip')
        plan['Day 3'] = plan['Day 6'] = plan['Day 7'] = 'Rest Day'

    elif muscle_group == 'Both' or user_data['Fitness Goal'] == 'Weight Loss':
        plan['Day 1'] = assign_workouts_for_day(user_data, workouts_df, 'push')
        plan['Day 2'] = assign_workouts_for_day(user_data, workouts_df, 'pull')
        plan['Day 4'] = assign_workouts_for_day(user_data, workouts_df, 'knee')
        plan['Day 5'] = assign_workouts_for_day(user_data, workouts_df, 'hip')
        plan['Day 3'] = plan['Day 6'] = plan['Day 7'] = 'Rest Day'

    return plan

# Generate workout plans for the first 50 users
demographics_df['Workout_Plan'] = demographics_df.apply(lambda x: generate_7_day_plan(x, workouts_df), axis=1)

# Function to format the workout plan as a string for each day
def format_workout_plan(workout_plan):
    if isinstance(workout_plan, list):
        return ', '.join([
            f"{exercise.get('Exercise', 'Unknown')} {exercise.get('Machine', 'No Machine')}" +
            (f" {exercise.get('Sets', '3')} sets {exercise.get('Reps', '12')} reps {exercise.get('Weight', 'N/A')}" if exercise['Target Muscle'] != 'cardio' else f" {exercise.get('Weight', 'N/A')}")
            for exercise in workout_plan
        ])
    return 'Rest Day'

# Save the generated workout plans into a new spreadsheet with a separate sheet for each day
with pd.ExcelWriter('user_workout_plans_first_10.xlsx', engine='xlsxwriter') as writer:
    for day in range(1, 8):
        day_df = demographics_df[['ID', 'Workout_Plan']].copy()
        day_df[f'Day {day}'] = day_df['Workout_Plan'].apply(lambda plan: format_workout_plan(plan.get(f'Day {day}', 'Rest Day')))

        # Save each day in a separate sheet
        day_df[['ID', f'Day {day}']].to_excel(writer, sheet_name=f'Day {day}', index=False)

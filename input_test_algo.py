import pandas as pd
import random

# Load the workouts spreadsheet
workouts_df = pd.read_excel('C:/Users/63956/Downloads/Workouts Spreadsheet.xlsx')
workouts_df.columns = workouts_df.columns.str.strip()  # Remove leading/trailing spaces from column names

# Mapping of exercises to machines
exercise_machine_mapping = {}
for index, row in workouts_df.iterrows():
    exercise_name = row['Exercises']
    machine_name = row.get('Equipments/Machine', 'No Machine')

    if exercise_name not in exercise_machine_mapping:
        exercise_machine_mapping[exercise_name] = []
    exercise_machine_mapping[exercise_name].append(machine_name)

# Function to calculate BMI
def calculate_bmi(height, weight):
    bmi = weight / (height ** 2)
    return bmi

# Function to classify fitness score
def classify_fitness_score(fitness_score):
    if 4 <= fitness_score <= 6:
        return 'Below Average'
    elif 7 <= fitness_score <= 9:
        return 'Average'
    elif 10 <= fitness_score <= 12:
        return 'Above Average'
    else:
        return 'Invalid'

# Function to get user input
def get_user_input():
    height = float(input("Enter your height in meters: "))
    weight = float(input("Enter your weight in kilograms: "))
    fitness_score = int(input("Enter your fitness score (4-12): "))

    # Calculate BMI
    bmi = calculate_bmi(height, weight)

    # Determine fitness goal based on BMI
    if bmi < 18.5:
        fitness_goal = 'Muscle Building'
        bmi_category = 'Underweight'
    elif 18.5 <= bmi < 25:
        fitness_goal = 'Muscle Building'
        bmi_category = 'Normal'
    elif 25 <= bmi < 30:
        fitness_goal = 'Weight Loss'
        bmi_category = 'Overweight'
    else:
        fitness_goal = 'Weight Loss'
        bmi_category = 'Obese'

    print(f"\nYour BMI is {bmi:.2f} ({bmi_category}).")
    print(f"Your fitness goal is set to: {fitness_goal}.")

    # For weight loss, muscle group is set to "Weight Loss Only"
    if fitness_goal == 'Muscle Building':
        muscle_group = input("Choose your muscle group (Upper, Lower, Both): ").strip().capitalize()
    else:
        muscle_group = 'Weight Loss Only'

    fitness_score_category = classify_fitness_score(fitness_score)
    if fitness_score_category == 'Invalid':
        print("Invalid fitness score. Please enter a score between 4 and 12.")
        return None

    return {
        'Height': height,
        'Weight': weight,
        'BMI': bmi,
        'Fitness Score': fitness_score,
        'Fitness Goal': fitness_goal,
        'Muscle Groups': muscle_group,
        'Fitness Score Category': fitness_score_category
    }

# Function to select unique exercises
def select_unique_exercises(exercise_type, count, is_weight_loss=False):
    relevant_exercises = workouts_df[workouts_df['Classification'] == exercise_type]

    # Filter weight loss restrictions
    if is_weight_loss:
        relevant_exercises = relevant_exercises[
            (relevant_exercises['WL Below Average'] != '-') &
            (relevant_exercises['WL Below Average'].notna())
        ]

    unique_exercises = relevant_exercises.drop_duplicates(subset=['Exercises'])
    if len(unique_exercises) >= count:
        return unique_exercises.sample(count)
    else:
        return unique_exercises

# Function to get the appropriate weight based on fitness score and fitness goal
def get_appropriate_weight(row, fitness_goal, fitness_score):
    if fitness_goal == 'Muscle Building':
        if 4 <= fitness_score <= 6:
            return row['MB Below Average']
        elif 7 <= fitness_score <= 9:
            return row['MB Average']
        elif 10 <= fitness_score <= 12:
            return row['MB Above Average']
    else:  # Weight Loss
        if 4 <= fitness_score <= 6:
            return row['WL Below Average']
        elif 7 <= fitness_score <= 9:
            return row['WL Average']
        elif 10 <= fitness_score <= 12:
            return row['WL Above Average']

# Assign workouts for a specific day
def assign_workouts_for_day(user_data, day_type):
    is_weight_loss = user_data['Fitness Goal'] == 'Weight Loss'
    fitness_score = user_data['Fitness Score']

    if day_type == 'push':
        push_exercises = select_unique_exercises('push', 4, is_weight_loss)
        core_exercises = select_unique_exercises('core', 2, is_weight_loss)
        exercises = pd.concat([push_exercises, core_exercises], ignore_index=True)
    elif day_type == 'pull':
        pull_exercises = select_unique_exercises('pull', 4, is_weight_loss)
        core_exercises = select_unique_exercises('core', 2, is_weight_loss)
        exercises = pd.concat([pull_exercises, core_exercises], ignore_index=True)
    elif day_type == 'knee':
        knee_exercises = select_unique_exercises('knee', 6, is_weight_loss)
        exercises = knee_exercises.reset_index(drop=True)
    elif day_type == 'hip':
        hip_exercises = select_unique_exercises('hips', 6, is_weight_loss)
        exercises = hip_exercises.reset_index(drop=True)
    else:
        exercises = pd.DataFrame()

    if is_weight_loss:
        cardio_exercise = select_unique_exercises('cardio', 1)
        exercises = pd.concat([exercises, cardio_exercise], ignore_index=True)

    workout_plan = []
    used_exercises = set()

    for idx, row in exercises.iterrows():
        exercise_name = row['Exercises']
        machines = exercise_machine_mapping.get(exercise_name, ['No Machine'])
        machine = random.choice(machines)

        weight = get_appropriate_weight(row, user_data['Fitness Goal'], fitness_score)

        if row['Classification'] == 'cardio':
            exercise = {
                'Exercise': exercise_name,
                'Machine': machine,
                'Target Muscle': row['Classification'],
                'Weight': weight
            }
        else:
            exercise = {
                'Exercise': exercise_name,
                'Machine': machine,
                'Target Muscle': row['Classification'],
                'Reps': row['MB Reps'] if user_data['Fitness Goal'] == 'Muscle Building' else row['WL Reps'],
                'Sets': row['Sets'],
                'Weight': weight
            }

        if exercise_name not in used_exercises:
            workout_plan.append(exercise)
            used_exercises.add(exercise_name)

    return workout_plan

# Function to generate a 7-day workout plan
def generate_7_day_plan(user_data):
    plan = {}

    if user_data['Muscle Groups'] == 'Upper':
        plan['Day 1'] = assign_workouts_for_day(user_data, 'push')
        plan['Day 4'] = assign_workouts_for_day(user_data, 'push')
        plan['Day 2'] = assign_workouts_for_day(user_data, 'pull')
        plan['Day 5'] = assign_workouts_for_day(user_data, 'pull')
        plan['Day 3'] = plan['Day 6'] = plan['Day 7'] = 'Rest Day'
    elif user_data['Muscle Groups'] == 'Lower':
        plan['Day 1'] = assign_workouts_for_day(user_data, 'knee')
        plan['Day 4'] = assign_workouts_for_day(user_data, 'knee')
        plan['Day 2'] = assign_workouts_for_day(user_data, 'hip')
        plan['Day 5'] = assign_workouts_for_day(user_data, 'hip')
        plan['Day 3'] = plan['Day 6'] = plan['Day 7'] = 'Rest Day'
    elif user_data['Muscle Groups'] == 'Both' or user_data['Fitness Goal'] == 'Weight Loss':
        plan['Day 1'] = assign_workouts_for_day(user_data, 'push')
        plan['Day 2'] = assign_workouts_for_day(user_data, 'pull')
        plan['Day 4'] = assign_workouts_for_day(user_data, 'knee')
        plan['Day 5'] = assign_workouts_for_day(user_data, 'hip')
        plan['Day 3'] = plan['Day 6'] = plan['Day 7'] = 'Rest Day'

    return plan

# Function to print workout plan
def print_workout_plan(workout_plan):
    for day, exercises in workout_plan.items():
        if isinstance(exercises, list):
            exercise_details = ', '.join([
                f"{exercise['Exercise']} {exercise['Machine']}" +
                (f" {exercise.get('Sets', '3')} sets {exercise.get('Reps', '12')} reps {exercise['Weight']} kg" if exercise['Target Muscle'] != 'cardio' else f" {exercise['Weight']}")
                for exercise in exercises
            ])
            print(f"{day}: {exercise_details}")
        else:
            print(f"{day}: Rest Day")

# Main program
if __name__ == "__main__":
    user_data = get_user_input()
    if user_data:
        workout_plan = generate_7_day_plan(user_data)
        print("\nYour 7-day workout plan:")
        print_workout_plan(workout_plan)

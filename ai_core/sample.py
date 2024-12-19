import pandas as pd


def identify_problematic_difficulties(data):
    # Convert the data to a DataFrame for easier processing
    df = pd.DataFrame(data)

    # Group by Difficulty
    difficulty_groups = df.groupby("Difficulty")

    # Step 1: Check if a difficulty level is completed
    difficulty_status = {}
    incomplete_difficulties = []

    for difficulty, group in difficulty_groups:
        total_questions = len(group)
        completed_questions = (
            group["Completed"].str.lower().value_counts().get("yes", 0)
        )

        if completed_questions >= (2 / 3) * total_questions:
            difficulty_status[difficulty] = "completed"
        else:
            difficulty_status[difficulty] = "incomplete"
            incomplete_difficulties.append(difficulty)

    # Step 2: Rank incomplete difficulties by average attempts
    avg_attempts = {}
    for difficulty, group in difficulty_groups:
        if difficulty in incomplete_difficulties:
            avg_attempts[difficulty] = group["Attempts"].mean()

    # Sort incomplete difficulties by average attempts (descending)
    ranked_difficulties = sorted(avg_attempts.items(), key=lambda x: x[1], reverse=True)

    return ranked_difficulties, difficulty_status


# Sample Dataset
data = [
    {
        "Question": "qn1",
        "Difficulty": "Easy",
        "Topic": "Factorising Quadratic Equations",
        "Attempts": 3,
        "Completed": "no",
    },
    {
        "Question": "qn2",
        "Difficulty": "Easy",
        "Topic": "Factorising Quadratic Equations",
        "Attempts": 2,
        "Completed": "yes",
    },
    {
        "Question": "qn3",
        "Difficulty": "Easy",
        "Topic": "Factorising Quadratic Equations",
        "Attempts": 3,
        "Completed": "no",
    },
    {
        "Question": "qn4",
        "Difficulty": "Medium",
        "Topic": "Factorising Quadratic Equations",
        "Attempts": 3,
        "Completed": "no",
    },
    {
        "Question": "qn5",
        "Difficulty": "Medium",
        "Topic": "Factorising Quadratic Equations",
        "Attempts": 1,
        "Completed": "yes",
    },
    {
        "Question": "qn6",
        "Difficulty": "Medium",
        "Topic": "Factorising Quadratic Equations",
        "Attempts": 2,
        "Completed": "yes",
    },
    {
        "Question": "qn7",
        "Difficulty": "Hard",
        "Topic": "Factorising Quadratic Equations",
        "Attempts": 3,
        "Completed": "no",
    },
    {
        "Question": "qn8",
        "Difficulty": "Hard",
        "Topic": "Factorising Quadratic Equations",
        "Attempts": 2,
        "Completed": "yes",
    },
    {
        "Question": "qn9",
        "Difficulty": "Hard",
        "Topic": "Factorising Quadratic Equations",
        "Attempts": 1,
        "Completed": "yes",
    },
    {
        "Question": "qn10",
        "Difficulty": "Easy",
        "Topic": "Factorising Quadratic",
        "Attempts": 3,
        "Completed": "no",
    },
    {
        "Question": "qn11",
        "Difficulty": "Easy",
        "Topic": "Factorising Quadratic",
        "Attempts": 2,
        "Completed": "yes",
    },
    {
        "Question": "qn12",
        "Difficulty": "Easy",
        "Topic": "Factorising Quadratic",
        "Attempts": 3,
        "Completed": "no",
    },
]

# Call the function
return_data = identify_problematic_difficulties(data)

# Output results
print(return_data)

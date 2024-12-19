import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder

# TODO : personal blog --> how you learnt and taught yourself data analysis basics for the purpose of the app
# Adjusted function with filtering by topic first


# data preparation process --> I guess i can split my application by that
def recommend_questions_with_weights(
    query_features, data_frame, target_features, feature_weights
):
    # One-hot encode the target features
    # handle_unknown='ignore' -- > how exactly do i want to handle unkown data
    encoder = OneHotEncoder()
    encoded_features = encoder.fit_transform(data_frame[target_features]).toarray()

    print(encoded_features)

    # Create a query vector for the input features
    query_df = pd.DataFrame([query_features], columns=target_features)
    query_encoded = encoder.transform(query_df).toarray()

    # Expand feature_weights to match one-hot encoded feature dimensions
    categories = encoder.categories_
    expanded_weights = np.concatenate(
        [np.full(len(cat), weight) for cat, weight in zip(categories, feature_weights)]
    )

    # Apply weights to encoded features
    weighted_features = encoded_features * expanded_weights
    query_weighted = query_encoded * expanded_weights

    # Calculate similarity scores between the query and dataset
    similarity_scores = cosine_similarity(query_weighted, weighted_features)

    # Rank questions by similarity (exclude the query itself, if needed)
    sorted_indices = similarity_scores[0].argsort()[::-1]
    recommended_questions = data_frame.iloc[sorted_indices]

    # Step 1: Filter recommendations by the topic
    topic_filtered = recommended_questions[
        recommended_questions["topic"] == query_features["topic"]
    ]

    # Step 2: Filter the already topic-filtered recommendations by difficulty, class, and level
    filtered_recommendations = topic_filtered[
        (topic_filtered["difficulty"] == query_features["difficulty"])
        & (topic_filtered["class"] == query_features["class"])
        & (topic_filtered["level"] == query_features["level"])
    ]

    return filtered_recommendations["_id"]


# Example usage
data = [
    {
        "_id": {"$oid": "675b14bb43adab977ec7c896"},
        "question_id": "Q001",
        "text": "Identify the coefficients a, b, and c in the quadratic expression: \\( 2x^2 - 5x + 3 \\)",
        "topic": "Understanding Quadratic Expressions",
        "level": "MSCE",
        "class": "Form 3",
        "difficulty": "easy",
        "tags": ["algebra", "quadratic", "coefficients"],
        "choices": [
            {"text": "a=2, b=-5, c=3", "is_correct": True},
            {"text": "a=3, b=-5, c=2", "is_correct": False},
            {"text": "a=-5, b=2, c=3", "is_correct": False},
            {"text": "a=2, b=3, c=-5", "is_correct": False},
        ],
        "solution": {
            "explanation": "In a quadratic expression ax² + bx + c, we identify: \n- The coefficient of x² is 'a' (here 2)\n- The coefficient of x is 'b' (here -5)\n- The constant term is 'c' (here 3)"
        },
        "hint": "Look at each term and match it with the standard form ax² + bx + c",
        "metadata": {
            "created_by": "system",
            "created_at": "2024-12-12T00:00:00Z",
            "updated_at": "2024-12-12T00:00:00Z",
        },
        "category": "quadratic_equation",
    },
    {
        "_id": {"$oid": "675b14bb43adab977ec7c897"},
        "question_id": "Q002",
        "text": "Factor the quadratic expression: \\( x^2 + 7x + 12 \\)",
        "topic": "Factorizing Quadratic Expressions",
        "level": "MSCE",
        "class": "Form 3",
        "difficulty": "medium",
        "tags": ["algebra", "factorization", "quadratic"],
        "choices": [
            {"text": "(x + 3)(x + 4)", "is_correct": True},
            {"text": "(x + 6)(x + 1)", "is_correct": False},
            {"text": "(x - 3)(x - 4)", "is_correct": False},
            {"text": "(x + 2)(x + 5)", "is_correct": False},
        ],
        "solution": {
            "explanation": "To factor x² + 7x + 12:\n1. Find two numbers that:\n   - Add up to b (7)\n   - Multiply to give c (12)\n2. These numbers are 3 and 4\n3. Therefore, x² + 7x + 12 = (x + 3)(x + 4)"
        },
        "hint": "Look for two numbers that add to give the coefficient of x and multiply to give the constant term",
        "metadata": {
            "created_by": "system",
            "created_at": "2024-12-12T00:00:00Z",
            "updated_at": "2024-12-12T00:00:00Z",
        },
    },
    {
        "_id": {"$oid": "675b14bb43adab977ec7c898"},
        "question_id": "Q003",
        "text": "Complete the square for the quadratic expression: \\( 2x^2 + 12x + 15 \\)",
        "topic": "Completing the Square",
        "level": "MSCE",
        "class": "Form 3",
        "difficulty": "hard",
        "tags": ["algebra", "completing square", "quadratic"],
        "choices": [
            {"text": "2(x² + 6x + 9) - 3", "is_correct": True},
            {"text": "2(x² + 6x + 9) + 3", "is_correct": False},
            {"text": "2(x² + 6x + 4) + 7", "is_correct": False},
            {"text": "2(x² + 6x + 3) + 6", "is_correct": False},
        ],
        "solution": {
            "explanation": "To complete the square for 2x² + 12x + 15:\n1. Factor out coefficient of x²: 2(x² + 6x) + 15\n2. Inside parentheses, add and subtract square of half the coefficient of x: 2(x² + 6x + 9 - 9) + 15\n3. Factor perfect square trinomial: 2(x + 3)² - 18 + 15\n4. Simplify: 2(x + 3)² - 3"
        },
        "hint": "First factor out the coefficient of x², then complete the square inside the parentheses",
        "metadata": {
            "created_by": "system",
            "created_at": "2024-12-12T00:00:00Z",
            "updated_at": "2024-12-12T00:00:00Z",
        },
    },
    {
        "_id": {"$oid": "675b14bb43adab977ec7c899"},
        "question_id": "Q004",
        "text": "Identify the type of quadratic expression: \\( 4x^2 - 36 \\)",
        "topic": "Understanding Quadratic Expressions",
        "level": "MSCE",
        "class": "Form 3",
        "difficulty": "easy",
        "tags": ["algebra", "quadratic", "special cases"],
        "choices": [
            {"text": "Difference of squares", "is_correct": True},
            {"text": "Perfect square trinomial", "is_correct": False},
            {"text": "Standard quadratic trinomial", "is_correct": False},
            {"text": "Incomplete quadratic", "is_correct": False},
        ],
        "solution": {
            "explanation": "4x² - 36 can be written as 4x² - 6²\nThis is in the form a² - b², which is a difference of squares.\nIt can be factored as (2x+6)(2x-6)"
        },
        "hint": "Look at the terms - do you see a squared term minus another number?",
        "metadata": {
            "created_by": "system",
            "created_at": "2024-12-12T00:00:00Z",
            "updated_at": "2024-12-12T00:00:00Z",
        },
    },
    {
        "_id": {"$oid": "675b14bb43adab977ec7c89a"},
        "question_id": "Q005",
        "text": "Solve the quadratic equation: \\( 3x^2 - 27 = 0 \\)",
        "topic": "Solving Quadratic Equations by Factorization",
        "difficulty": "medium",
        "level": "MSCE",
        "class": "Form 3",
        "tags": ["algebra", "quadratic equations", "factorization"],
        "choices": [
            {"text": "x = ±3", "is_correct": True},
            {"text": "x = ±9", "is_correct": False},
            {"text": "x = ±6", "is_correct": False},
            {"text": "x = ±2", "is_correct": False},
        ],
        "solution": {
            "explanation": "To solve 3x² - 27 = 0:\n1. Factor out 3: 3(x² - 9) = 0\n2. Factor difference of squares: 3(x+3)(x-3) = 0\n3. Use zero product property: x = -3 or x = 3\n4. Therefore, x = ±3"
        },
        "hint": "Try factoring out the greatest common factor first",
        "metadata": {
            "created_by": "system",
            "created_at": "2024-12-12T00:00:00Z",
            "updated_at": "2024-12-12T00:00:00Z",
        },
    },
    {
        "_id": {"$oid": "675b14bb43adab977ec7c89b"},
        "question_id": "Q006",
        "text": "Solve the quadratic equation by completing the square: \\( 2x^2 - 8x - 24 = 0 \\)",
        "topic": "Completing the Square",
        "difficulty": "hard",
        "level": "MSCE",
        "class": "Form 3",
        "tags": ["algebra", "completing square", "quadratic equations"],
        "choices": [
            {"text": "x = 6 or x = -2", "is_correct": True},
            {"text": "x = 4 or x = -4", "is_correct": False},
            {"text": "x = 5 or x = -3", "is_correct": False},
            {"text": "x = 3 or x = -5", "is_correct": False},
        ],
        "solution": {
            "explanation": "To solve 2x² - 8x - 24 = 0:\n1. Rearrange to standard form: 2x² - 8x = 24\n2. Factor out 2: 2(x² - 4x) = 24\n3. Complete the square inside parentheses: 2(x² - 4x + 4 - 4) = 24\n4. Simplify: 2(x - 2)² - 8 = 24\n5. Add 8 to both sides: 2(x - 2)² = 32\n6. Divide by 2: (x - 2)² = 16\n7. Take square root: x - 2 = ±4\n8. Solve for x: x = 6 or x = -2"
        },
        "hint": "Start by factoring out the coefficient of x², then complete the square inside the parentheses",
        "metadata": {
            "created_by": "system",
            "created_at": "2024-12-12T00:00:00Z",
            "updated_at": "2024-12-12T00:00:00Z",
        },
    },
    {
        "_id": {"$oid": "675b16cc43adab977ec7c8be"},
        "question_id": "Q007",
        "text": "A rectangle has a length that is 2 units more than its width. If the area of the rectangle is 35 square units, set up and solve the quadratic equation to find its dimensions.",
        "topic": "Understanding Quadratic Expressions",
        "level": "MSCE",
        "class": "Form 3",
        "difficulty": "medium",
        "tags": ["algebra", "word problems", "geometric application"],
        "choices": [
            {"text": "Width = 5 units, Length = 7 units", "is_correct": True},
            {"text": "Width = 3 units, Length = 5 units", "is_correct": False},
            {"text": "Width = 4 units, Length = 6 units", "is_correct": False},
            {"text": "Width = 6 units, Length = 8 units", "is_correct": False},
        ],
        "solution": {
            "explanation": "Let's solve this step by step:\n1. Let width = x\n2. Then length = x + 2\n3. Area = length × width\n4. 35 = x(x + 2)\n5. 35 = x² + 2x\n6. x² + 2x - 35 = 0\n7. (x + 7)(x - 5) = 0\n8. x = -7 or x = 5\n9. Since width can't be negative, x = 5\nTherefore, width = 5 units and length = 7 units"
        },
        "hint": "Start by expressing the length in terms of the width, then use the area formula to create your equation",
        "metadata": {
            "created_by": "system",
            "created_at": "2024-12-12T00:00:00Z",
            "updated_at": "2024-12-12T00:00:00Z",
        },
    },
    {
        "_id": {"$oid": "675b16cc43adab977ec7c8bf"},
        "question_id": "Q008",
        "text": "Examine the expression \\( x^2 + 10x + 25 \\) and explain why it's considered a perfect square trinomial.",
        "topic": "Factorizing Quadratic Expressions",
        "difficulty": "easy",
        "level": "MSCE",
        "class": "Form 3",
        "tags": ["algebra", "perfect squares", "pattern recognition"],
        "choices": [
            {"text": "It can be written as (x + 5)²", "is_correct": True},
            {"text": "It has three terms", "is_correct": False},
            {
                "text": "The first and last terms are perfect squares",
                "is_correct": False,
            },
            {
                "text": "The middle term is twice the product of the other terms",
                "is_correct": False,
            },
        ],
        "solution": {
            "explanation": "This is a perfect square trinomial because:\n1. The first term (x²) is a perfect square\n2. The last term (25) is a perfect square\n3. The middle term (10x) is twice the product of √(x²) and √25\n4. √(x²) = x and √25 = 5\n5. 2(x)(5) = 10x\nTherefore, x² + 10x + 25 = (x + 5)(x + 5) = (x + 5)²"
        },
        "hint": "Look at the relationship between the middle term and the square roots of the first and last terms",
        "metadata": {
            "created_by": "system",
            "created_at": "2024-12-12T00:00:00Z",
            "updated_at": "2024-12-12T00:00:00Z",
        },
    },
    {
        "_id": {"$oid": "675b17f843adab977ec7c8d4"},
        "question_id": "Q010",
        "text": "The sum of the squares of two consecutive integers is 365. Find the integers.",
        "topic": "Solving Quadratic Equations",
        "difficulty": "medium",
        "level": "MSCE",
        "class": "Form 3",
        "tags": ["algebra", "number problems", "quadratic equations"],
        "choices": [
            {"text": "13 and 14", "is_correct": True},
            {"text": "12 and 13", "is_correct": False},
            {"text": "14 and 15", "is_correct": False},
            {"text": "15 and 16", "is_correct": False},
        ],
        "solution": {
            "explanation": "Let the two consecutive integers be x and x + 1:\n1. The sum of their squares is 365:\n   x² + (x + 1)² = 365\n2. Expand the equation:\n   x² + x² + 2x + 1 = 365\n3. Combine like terms:\n   2x² + 2x + 1 = 365\n4. Simplify:\n   2x² + 2x - 364 = 0\n5. Divide by 2:\n   x² + x - 182 = 0\n6. Factorize:\n   (x - 13)(x + 14) = 0\n7. Solutions are x = 13 or x = -14\n8. Since we're looking for positive integers, x = 13\n   Therefore, the integers are 13 and 14."
        },
        "hint": "Write the equation for the sum of squares, then simplify it into a quadratic equation.",
        "metadata": {
            "created_by": "system",
            "created_at": "2024-12-12T00:00:00Z",
            "updated_at": "2024-12-12T00:00:00Z",
        },
    },
    {
        "_id": {"$oid": "675b17f843adab977ec7c8d5"},
        "question_id": "Q011",
        "text": "A rectangular garden has a perimeter of 60 meters. Its length is twice its width. Find the dimensions of the garden.",
        "topic": "Linear Equations",
        "difficulty": "easy",
        "level": "MSCE",
        "class": "Form 2",
        "tags": ["geometry", "word problems", "linear equations"],
        "choices": [
            {"text": "Length = 20 meters, Width = 10 meters", "is_correct": True},
            {"text": "Length = 30 meters, Width = 15 meters", "is_correct": False},
            {"text": "Length = 15 meters, Width = 5 meters", "is_correct": False},
            {"text": "Length = 25 meters, Width = 12.5 meters", "is_correct": False},
        ],
        "solution": {
            "explanation": "1. Let the width be x and the length be 2x\n2. The perimeter of a rectangle is given by:\n   P = 2(length + width)\n3. Substituting the values:\n   60 = 2(2x + x)\n4. Simplify:\n   60 = 6x\n5. Solve for x:\n   x = 10\n6. Therefore, the width is 10 meters, and the length is 20 meters."
        },
        "hint": "Use the formula for the perimeter of a rectangle to form the equation.",
        "metadata": {
            "created_by": "system",
            "created_at": "2024-12-12T00:00:00Z",
            "updated_at": "2024-12-12T00:00:00Z",
        },
    },
]


df = pd.DataFrame(data)

# Define feature weights (e.g., more weight to 'topic' and 'difficulty')
feature_weights = [0.5, 0.3, 0.2, 1.0]  # Adjust weights to your preference
# Query features
# we also have to add the category of the questions here, for more efficient filtering
input_features = {
    "difficulty": "easy",
    "class": "Form 3",
    "level": "MSCE",
    "topic": "Understanding Quadratic Expressions",
}

# Get recommendations
recommended_questions = recommend_questions_with_weights(
    input_features, df, ["difficulty", "class", "level", "topic"], feature_weights
)

print("Recommended Questions:", recommended_questions.tolist())


@abstractmethod
def get_user_performance_metric(self):
    raise NotImplementedError


@abstractmethod
def calculate_user_performance_metric(self):
    raise NotImplementedError


@abstractmethod
def calculate_group_performance(self, group_id: int):
    """Calculate and return performance metrics for a group of users."""
    raise NotImplementedError


@abstractmethod
def analyze_difficulty_performance(self, user_id: int):
    """Analyze performance based on question difficulty levels."""
    raise NotImplementedError


@abstractmethod
def compare_performance(self, user_id: int, peer_group_id: int):
    """Compare the user's performance to their peer group."""
    raise NotImplementedError


@abstractmethod
def generate_performance_report(self, user_id: int):
    """Generate a detailed performance report for the user."""
    raise NotImplementedError

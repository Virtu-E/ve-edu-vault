import datetime
import json
import re
from typing import Dict, List

import aisuite as ai
from decouple import config


class QuestionAPIGenerator:
    def __init__(self, api_client: ai.Client):
        self.client = api_client
        self.models = ["openai:gpt-4o-mini"]

    def get_current_timestamp(self) -> str:
        return str(datetime.datetime.now(datetime.UTC))

    def create_metadata(self, model_name: str) -> Dict:
        timestamp = self.get_current_timestamp()
        return {
            "created_by": model_name,
            "created_at": timestamp,
            "updated_at": timestamp,
            "time_estimate": {"minutes": "3"},
        }

    def create_prompt(self, subject: str, topic_data: Dict, model_name: str) -> List[Dict]:
        metadata = self.create_metadata(model_name)
        return [
            {
                "role": "system",
                "content": f"""You must respond with only a JSON array containing chemistry exam questions. The response should be a valid JSON array of question objects. Each question object should follow this structure:
{{
    "question_id": "subject_topic_difficulty_number",
    "text": "question_text",
    "topic": "topic_name",
    "category": "category_name",
    "academic_class": "form_level",
    "examination_level": "exam_system",
    "difficulty": "difficulty_level",
    "tags": ["tag1", "tag2"],
    "choices": [
        {{"text": "option_text", "is_correct": boolean}}
    ],
    "solution": {{
        "explanation": "detailed_explanation",
        "steps": ["step1 reason to get to explanation", "step2 reason to get to explanation"]
    }},
    "hint": "hint_text",
    "metadata": {json.dumps(metadata)}
}}""",
            },
            {
                "role": "user",
                "content": f"""Generate {topic_data["num_questions"]} multiple-choice questions for {subject} with these specifications:
Topic: {topic_data["topic"]}
Category: {topic_data["category"]}
Academic Class: {topic_data["academic_class"]}
Examination Level: {topic_data["examination_level"]}
Difficulty Distribution: {json.dumps(topic_data["difficulty_distribution"])}

Important: Ensure questions align with Malawian curriculum context and utilize the specified teaching activities and resources. How ever, do not include them in the generated response. The response must be a valid JSON array containing question objects that exactly match the structure provided.""",
            },
        ]

    def generate_questions(self, subject: str, topic_data: Dict) -> Dict[str, List]:
        results = {}

        for model in self.models:
            try:
                messages = self.create_prompt(subject, topic_data, model)
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000,
                    response_format={"type": "json_object"},
                )

                # Parse the response content
                response_content = response.choices[0].message.content

                # Check if the response is a string and parse it
                if isinstance(response_content, str):
                    questions = json.loads(response_content)
                    if not isinstance(questions, list):
                        # If the parsed content is not a list, check if it's in a nested structure
                        questions = questions.get("questions", [])
                else:
                    questions = []

                # Create a new list to store processed questions
                processed_questions = []
                timestamp = self.get_current_timestamp()

                # Process each question and create new dictionaries
                for q in questions:
                    # Create a new dictionary for each question
                    new_question = dict(q)
                    new_question["metadata"] = {
                        "created_by": model,
                        "created_at": timestamp,
                        "updated_at": timestamp,
                        "time_estimate": {"$numberInt": "3"},
                    }
                    processed_questions.append(new_question)

                results[model] = processed_questions

            except Exception as e:
                print(f"Error with {model}: {str(e)}")
                print("Full error details: ", e)
                results[model] = []

        return results

    @staticmethod
    def sanitize_filename(text: str) -> str:
        """Convert text to a filename-safe format."""
        # Replace spaces and special characters with underscores
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "_", text).strip("-_")
        return text.lower()


def main():
    client = ai.Client(provider_configs={"openai": {"api_key": config("OPENAI_API_KEY")}})
    generator = QuestionAPIGenerator(client)

    topic_data = {
        "topic": "chemist_careers",
        "category": "introduction_to_chemistry",
        "academic_class": "Form 1",
        "examination_level": "JCE",
        "num_questions": 9,
        "teaching_activities": [
            "discussing some careers in chemistry (biochemist, teacher chemist, geochemist, pharmacist, environmental chemist, food chemist, quality control and assurance personnel, photochemist",
            "discussing their importance in society",
        ],
        "learning_resources": [
            "Chemistry textbooks",
            "Laboratory equipment",
            "Charts showing different branches of chemistry",
            "Local industry case studies",
            "Educational videos",
            "digital balances",
            "rulers",
            "thermometers",
            "stop watches",
            "tripod stands",
            "glassware",
            "fire extinguishers",
        ],
        "assessment_resources": [
            "Written tests",
            "Laboratory practical assessments",
            "Project presentations",
            "Peer assessment rubrics",
            "Group work evaluation forms",
        ],
        "difficulty_distribution": {"easy": 3, "medium": 3, "hard": 3},
    }

    results = generator.generate_questions("Chemistry", topic_data)

    # Save results to separate files for each model with detailed naming
    for model, questions in results.items():
        # Create a detailed filename including course, category, and topic
        filename_parts = [
            "chemistry",
            generator.sanitize_filename(topic_data["category"]),
            generator.sanitize_filename(topic_data["topic"]),
            model.split(":")[0],  # model name without provider prefix
        ]

        filename = f"{('_').join(filename_parts)}.json"

        with open(filename, "w") as f:
            json.dump(questions, f, indent=2)


if __name__ == "__main__":
    main()

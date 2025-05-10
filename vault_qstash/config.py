from qstash import Receiver, QStash
import json
import time
import requests
from datetime import datetime, timedelta

from edu_vault.settings import common

# Module-level initialization
QSTASH_TOKEN = getattr(common, "QSTASH_TOKEN", "")  # Note: using token instead of URL
QSTASH_CURRENT_SIGNING_KEY = getattr(common, "QSTASH_CURRENT_SIGNING_KEY", "")
QSTASH_NEXT_SIGNING_KEY = getattr(common, "QSTASH_NEXT_SIGNING_KEY", "")

qstash = QStash(token=QSTASH_TOKEN)  # Initialize with token
receiver = Receiver(
    current_signing_key=QSTASH_CURRENT_SIGNING_KEY,
    next_signing_key=QSTASH_NEXT_SIGNING_KEY,
)

WEBHOOK_URL = "https://webhook.site/7adae75a-465d-4cd8-b9d8-27855e7989ad"


def handle_expiry(data):
    """This would normally be your Django view handler"""
    response = requests.post(
        WEBHOOK_URL, json=data, headers={"Content-Type": "application/json"}
    )
    print(f"Posted to webhook, status: {response.status_code}")
    return response.status_code


def schedule_test_assessment(timer_duration=30, webhook_url=None):
    """
    Schedule a test assessment with an expiry timer that posts to a webhook.

    Args:
        timer_duration: Time in seconds before the assessment expires
        webhook_url: Optional custom webhook URL (uses default if not provided)

    Returns:
        dict: Response from QStash with message ID and other details
    """
    # Use provided webhook URL or fall back to default
    target_url = webhook_url or WEBHOOK_URL

    # Test data - simulating an assessment
    assessment_data = {
        "assessment_id": "test123",
        "student_id": "student456",
        "started_at": datetime.now().isoformat(),
        "message": "This assessment timer has expired!",
    }

    # Calculate when the assessment should end
    end_time = datetime.now() + timedelta(seconds=timer_duration)

    print(f"Current time: {datetime.now().isoformat()}")
    print(f"Scheduling webhook post at: {end_time.isoformat()}")
    print(f"Timer duration: {timer_duration} seconds")

    # Create a unique ID for this test
    test_id = f"test-{int(time.time())}"

    # Use the message API for sending with a delay
    response = qstash.message.publish(
        url=target_url,
        body=json.dumps(assessment_data),
        delay=timer_duration,  # Delay in seconds before the request is sent
        retries=3,
    )

    print(f"Scheduled with QStash, message ID: {response}")
    print(f"Check your webhook at {target_url} after {timer_duration} seconds")

    return response


# Alternative using the schedule API for more control
def schedule_test_with_cron(timer_duration=30, webhook_url=None):
    """
    Schedule a test assessment using the schedule API with a one-time cron expression.
    This is useful for more precise timing than simple delays.
    """
    target_url = webhook_url or WEBHOOK_URL

    assessment_data = {
        "assessment_id": "test123",
        "student_id": "student456",
        "started_at": datetime.now().isoformat(),
        "message": "This assessment timer has expired using scheduled cron!",
    }

    # Calculate end time
    end_time = datetime.now() + timedelta(seconds=timer_duration)

    # Create a one-time cron expression for the end time
    # Format: minute hour day month day-of-week
    cron = f"{end_time.minute} {end_time.hour} {end_time.day} {end_time.month} *"

    print(f"Current time: {datetime.now().isoformat()}")
    print(f"Scheduling webhook post at: {end_time.isoformat()}")
    print(f"Using cron expression: {cron}")

    # Create a schedule with the schedule API
    response = qstash.schedule.create(
        destination=target_url,
        body=json.dumps(assessment_data),
        cron=cron,
        schedule_id=f"assessment-test-{int(time.time())}",
    )

    print(f"Scheduled with QStash, schedule ID: {response}")
    print(f"Check your webhook at {target_url} at the scheduled time")

    return response

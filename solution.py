from collections import defaultdict
from datetime import timedelta
from typing import Any, Dict, List

import requests

SESSION_DIFF = timedelta(minutes=10).total_seconds() * 1000


def create_new_session(event: dict):
    session = {
        'duration': 0,
        'pages': [event.get("url")],
        'startTime': event.get("timestamp")
    }
    return session, event.get("timestamp")


def add_event_to_session(event: dict, session: dict, last_visit_time: int):
    session["pages"].append(event["url"])
    session["duration"] = session["duration"] + (event["timestamp"] - last_visit_time)
    return session, event["timestamp"]


def generate_session_by_user(input: List[Dict[str, Any]]):
    user_sessions = defaultdict(list)
    for event in input['events']:
        user_sessions[event['visitorId']].append(event)

    output = {}
    for user, events in user_sessions.items():

        # sessions will store list of (dict, last_visit_time) as tuple.
        sessions = []

        events.sort(key=lambda e: e["timestamp"])

        # Add first event as new session.
        sessions.append(create_new_session(events[0]))

        for event in events[1:]:
            timestamp = event["timestamp"]
            session, last_visit_time = sessions[-1]
            if timestamp <= last_visit_time + SESSION_DIFF:
                sessions[-1] = add_event_to_session(event, session, last_visit_time)
            else:
                # Create and add new session.
                sessions.append(create_new_session(event))

        # Convert to list of only sessions.
        only_sessions = [session for session, _ in sessions]

        output[user] = only_sessions
    return {'sessionsByUser': output}


import json

if __name__ == '__main__':
    input_response = requests.get(
        url="https://candidate.hubteam.com/candidateTest/v3/problem/dataset?userKey=b35ec2772f65d018cc098080e742")
    input_data = input_response.json()

    print("Input ---> ")
    print(input_data)
    print("-------------------------------------")
    print()

    response_data = generate_session_by_user(input_data)

    print("Output ---> ")
    print(response_data)
    print("-------------------------------------")
    print()

    response = requests.post(
        "https://candidate.hubteam.com/candidateTest/v3/problem/result?userKey=b35ec2772f65d018cc098080e742",
        data=json.dumps(response_data), headers={"Content-Type": "application/json"})

    print(response.status_code)
    print(response.text)

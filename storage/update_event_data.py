import datetime
import json
EVENTFILE = "events.json"
MAX_EVENTS = 5

def update_event_data(event_type, event_data):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    formatted_data = ", ".join([f"{key}: {event_data[key]}" for key in event_data])
    event = {
        "received_timestamp": current_time,
        "msg_data": formatted_data
    }
    try:
        with open( EVENTFILE, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}
    if event_type not in data:
        data[event_type] = {"count":0, "events":[]}
    data[event_type]["count"] += 1
    data[event_type]["events"].insert(0, event)
    data[event_type]["events"] = data[event_type]["events"][:MAX_EVENTS]
    with open(EVENTFILE, "w") as file:
        json.dump(data, file, indent=4)
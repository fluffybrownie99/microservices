import connexion, datetime, json, yaml, logging, logging.config, uuid, os
from pykafka import KafkaClient
from starlette.middleware.cors import CORSMiddleware
from flask_cors import CORS

import os

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"
# External Application Configuration
with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())
# External Logging Configuration
with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)


def get_media_upload(index):
    """ Get Upload data in History """
    hostname = "%s:%d" % (app_config["events"]["hostname"],
    app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    # Here we reset the offset on start so that we retrieve
    # messages at the beginning of the message queue.
    # To prevent the for loop from blocking, we set the timeout to
    # 100ms. There is a risk that this loop never stops if the
    # index is large and messages are constantly being received!
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
    consumer_timeout_ms=1000)
    logger.info("Retrieving media upload at index %d" % index)
    counter = 0
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            if msg.get("type") == "mediaupload": # acts as a filter for only media uploads
                if counter == index:  # Check if the current message is at the desired index
                    return msg, 200  # Return the found message
                counter += 1  # Increment the counter for each media upload message
        logger.error("Could not find Media Upload at index %d" % index)
        return {"message": "Not Found"}, 404        
    except Exception as e:
        logger.error("Error retrieving message: %s" % str(e))
        return {"message": "Error"}, 500

def get_media_playback(index):
    """ Get Playback data in History """
    hostname = "%s:%d" % (app_config["events"]["hostname"],
    app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    # Here we reset the offset on start so that we retrieve
    # messages at the beginning of the message queue.
    # To prevent the for loop from blocking, we set the timeout to
    # 100ms. There is a risk that this loop never stops if the
    # index is large and messages are constantly being received!
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
    consumer_timeout_ms=1000)
    logger.info("Retrieving media playback at index %d" % index)
    counter = 0
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
        # Find the event at the index you want and
        # return code 200
            if msg.get("type") == "mediaplayback":
                if counter == index:  # use counter to make sure the msg is at the correct index
                    return msg, 200  # return the found message
                counter += 1  # if counter isn't index, then increment the counter for each msg
        logger.error("Could not find Media Playback at index %d" % index)
        return {"message": "Not Found"}, 404
    except Exception as e:
        logger.error("Error retrieving message: %s" % str(e))
        return {"message": "Error"}, 500

# Connexion and Flask stuff
app = connexion.FlaskApp(__name__, specification_dir='')
#specification_dir is where to look for OpenAPI specifications. Empty string means
#look in the current directory
# CORS(app.app)
# app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yml",
            base_path="/audit_log",
            strict_validation=True,
            validate_responses=True)
            


if __name__ == "__main__":
    app.run(port=8110)
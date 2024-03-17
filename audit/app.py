import connexion, datetime, json, yaml, logging, logging.config, uuid
from pykafka import KafkaClient
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

#loading log conf
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

# audit app_conf
with open('app_conf.yml', 'r') as config_file:
    app_config = yaml.safe_load(config_file)

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
            if msg.get("type") == "mediaupload":
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
app.add_api("openapi.yml",
            strict_validation=True,
            validate_responses=True)
            
app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    app.run(port=8110)
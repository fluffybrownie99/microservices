import connexion, datetime, json, yaml, logging, logging.config, time, os
from connexion import NoContent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from update_event_data import update_event_data
from media_upload import MediaUpload
from media_playback import MediaPlayback
from operator import and_
from pykafka import KafkaClient
from pykafka.common import OffsetType 
from threading import Thread

import os

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


db_config = app_config['datastore']
db_user = db_config['user']
db_password = db_config['password']
db_hostname = db_config['hostname']
db_port = db_config.get('port', 3306)  # Provide a default port if not specified
db_name = db_config['db']


# Kafka configuration for retry logic
kafka_config = app_config['kafka']
max_retries = kafka_config['max_retries']
retry_sleep_duration = kafka_config['retry_sleep_duration']

# DB Connection
logger.info(f"Connecting to DB. Hostname:{db_hostname}, Port:{db_port}")
DB_ENGINE = create_engine(f'mysql+pymysql://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}',     
    pool_size=10,
    pool_recycle=300, # recycles the connection after 5 minutes
    pool_pre_ping=True) # Makes sure connections are alive
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

def media_upload(body):
    #this makes sure time is properly formatted for the database.
    upload_timestamp = datetime.datetime.strptime(body['uploadTimestamp'], '%Y-%m-%d %H:%M:%S')
    session = DB_SESSION()
    new_upload = MediaUpload(
        fileSize=body['fileSize'],
        mediaType=body['mediaType'],
        uploadTimestamp=upload_timestamp,
        userID=body['userID'],
        date_created=datetime.datetime.now(),
        trace_id=body['trace_id']
    )
    session.add(new_upload)
    session.commit()
    # response = {
    #     "mediaId": str(new_upload.id)
    # }
    session.close()
    logger.debug(f'Stored event "media_upload" request with a trace id of {body["trace_id"]}')
    # return response, 201 
    return NoContent, 201

def media_playback(body):
    session = DB_SESSION()
    playback_start_time = datetime.datetime.strptime(body['playbackStartTime'], '%Y-%m-%d %H:%M:%S')
    new_playback = MediaPlayback(
        mediaId=body['mediaId'],
        playbackStartTime=playback_start_time,
        userID=body['userID'],
        playbackId=body['playbackId'],
        playbackDuration=body.get('playbackDuration', None),
        date_created=datetime.datetime.now(),
        trace_id=body['trace_id']
    )
    session.add(new_playback)
    session.commit()
    # response = {
    #     "userID":str(new_playback.userID)
    # }
    session.close()
    logger.debug(f'Stored event "media_playback" request with a trace id of {body["trace_id"]}')
    # return response, 201  
    return NoContent, 201  

def get_media_upload_events(start_timestamp, end_timestamp):
    """ Gets new media upload readings between the start and end timestamps """
    session = DB_SESSION()
    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, '%Y-%m-%d %H:%M:%S')
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, '%Y-%m-%d %H:%M:%S')
    # Filter results by start time and end time
    results = session.query(MediaUpload).filter(
    and_(MediaUpload.date_created >= start_timestamp_datetime,
    MediaUpload.date_created < end_timestamp_datetime))
    results_list = []
    for reading in results:
        results_list.append(reading.to_dict())
    session.close()
    logger.info("Query for Media Uploads after %s returns %d results" % (start_timestamp, len(results_list)))
    return results_list, 200


def get_media_playback_events(start_timestamp, end_timestamp):
    """ Gets new media playback readings between the start and end timestamps """
    session = DB_SESSION()
    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, '%Y-%m-%d %H:%M:%S')
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, '%Y-%m-%d %H:%M:%S')
    # Filter results by start time and end time
    results = session.query(MediaPlayback).filter(
    and_(MediaPlayback.date_created >= start_timestamp_datetime,
    MediaPlayback.date_created < end_timestamp_datetime))
    results_list = []
    for result in results:
        results_list.append(result.to_dict())
    session.close()
    logger.info("Query for Media Playbacks after %s returns %d results" % (start_timestamp, len(results_list)))
    return results_list, 200

def create_kafka_client():
    retry_count = 0
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    while retry_count < max_retries:
        try:
            logging.info(f"Attempting to connect to Kafka, retry {retry_count}")
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config["events"]["topic"])]
            return client, topic
        except Exception as e:
            logging.error(f"Failed to connect to Kafka: {e}")
            time.sleep(retry_sleep_duration)
            retry_count += 1
    raise Exception("Failed to connect to Kafka after maximum retries")


# Kafka Process
def process_messages():
    """ Process event messages """
    kafka_client, kafka_topic = create_kafka_client()    
    # hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    # client = KafkaClient(hosts=hostname)
    # topic = kafka_client.topics[str.encode(app_config["events"]["topic"])]

    # Create a consume on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).
    consumer = kafka_topic.get_simple_consumer(consumer_group=b'event_group', 
                                        reset_offset_on_start=False, 
                                        auto_offset_reset=OffsetType.LATEST)
    # This is blocking - it will wait for a new message
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s", msg)
        payload = msg["payload"]
        if msg["type"] == "mediaupload": # Change this to your event type
            # Store the event1 (i.e., the payload) to the DB
            media_upload(payload)
        elif msg["type"] == "mediaplayback": # Change this to your event type
            # Store the event2 (i.e., the payload) to the DB
            media_playback(payload)
        
        # Commit the new message as being read
        consumer.commit_offsets()
# Connexion and Flask stuff
app = connexion.FlaskApp(__name__, specification_dir='')
#specification_dir is where to look for OpenAPI specifications. Empty string means
#look in the current directory
app.add_api("openapi.yaml",
            base_path="/storage",
            strict_validation=True,
            validate_responses=True)


#openapi.yaml is the name of the file
# strict_validation - whether to validate requests parameters or messages
# validate_responses - whether to validate the parameters in a request message against your OpenAPI specification

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8090, host="0.0.0.0")
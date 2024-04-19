import connexion, datetime, json, yaml, logging, logging.config, requests, pytz, sqlite3, os
from flask import request, jsonify
from connexion import NoContent
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from operator import and_
from apscheduler.schedulers.background import BackgroundScheduler
from base import Base
from anomaly import Anomaly
from starlette.middleware.cors import CORSMiddleware
from flask_cors import CORS
from create_db import create_database
from pykafka import KafkaClient
from pykafka.common import OffsetType 



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

# Setting thresholds
threshold1 = app_config['threshold']['filesize']
threshold2 = app_config['threshold']['id_limit']

# Check if the SQLite file exists
if not os.path.exists(app_config['datastore']['filename']):
    create_database(app_config['datastore']['filename'])

# connecting to sqlite db
DB_ENGINE = create_engine(f"sqlite:///{app_config['datastore']['filename']}")
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


# Kafka configuration for retry logic
kafka_config = app_config['kafka']
max_retries = kafka_config['max_retries']
retry_sleep_duration = kafka_config['retry_sleep_duration']

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



# GET Handler
def get_anomalies():
    session = DB_SESSION()
    logger.info("Request received. Querying anomalies")
    anomaly_type_query = request.args.get('anomaly_type') 
    try:
        if anomaly_type_query:
            anomalies = session.query(Anomaly).filter(Anomaly.anomaly_type == anomaly_type_query).order_by(Anomaly.date_created.desc()).all()
        else:
            anomalies = session.query(Anomaly).order_by(Anomaly.date_created.desc()).all()
        if not anomalies:
            return jsonify({'message': 'No anomalies found'}), 404

        anomalies_list = [anomaly.to_dict() for anomaly in anomalies]

        return jsonify(anomalies_list), 200

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500
    finally:
        session.close()

def consumer():
    logger.info("Retrieving events")
    counter = 0
    session = DB_SESSION()
    client, topic = create_kafka_client()
    consumer = topic.get_simple_consumer(consumer_group=b'event_group', reset_offset_on_start=True, auto_offset_reset=OffsetType.EARLIEST)

    try:
        for message in consumer:
            logger.info("Message received from Kafka.")
            if message is not None:
                msg_str = message.value.decode('utf-8')
                msg = json.loads(msg_str)
                logger.debug(f"Message processed: {msg}")
                event_type = msg.get("type")
                payload = msg.get("payload")
                if event_type and payload:
                    if event_type == "mediaupload":
                        msg_filesize = payload.get("fileSize")
                        if msg_filesize and int(msg_filesize) > threshold1:
                            record_anomaly(payload, "mediaupload", "TooHigh", f"File size of {msg_filesize} surpassed threshold: {threshold1}", session)

                    elif event_type == "mediaplayback":
                        msg_playbacks = payload.get("playbackId")
                        if msg_playbacks and int(msg_playbacks) > threshold2:
                            record_anomaly(payload, "mediaplayback", "TooMany", f"Playback IDs {msg_playbacks} surpassed threshold: {threshold2}", session)

    except Exception as e:
        logger.error(f"Error retrieving message: {str(e)}")
    finally:
        session.close()

def record_anomaly(payload, event_type, anomaly_type, description, session):
    try:
        anomaly = Anomaly(
            event_id=payload.get("userID"),
            trace_id=payload.get("trace_id"),
            event_type=event_type,
            anomaly_type=anomaly_type,
            description=description
        )
        session.add(anomaly)
        session.commit()
        logger.info(f"Anomaly detected: {anomaly}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error recording anomaly: {str(e)}")



def init_scheduler():
    timezone = pytz.timezone('America/Vancouver') 
    sched = BackgroundScheduler(timezone=timezone, daemon=True)
    sched.add_job(
        consumer,
        'interval',
        seconds=app_config['scheduler']['period_sec'],
        # timezone=timezone  # Add this line if your APScheduler version supports it
    )
    sched.start()

# Connexion and Flask stuff
app = connexion.FlaskApp(__name__, specification_dir='')
#specification_dir is where to look for OpenAPI specifications. Empty string means
#look in the current directory
# CORS(app.app)
# app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi1.yaml",
            base_path="/anomalies",
            strict_validation=True,
            validate_responses=True)




#openapi.yaml is the name of the file
# strict_validation - whether to validate requests parameters or messages
# validate_responses - whether to validate the parameters in a request message against your OpenAPI specification


if __name__ == "__main__":
    init_scheduler()
    app.run(port=8111, host='0.0.0.0')

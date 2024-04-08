import connexion, datetime, json, yaml, logging, logging.config, requests, pytz, sqlite3, os
from connexion import NoContent
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from operator import and_
from apscheduler.schedulers.background import BackgroundScheduler
from base import Base
from server_stats import ServerStats
from starlette.middleware.cors import CORSMiddleware
from flask_cors import CORS
from create_database import create_database

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yaml"
    log_conf_file = "/config/log_conf.yaml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yaml"
    log_conf_file = "log_conf.yaml"
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


# Check if the SQLite file exists
if not os.path.exists(app_config['datastore']['filename']):
    create_database(app_config['datastore']['filename'])

# connecting to sqlite db
DB_ENGINE = create_engine(f"sqlite:///{app_config['datastore']['filename']}")
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)
# GET Handler
def get_stats():
    logger.info("Request for statistics has started")
    session = DB_SESSION()
    current_stats = session.query(ServerStats).order_by(ServerStats.last_updated.desc()).first()
    if current_stats:
        stats_dict = [{
            "total_playbacks": current_stats.total_playbacks,
            "total_uploads": current_stats.total_uploads,
            "most_accessed_file_id":current_stats.most_accessed_file_id,
            "largest_file_id":current_stats.largest_file_id,
            "last_updated":current_stats.last_updated.strftime('%Y-%m-%d %H:%M:%S')
        }]
        logger.debug("Current statistics: %s", stats_dict)
        logger.info("Request for statistics has completed")
        session.close()
        return stats_dict, 200
    else:
        logger.error("Statistics do not exist")
        logger.info("Request for statistics has completed")
        session.close()
        return "Statistics do not exist", 404

def populate_stats():
    """ Periodically update stats """
    logger.info("Start Periodic Processing")
    session = DB_SESSION()
    # query for last_updated time
    current_stats = session.query(ServerStats).order_by(ServerStats.last_updated.desc()).first()
    if current_stats:
        last_updated = current_stats.last_updated.strftime('%Y-%m-%d %H:%M:%S')
    else:
        last_updated = '2020-01-01 00:00:00'

    current_datetime = datetime.datetime.now()
    current_datetime_formatted = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    upload_response = requests.get(app_config['eventstore']['url']+'/home/media/upload', params={'start_timestamp': last_updated, 'end_timestamp': current_datetime_formatted})
    playback_response = requests.get(app_config['eventstore']['url']+'/home/media/playback', params={'start_timestamp': last_updated, 'end_timestamp': current_datetime_formatted})
    upload_response_data = upload_response.json()
    playback_response_data = playback_response.json()

    if upload_response_data == [] and playback_response_data == []:
        logger.info(f'No new events, last update at {last_updated}, current time is {current_datetime_formatted}')
        session.close()
        return
    elif upload_response.status_code != 200 or playback_response.status_code != 200:
        logger.error(f"Received Status code {upload_response.status_code} and {playback_response.status_code}")
        session.close()
    else:
        total_uploads = len(upload_response_data)
        total_playbacks = len(playback_response_data)
        logger.info(f"Received {total_uploads} Upload Events and {total_playbacks} Playback Events")
        # Caluclate updated statistics
        for upload in upload_response_data:
            logger.debug(f'Now processing {upload["trace_id"]}')
            print(f'Now processing {upload["trace_id"]}')
        if upload_response_data:
            largest_file = max(upload_response_data, key=lambda x: x['fileSize'])
            largest_file_id = largest_file['id']
        else:
            largest_file_id = None
        playback_counts = {}
        for playback in playback_response_data:
            logger.debug(f"Now processing Playback event {playback['trace_id']}")
            media_id = playback['mediaId']
            if media_id not in playback_counts:
                playback_counts[media_id] = 1
            else:
                playback_counts[media_id] += 1
        if playback_counts:
            most_accessed_file_id = max(playback_counts, key=playback_counts.get)
        else:
            most_accessed_file_id = None  
    if current_stats != None:
        total_playbacks += int(current_stats.total_playbacks)
        total_uploads += int(current_stats.total_uploads)
    new_stats = ServerStats(
        total_playbacks=total_playbacks, 
        total_uploads=total_uploads, 
        most_accessed_file_id=most_accessed_file_id, 
        largest_file_id=largest_file_id,
        last_updated=current_datetime
    )
    session.add(new_stats)
    session.commit()
    logger.debug(f'New Values: {total_playbacks, total_uploads, most_accessed_file_id, largest_file_id,last_updated}')
    session.close()



def init_scheduler():
    timezone = pytz.timezone('America/Vancouver') 
    sched = BackgroundScheduler(timezone=timezone, daemon=True)
    sched.add_job(
        populate_stats,
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
app.add_api("openapi.yaml",
            base_path="/processing",
            strict_validation=True,
            validate_responses=True)




#openapi.yaml is the name of the file
# strict_validation - whether to validate requests parameters or messages
# validate_responses - whether to validate the parameters in a request message against your OpenAPI specification


if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, host='0.0.0.0')

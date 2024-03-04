# import mysql.connector
# # create_database.py
# db_conn = mysql.connector.connect(host="localhost", user="ram", password="Password", database="arch")
# db_cursor = db_conn.cursor()

# # Base = declarative_base()
# db_cursor.execute('''
#     CREATE TABLE media_uploads(
#         id INT NOT NULL AUTO_INCREMENT,
#         fileSize INT NOT NULL,
#         mediaType ENUM('Photo', 'Video') NOT NULL,
#         uploadTimestamp VARCHAR(100) NOT NULL,
#         userID BINARY(16) NOT NULL,
#         date_created DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
#         trace_id BINARY(16) NOT NULL,
#         CONSTRAINT media_uploads_pk PRIMARY KEY (id)
#     )
# ''')

# db_cursor.execute('''
#     CREATE TABLE media_playbacks(
#         id INT NOT NULL AUTO_INCREMENT,
#         mediaId VARCHAR(255) NOT NULL,
#         playbackStartTime DATETIME NOT NULL,
#         userID BINARY(16) NOT NULL ,
#         playbackId INT NOT NULL,
#         playbackDuration INT,
#         date_created DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
#         trace_id BINARY(16) NOT NULL,
#         CONSTRAINT media_playbacks_pk PRIMARY KEY (id)
#     )
# ''')

# # class MediaUpload(Base):
# #     __tablename__ = 'media_uploads'
# #     id = Column(Integer, primary_key=True)
# #     fileSize = Column(Integer)
# #     mediaType = Column(String)
# #     uploadTimestamp = Column(DateTime)
# #     userID = Column(Uuid)
# #     date_created = Column(DateTime, default=datetime.datetime.utcnow)
# #     trace_id = Column(UUIDType, nullable=False)

# db_conn.commit()
# db_conn.close()


import mysql.connector

# Connect to the MySQL database
db_conn = mysql.connector.connect(host="acit3855audit.westus3.cloudapp.azure.com", user="ram", password="Password", database="arch")
db_cursor = db_conn.cursor()

# Create the media_uploads table with adjustments
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS media_uploads(
        id INT NOT NULL AUTO_INCREMENT,
        fileSize INT NOT NULL,
        mediaType ENUM('Photo', 'Video') NOT NULL,
        uploadTimestamp DATETIME NOT NULL,
        userID BINARY(16) NOT NULL,
        date_created DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        trace_id BINARY(16) NOT NULL,
        CONSTRAINT media_uploads_pk PRIMARY KEY (id)
    )
''')

# Create the media_playbacks table with adjustments
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS media_playbacks(
        id INT NOT NULL AUTO_INCREMENT,
        mediaId INT NOT NULL,
        playbackStartTime DATETIME NOT NULL,
        userID BINARY(16) NOT NULL,
        playbackId INT NOT NULL,
        playbackDuration INT,
        date_created DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        trace_id BINARY(16) NOT NULL,
        CONSTRAINT media_playback_pk PRIMARY KEY (id)
);
''')

# Commit the changes to the database and close the connection
db_conn.commit()
db_conn.close()

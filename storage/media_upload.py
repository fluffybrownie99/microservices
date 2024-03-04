from sqlalchemy import Column, Integer, String, DateTime
from base import Base
from sqlalchemy_utils import UUIDType
import datetime, uuid

class MediaUpload(Base):
    """ Media Upload """
    __tablename__ = 'media_uploads'
    id = Column(Integer, primary_key=True)
    mediaType = Column(String(250), nullable=False)
    fileSize = Column(Integer, nullable=False)
    uploadTimestamp = Column(DateTime, nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now())
    userID = Column(UUIDType, nullable=False, default=uuid.uuid4)
    trace_id = Column(UUIDType, nullable=False)
    def __init__(self, userID, mediaType, fileSize,date_created, uploadTimestamp, trace_id):
        self.mediaType = mediaType.lower()
        self.fileSize = fileSize
        self.uploadTimestamp = uploadTimestamp
        self.userID = userID
        self.trace_id = trace_id    
        self.date_created = date_created
    def to_dict(self):
        return {
            'id': self.id,
            'mediaType': self.mediaType.lower(),
            'fileSize': self.fileSize,
            'uploadTimestamp': self.uploadTimestamp.isoformat(),
            'date_created': self.date_created.isoformat(),
            'userID': str(self.userID),
            'trace_id': str(self.trace_id)
        }
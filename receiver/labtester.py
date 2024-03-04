import requests
import uuid
from datetime import datetime

def test_media_upload():
    media_upload_url = 'http://127.0.0.1:8080/home/media/upload'
    file_path = './test.jpg'
    
    # Generate a dummy UUID for both userID and trace_id for the purpose of this example
    dummy_uuid = str(uuid.uuid4())

    data = {
        'mediaType': 'photo',
        'fileSize': 1024,  # Size in bytes as an integer
        'uploadTimestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),  # Current time in ISO 8601 format
        'userID': dummy_uuid,  # Dummy UUID
        'trace_id': dummy_uuid  # Reusing the dummy UUID for simplicity
    }

    # Use a context manager to ensure the file is properly closed after being sent
    with open(file_path, 'rb') as f:
        files = {'file': f}
        try:
            response = requests.post(media_upload_url, files=files, data=data)
            print(f'Status Code: {response.status_code}')
            print(f'Response: {response.text}')  # Using response.text in case the response is not JSON formatted
        except requests.exceptions.RequestException as e:
            print(f'Request failed: {e}')

if __name__ == "__main__":
    test_media_upload()

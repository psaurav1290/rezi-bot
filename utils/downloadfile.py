from io import BytesIO
import requests

def save_file_to_buffer(response):
    CHUNK_SIZE = 32768
    file = BytesIO()
    with open('e:/Coding/08-Python/03-reddit-bot-rezi.ai/test/new.pdf', 'wb') as diskFile:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:
                file.write(chunk)
                diskFile.write(chunk)
    return file


def downloadDriveFile(fileID):
    URL = 'https://docs.google.com/uc?export=download'
    response = requests.get(URL, params={'id':fileID}, stream=True)
    if response.status_code == requests.codes.ok:
      return save_file_to_buffer(response)
    return None
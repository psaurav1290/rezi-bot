from io import BytesIO
import requests


def save_file_to_buffer(response):
    CHUNK_SIZE = 32768
    file = BytesIO()
    for chunk in response.iter_content(CHUNK_SIZE):
        if chunk:
            file.write(chunk)
    return file


def downloadDriveFile(fileID):
    URL = 'https://docs.google.com/uc?export=download'
    response = requests.get(URL, params={'id': fileID}, stream=True)
    if response.status_code == requests.codes.ok:
        fileSize = int(response.headers['Content-Length'])
        if fileSize == 0:
            raise ValueError("The file should be smaller than 2MB.")
        if fileSize > 2097152:
            raise ValueError("The file should be smaller than 2MB.")
        else:
            return save_file_to_buffer(response)
    else:
        raise FileExistsError("Could not fetch your resume!")

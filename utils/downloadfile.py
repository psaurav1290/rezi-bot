from io import BytesIO
import requests

TOO_LARGE = 2097152


def saveFileToBuffer(response):
    CHUNK_SIZE = 32768
    file = BytesIO()
    for chunk in response.iter_content(CHUNK_SIZE):
        if chunk:
            file.write(chunk)
    return file


def saveChunkedFileToBuffer(response):
    CHUNK_SIZE = 32768
    file = BytesIO()
    for chunk in response.iter_content(CHUNK_SIZE):
        if chunk:
            file.write(chunk)
            if file.getbuffer().nbytes > TOO_LARGE:
                raise ValueError("File too large! The file should be smaller than 2MB.")
    return file


def downloadDriveFile(fileID, session=None):
    URL = 'https://docs.google.com/uc?export=download'
    if session:
        response = session.get(URL, params={'id': fileID}, stream=True)
    else:
        response = requests.get(URL, params={'id': fileID}, stream=True)

    if response.status_code == requests.codes.ok:
        fileSize = response.headers.get('Content-Length')
        if(fileSize):
            fileSize = int(fileSize)
            if fileSize == 0:
                raise ValueError("The resume file is blank!")
            if fileSize > TOO_LARGE:
                raise ValueError("The file should be smaller than 2MB!")
            else:
                return saveFileToBuffer(response)
        else:
            return saveChunkedFileToBuffer(response)
    else:
        raise FileExistsError("Could not fetch your resume!")

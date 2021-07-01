from io import BytesIO
import requests

TOO_LARGE = 2097152


def save_file_to_buffer(response):
    CHUNK_SIZE = 32768
    file = BytesIO()
    for chunk in response.iter_content(CHUNK_SIZE):
        if chunk:
            file.write(chunk)
            if file.getbuffer().nbytes > TOO_LARGE:
                raise ValueError("File too large! The file should be smaller than 2MB.")
    return file


def downloadDriveFile(fileID):
    URL = 'https://docs.google.com/uc?export=download'
    response = requests.get(URL, params={'id': fileID}, stream=True)
    if response.status_code == requests.codes.ok:
        fileSize = response.headers.get('Content-Length')
        if(fileSize):
            fileSize = int(fileSize)
            print(fileSize)
            if fileSize == 0:
                raise ValueError("The resume file is blank!")
            if fileSize > TOO_LARGE:
                raise ValueError("The file should be smaller than 2MB!")
            else:
                return save_file_to_buffer(response)
        else:
            return save_file_to_buffer(response)
    else:
        raise FileExistsError("Could not fetch your resume!")

from io import BytesIO
from googleapiclient.errors import HttpError
import requests

from google.auth.transport import requests as requests_
import requests as pyrequests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload

MAX_FILE_SIZE = 2097152


def save_file_to_buffer(response):
    CHUNK_SIZE = 32768
    file = BytesIO()
    for chunk in response.iter_content(CHUNK_SIZE):
        if chunk:
            file.write(chunk)
    return file


def save_chunked_file_to_buffer(response):
    CHUNK_SIZE = 32768
    file = BytesIO()
    for chunk in response.iter_content(CHUNK_SIZE):
        if chunk:
            file.write(chunk)
            if file.getbuffer().nbytes > MAX_FILE_SIZE:
                raise ValueError("File too large! The file should be smaller than 2MB.")
    return file


def download_drive_from_request(fileID, session=None):
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
            if fileSize > MAX_FILE_SIZE:
                raise ValueError("The file should be smaller than 2MB!")
            else:
                return save_file_to_buffer(response)
        else:
            return save_chunked_file_to_buffer(response)
    else:
        raise FileNotFoundError("Could not fetch your resume!")


# __________________________ Google Client Library __________________________

def drive_file_size(fileId, service):
    request = service.files().get(fileId=fileId, supportsAllDrives=True, fields='size')
    return request.execute().get('size')


class CustomMediaIoBaseDownload(MediaIoBaseDownload):
    def __init__(self, fd, request, chunksize=MAX_FILE_SIZE):
        super().__init__(fd, request, chunksize=chunksize)

    def downloaded_file_size(self):
        return self._progress


def save_to_iobase(fileId, service):
    request = service.files().get_media(fileId=fileId)

    resumeFile = BytesIO()
    downloader = CustomMediaIoBaseDownload(resumeFile, request)
    done = False
    while True:
        status, done = downloader.next_chunk()
        if not done:
            if downloader.downloaded_file_size() >= MAX_FILE_SIZE:
                raise ValueError("The file should be smaller than 2MB!")
        else:
            break

    return resumeFile


def download_from_drive(fileId, creds):
    service = build('drive', 'v3', credentials=creds)

    try:
        fileSize = drive_file_size(fileId, service)
        if fileSize:
            fileSize = int(fileSize)
            if fileSize == 0:
                raise ValueError("The resume file is blank!")
            if fileSize > MAX_FILE_SIZE:
                raise ValueError("The file should be smaller than 2MB!")
            else:
                return save_to_iobase(fileId, service)
        else:
            return save_to_iobase(fileId, service)
    except HttpError as e:
        if e.resp['status'] == 404:
            # Either the file id is invalid or the resume is private and not shared
            raise FileNotFoundError("Could not fetch your resume!")

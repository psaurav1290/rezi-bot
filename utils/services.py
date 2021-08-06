import requests
import os.path
from pathlib import Path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload, DEFAULT_CHUNK_SIZE
from googleapiclient.errors import HttpError
from io import BytesIO
import re

from requests import status_codes
from utils.errors import DocdroidFileNotFound, FileTooLarge, FileTooSmall, DriveFileAccessDenied, DriveFileNotFound, ReziApiRequestError

_MAX_FILE_SIZE = 2097152

BASE_DIR = Path(__file__).resolve().parent.parent


class __Service(object):
    def __init__(self):
        pass

    def get_resume_score(self):
        pass

    def get_reply_message(self):
        pass


class _ReziService(object):
    _api_endpoint = 'https://us-central1-rezi-3f268.cloudfunctions.net/scoreFromFile/'

    def __init__(self, resume):
        self.score = None
        self._fetch_score(resume)

    @staticmethod
    def _format_score(text):
        return round(float(text)*100, 2)

    def _fetch_score(self, resume):
        if resume:
            file_arg = {"resume": (
                'resume.pdf', resume.getvalue(), 'application/pdf')}
            response = requests.post(self._api_endpoint, files=file_arg)
            if (response.status_code == requests.codes.ok):
                self.score = self._format_score(response.text)
            else:
                raise ReziApiRequestError(response.status_code)
        else:
            raise FileTooSmall("Resume file not found!")


class _CustomMediaIoBaseDownload(MediaIoBaseDownload):
    def __init__(self, fd, request, chunksize=DEFAULT_CHUNK_SIZE):
        super().__init__(fd, request, chunksize=chunksize)

    def downloaded_file_size(self):
        return self._progress


class UnsupportedService(__Service):
    _message = "No Google Drive share link found in the post."

    def __init__(self):
        pass

    def __str__(self):
        return self._message

    def get_reply_message(self):
        return self._message


class DriveService(__Service):
    _creds = None
    _TOKEN_PATH = os.path.join(BASE_DIR, 'credentials', 'drive', 'token.json')
    _CLIENT_SECRET_PATH = os.path.join(
        BASE_DIR, 'credentials', 'drive', 'client_secret.json')

    def __init__(self, match):
        super().__init__()
        self._file_id = match.group(2)
        self._score = None

    def __str__(self):
        return self._file_id

    @classmethod
    def get_credentials(cls):

        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        if os.path.exists(cls._TOKEN_PATH):
            cls._creds = Credentials.from_authorized_user_file(cls._TOKEN_PATH)

        if not cls._creds or not cls._creds.valid:
            if cls._creds and cls._creds.expired and cls._creds.refresh_token:
                cls._creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    cls._CLIENT_SECRET_PATH, SCOPES)
                cls._creds = flow.run_local_server(port=0)

            with open(cls._TOKEN_PATH, 'w') as token:
                token.write(cls._creds.to_json())

    def _save_file_to_iobase(self, service):
        request = service.files().get_media(fileId=self._file_id)
        resume_file = BytesIO()
        downloader = _CustomMediaIoBaseDownload(
            resume_file, request, chunksize=_MAX_FILE_SIZE)
        done = False
        while True:
            status, done = downloader.next_chunk()
            if not done:
                if downloader.downloaded_file_size() >= _MAX_FILE_SIZE:
                    raise FileTooLarge(_MAX_FILE_SIZE)
            else:
                break

        return resume_file

    def _get_file_size(self, service):
        request = service.files().get(fileId=self._file_id,
                                      supportsAllDrives=True, fields='size')
        return request.execute().get('size')

    def _download_resume(self):
        if not self._creds:
            self.get_credentials()
        service = build('drive', 'v3', credentials=self._creds)

        try:
            file_size = self._get_file_size(service)
            if file_size:
                file_size = int(file_size)
                if file_size == 0:
                    raise FileTooSmall
                if file_size > _MAX_FILE_SIZE:
                    raise FileTooLarge
                else:
                    return self._save_file_to_iobase(service)
            else:
                return self._save_file_to_iobase(service)

        except HttpError as e:
            if e.resp['status'] == 404:
                # Either the file id is invalid
                raise DriveFileNotFound()
            elif e.error_details[0]['reason'] == 'notFound':
                raise DriveFileAccessDenied()
            else:
                raise e

    def get_resume_score(self):
        resume = self._download_resume()
        reziResume = _ReziService(resume)
        self._score = reziResume.score

    def get_reply_message(self):
        return f"Your resume score is {self._score}%."


class DocdroidService(__Service):
    _creds = None

    def __init__(self, match):
        super().__init__()
        self._redirecting_url = None
        self._download_url = None
        self._score = None
        self._process_link_match(match)

    def __str__(self):
        return self._download_url or self._redirecting_url

    def _process_link_match(self, match):
        if match.group(4):
            self._redirecting_url = match.group()
        elif not match.group(5):
            self._download_url = match.group(
                1)+'file/download/'+match.group(6)+'.pdf'
        else:
            self._download_url = match.group()

    def _get_file_downloader(self, download_url):
        downloader = requests.get(download_url, stream=True)
        if downloader.status_code == requests.codes.ok:
            file_size = downloader.headers.get('Content-Length')
            return downloader, file_size
        raise DocdroidFileNotFound(downloader.status_code)

    @staticmethod
    def _save_file_to_iobase(response):
        CHUNK_SIZE = 32768
        resume_file = BytesIO()
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:
                resume_file.write(chunk)
        return resume_file

    def _get_redirected_url(self):
        redirected_url = requests.head(
            self._redirecting_url).headers.get('location')
        if redirected_url:
            download_url_regex = re.compile(
                r'((http|https)://www.docdroid.net/)(\b[-a-zA-Z0-9]{7}\b/[-a-zA-Z0-9@:%._+~#?&//=]*)')
            download_url_match = re.match(download_url_regex, redirected_url)
            if download_url_match:
                self._download_url = download_url_match.group(
                    1)+'file/download/'+download_url_match.group(3)+'.pdf'

    def _download_resume(self):
        if self._redirecting_url:
            self._get_redirected_url()
        if self._download_url:
            downloader, file_size = self._get_file_downloader(
                self._download_url)
            if file_size:
                file_size = int(file_size)
                if file_size == 0:
                    raise FileTooSmall()
                if file_size > _MAX_FILE_SIZE:
                    raise FileTooLarge(_MAX_FILE_SIZE)
                else:
                    return self._save_file_to_iobase(downloader)
            else:
                return self._save_file_to_iobase(downloader)
        else:
            raise FileNotFoundError("Could not fetch your resume!")

    def get_resume_score(self):
        resume = self._download_resume()
        reziResume = _ReziService(resume)
        self._score = reziResume.score

    def get_reply_message(self):
        return f"Your resume score is {self._score}%."

from collections import deque
from utils.errors import BotError
import re
import time

from utils.logger import Logger
# Import new services defined in utils.services
from utils.services import UnsupportedService_


class Task(Logger):

    _DEBUG_MODE = True

    SERVICES = []

    def __init__(self, submission):
        super().__init__(__name__, self._DEBUG_MODE)
        self._submission = submission
        self._service = None
        self._message = None
        self._download_time = None

    def __str__(self):
        return str(self._service)

    def assign_service(self):
        text = self._submission.selftext_html or self._submission.url

        for service in self.SERVICES:
            match = re.search(service.PATTERN, text)
            if match:
                self._service = service(match)
                return
                
        self._service = UnsupportedService_()

    def _fetch_network_data(self):
        self._service.get_resume_score()

    def _set_reply_message(self, message=None):
        if message:
            self._message = message
        else:
            self._message = self._service.get_reply_message()

    def _send_reply(self):
        self.LOGGER.debug(
            f"[{self._submission.id}] Processed in {round(self._download_time,ndigits=3)}s | {self._message}")
        if not self._DEBUG_MODE:
            self._submission.reply(self._message)

    def do_it(self):
        try:
            self._download_time = time.time()
            self._fetch_network_data()
        except BotError as errorMessage:
            self._download_time = time.time() - self._download_time
            self._set_reply_message(str(errorMessage))
            self._send_reply()
        else:
            self._download_time = time.time() - self._download_time
            self._set_reply_message()
            self._send_reply()


class TaskQueue(object):
    def __init__(self):
        self._task_queue = deque()
        self.count_ = 0

    def append_(self, task):
        self._task_queue.append(task)
        self.count_ += 1

    def appendleft_(self, task):
        self._task_queue.appendleft(task)
        self.count_ += 1

    def pop_(self):
        self.count_ -= 1
        return self._task_queue.pop()

    def popleft_(self):
        self.count_ -= 1
        return self._task_queue.popleft()

    def empty(self):
        return not self.count_


class Submissions(object):
    def __init__(self, reddit, subreddit, hotword, lastChecked, blacklistedUsers):
        self._subreddit = reddit.subreddit(subreddit)
        self._hotword_pattern = re.compile(r"\A"+hotword+r".", re.I)
        self._hotword = hotword
        self._hotlen = len(hotword)
        self._last_checked = lastChecked
        self._checked_till = None
        self._blacklisted_users = blacklistedUsers
        self._new_submissions = None
        self._queued_tasks = None
        self.get_new()

    def get_new(self):
        self._new_submissions = self._subreddit.new()

    def get_tasks(self, limit=0):
        for submission in self._new_submissions:
            if not self._checked_till:
                self._checked_till = submission.created_utc
            if (submission.created_utc <= self._last_checked):
                break
            if (self._hotword == submission.title[:self._hotlen].lower() or self._hotword == submission.selftext[:self._hotlen].lower()) and (submission.author not in self._blacklisted_users):
                task = Task(submission)
                task.assign_service()
                yield task
                if limit == 1:
                    break
                limit -= 1

    def checked_till(self):
        return self._checked_till

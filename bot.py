import os.path
from pathlib import Path
import json
from utils.errors import BotError
import praw
import re
from collections import deque
import concurrent.futures
import time

from utils.services import UnsupportedService, DriveService, DocdroidService

BASE_DIR = Path(__file__).resolve().parent

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


class Task(object):

    _DEBUG_MODE = True

    _services = [
        (DriveService, re.compile(
            r'(http|https)://drive.google.com/file/d/(\b[-a-zA-Z0-9_]{33}\b)[-a-zA-Z0-9@:%._+~#?&//=]*')),
        (DocdroidService, re.compile(
            r'((http|https)://((docdro.id/)|www.docdroid.net/(file/download/)?))(\b[-a-zA-Z0-9]{7}\b/*[-a-zA-Z0-9@:%._+~#?&//=]*)'))
    ]

    def __init__(self, submission):
        self._submission = submission
        self._service = None
        self._message = None
        self._download_time = None

    def __str__(self):
        return str(self._service)

    def assign_service(self):
        text = self._submission.selftext_html or self._submission.url

        for (service, pattern) in self._services:
            match = re.search(pattern, text)
            if match:
                self._service = service(match)
                return

        self._service = UnsupportedService()

    def _fetch_network_data(self):
        self._service.get_resume_score()

    def _set_reply_message(self, message=None):
        if message:
            self._message = message
        else:
            self._message = self._service.get_reply_message()

    def _send_reply(self):
        if self._DEBUG_MODE:
            print(f"{self._submission.id} | {self._download_time}s | ",
                  self._message)
        else:
            self._submission.reply(self._message)

    def do_it(self):
        try:
            self._download_time = time.time()
            self._fetch_network_data()
            self._set_reply_message()
        except BotError as errorMessage:
            self._set_reply_message(str(errorMessage))
        # except:
        #     self._set_reply_message(ERROR_MESSAGE, "Could not fetch your resume! Some unknown error occured.")
        finally:
            self._download_time = time.time() - self._download_time
            self._send_reply()


class Submissions(object):
    def __init__(self, reddit, subreddit, hotword, lastChecked, blacklistedUsers):
        self._subreddit = reddit.subreddit(subreddit)
        self._hotword_pattern = re.compile(r"\A"+hotword+r".",re.I)
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

    def enqueue_tasks(self, task_queue, limit=0):
        for submission in self._new_submissions:
            if not self._checked_till:
                self._checked_till = submission.created_utc
            if (submission.created_utc <= self._last_checked):
                break
            if (self._hotword == submission.title[:self._hotlen].lower() or self._hotword == submission.selftext[:self._hotlen].lower()) and (submission.author not in self._blacklisted_users):
                task = Task(submission)
                task.assign_service()
                task_queue.appendleft_(task)
                if limit == 1:
                    break
                else:
                    limit -= 1

    def checked_till(self):
        return self._checked_till


class RedditBot(object):
    """ The main reddit bot class that finds the hot word downloads the
        resume and comments the score.
    """
    _DEBUG_MODE = False

    def __init__(self, configPath='config.json', dataPath='data.json', sleep=1.0, debug=False, limit=0, maxConnections=50):
        """Constructor.
        Args:
          configPath: string object, The path of the configuration file
             (*.json) for the bot
          dataPath: string object, The path of the data file (*.json)
            for the bot
        """

        self._data_path = os.path.join(BASE_DIR, dataPath)
        self._bot_config = None
        self._bot_data = None
        self._reddit = None
        Task._DEBUG_MODE = debug
        RedditBot._DEBUG_MODE = debug
        self._LIMIT = limit
        self._MAX_CONNECTIONS = maxConnections
        self._SLEEP_TIME = sleep

        self._task_queue = TaskQueue()
        self._get_bot_config(os.path.join(BASE_DIR, configPath))
        self._get_bot_data()
        self._login()
        self._eventloop()

    def _get_bot_config(self, configPath):
        if os.path.exists(configPath):
            with open(configPath, 'r') as file:
                self._bot_config = json.load(file)
        else:
            raise FileNotFoundError(
                f"Configuration file not found at '{configPath}'")

    def _get_bot_data(self):
        if os.path.exists(self._data_path):
            with open(self._data_path, 'r') as file:
                self._bot_data = json.load(file)
        else:
            bot_data = {
                "last_checked": {}
            }
            for subreddit in self._bot_config.get('subreddits'):
                bot_data['last_checked'][subreddit] = 0.0
            self._bot_data = bot_data

    def _save_bot_data(self):
        json_object = json.dumps(self._bot_data, indent=4)
        with open(self._data_path, 'w') as file:
            file.write(json_object)

    def _login(self):
        self._reddit = praw.Reddit(self._bot_config.get('bot_name'))

    def _task_manager(self):
        if self._task_queue.count_:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self._MAX_CONNECTIONS) as executor:
                futures = []
                for i in range(self._task_queue.count_):
                    task = self._task_queue.popleft_()
                    # task.do_it()
                    futures.append(executor.submit(task.do_it))

                for future in concurrent.futures.as_completed(futures):
                    temp = future.result()
                    try:
                        temp = future.result()
                    except Exception as e:
                        print(e)

    def _eventloop(self):
        while True:
            for subreddit_ in self._bot_config.get('subreddits'):

                _time_start = time.time()    # Start of fetching subreddits

                new_submissions = Submissions(
                    self._reddit,
                    subreddit_,
                    self._bot_config.get('hot_word'),
                    self._bot_data.get('last_checked').get(subreddit_),
                    self._bot_config.get('blacklisted_users')
                )

                new_submissions.enqueue_tasks(
                    self._task_queue,
                    limit=self._LIMIT
                )

                self._bot_data['last_checked'][subreddit_] = new_submissions.checked_till(
                )

                _time_mid_1 = time.time()

                print(f"\nr/{subreddit_}\n\n{self._LIMIT} Posts fetched - {_time_mid_1-_time_start}s\n")

                self._task_manager()

                _time_end = time.time()

                print(f"\n{self._LIMIT} Scores Processed = {_time_end - _time_mid_1}s\n\nTotal Time  = {_time_end-_time_start}s\n")

            # self._save_bot_data()
            break
            time.sleep(self._SLEEP_TIME)


if __name__ == '__main__':
    bot = RedditBot(debug=True, limit=1, maxConnections=20)

"""
                                                                        |
"""
"""Get bot configuration properties from the config.json file

Args:
    configPath: string object, The path of the configuration file
    for the bot

Returns:
    _bot_config: <class 'dict'>
    A dictionary containing-
        blacklisted_users (List of Reddit IDs who are blacklisted
        ie- their post won't be considered by bot);
        bot_name (Name of the bot required to pick the right);
        hot_word (The hotword that triggers the bot to process the submission);
        subreddits (List of subreddits from which the bot will consider submissions);

Raises:
    FileNotFoundError if the config file is not found at given path.
"""

import os.path
from pathlib import Path
import json
import praw
import concurrent.futures
import time
from utils.errors import ConfigFileNotFound,DataFileNotFound
from utils.logger import Logger
from utils.containers import Submissions, Task, TaskQueue
from utils import services
from inspect import getmembers, isclass
import re

BASE_DIR = Path(__file__).resolve().parent



class ReziBot(Logger):
    """ The main reddit bot class that initiates the bot, loads bot data
        and configurations. Runs the main event loop.
    """

    _DEBUG_MODE = False

    def __init__(self, configPath='config.json', dataPath='data.json'):

        self._data_path = os.path.join(BASE_DIR, dataPath)
        self._bot_config = self._get_bot_config(os.path.join(BASE_DIR, configPath))
        
        Task._DEBUG_MODE = self._bot_config.get('debug')
        ReziBot._DEBUG_MODE = self._bot_config.get('debug')
        
        # Setup Logger
        super().__init__(__name__, self._DEBUG_MODE)

        self._bot_data = self._get_bot_data()
        Task.SERVICES = [service for service in self._list_services()]
        self._reddit = self._login()
        self._task_queue = TaskQueue()
        self._eventloop()

    def _get_bot_config(self, configPath):
        if os.path.exists(configPath):
            with open(configPath, 'r') as file:
                return json.load(file)
        else:
            raise ConfigFileNotFound(configPath)

    def _get_bot_data(self):
        if not os.path.exists(self._data_path):
            self.LOGGER.warning(str(DataFileNotFound(self._data_path)))
            bot_data = {
                "last_checked": 0
            }
        else:
            with open(self._data_path, 'r') as file:
                bot_data = json.load(file)

        return bot_data

    def _save_bot_data(self):
        json_object = json.dumps(self._bot_data, indent=4)
        with open(self._data_path, 'w') as file:
            file.write(json_object)
        self.LOGGER.info(f"Bot data file saved at {self._data_path}")
        

    def _list_services(self):
        for member in getmembers(services):
            if isclass(member[1]):
                m = re.match(r'.+Service\b',member[0])
                if m:
                    yield member[1]

    def _login(self):
        reddit_ = praw.Reddit(self._bot_config.get('botName'))
        self.LOGGER.debug(f"Logged in")
        return reddit_

    def _task_manager(self):
        if self._task_queue.count_:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self._bot_config.get('maxThread')) as executor:
                futures = []
                for i in range(self._task_queue.count_):
                    task = self._task_queue.popleft_()
                    futures.append(executor.submit(task.do_it))

                for future in concurrent.futures.as_completed(futures):
                    temp = future.result()
                    try:
                        temp = future.result()
                    except Exception as e:
                        self.LOGGER.exception(e)

    def _eventloop(self):
        iterate = self._bot_config.get('loops')
        while iterate:
            _ts0 = time.time()
            subreddit_ = '+'.join([sr for sr in self._bot_config.get('subreddits')])

            _ts1 = time.time()
            self.LOGGER.info(f"Fetching r/{subreddit_}")

            new_submissions = Submissions(
                self._reddit,
                subreddit_,
                self._bot_config.get('hotWord'),
                self._bot_data.get('last_checked'),
                self._bot_config.get('blacklistedUsers')
            )

            count = 0
            for task in new_submissions.get_tasks(limit=self._bot_config.get('limit')):
                self._task_queue.appendleft_(task)
                count += 1

            self._bot_data['last_checked'] = new_submissions.checked_till()

            _ts2 = time.time()
            self.LOGGER.info(f"{count} posts fetched in {round((_ts2-_ts1),ndigits=3)}s")

            self._task_manager()

            _ts3 = time.time()
            self.LOGGER.info(f"{count} scores fetched in {round((_ts3-_ts2),ndigits=3)}s")

            self.LOGGER.info(
                f"Subreddits processed in {round((_ts3-_ts0),ndigits=3)}s")

            self._save_bot_data()
            iterate -= 1
            time.sleep(self._bot_config.get('sleepTime'))

if __name__ == '__main__':
    bot = ReziBot()

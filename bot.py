import os.path
from pathlib import Path
import json
import praw
import concurrent.futures
import time
from utils.logger import Logger
from utils.containers import Submissions, Task, TaskQueue

BASE_DIR = Path(__file__).resolve().parent


class RedditBot(Logger):
    """ The main reddit bot class that initiates the bot, loads bot data
        and configurations. Runs the main event loop.
    """
    _DEBUG_MODE = False

    def __init__(self, configPath='config.json', dataPath='data.json'):
        """Constructor
        Args:
          configPath: string object, The path of the configuration file
             (*.json) for the bot
          dataPath: string object, The path of the data file (*.json)
            for the bot
        """

        self._data_path = os.path.join(BASE_DIR, dataPath)
        self._bot_config = self._get_bot_config(
            os.path.join(BASE_DIR, configPath))
        self._bot_data = self._get_bot_data()

        Task._DEBUG_MODE = self._bot_config.get('debug')
        RedditBot._DEBUG_MODE = self._bot_config.get('debug')

        # Setup Logger
        super().__init__(__name__, self._DEBUG_MODE)

        self._reddit = self._login()
        self._task_queue = TaskQueue()
        self._eventloop()

    def _get_bot_config(self, configPath):
        if os.path.exists(configPath):
            with open(configPath, 'r') as file:
                return json.load(file)
        else:
            raise FileNotFoundError(
                f"Configuration file not found at '{configPath}'")

    def _get_bot_data(self):
        if os.path.exists(self._data_path):
            with open(self._data_path, 'r') as file:
                return json.load(file)
        else:
            bot_data = {
                "last_checked": {}
            }
            for subreddit in self._bot_config.get('subreddits'):
                bot_data['last_checked'][subreddit] = 0.0
            return bot_data

    def _save_bot_data(self):
        json_object = json.dumps(self._bot_data, indent=4)
        with open(self._data_path, 'w') as file:
            file.write(json_object)

    def _login(self):
        reddit_ = praw.Reddit(self._bot_config.get('bot_name'))
        self.LOGGER.debug(f"Logged in")
        return reddit_


    def _task_manager(self):
        if self._task_queue.count_:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self._bot_config.get('max-thread')) as executor:
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
            for subreddit_ in self._bot_config.get('subreddits'):

                _ts1 = time.time()
                self.LOGGER.info(f"Fetching r/{subreddit_}")

                new_submissions = Submissions(
                    self._reddit,
                    subreddit_,
                    self._bot_config.get('hot_word'),
                    self._bot_data.get('last_checked').get(subreddit_),
                    self._bot_config.get('blacklisted_users')
                )

                count = 0
                for task in new_submissions.get_tasks(limit=self._bot_config.get('limit')):
                    self._task_queue.appendleft_(task)
                    count += 1

                self._bot_data['last_checked'][subreddit_] = new_submissions.checked_till(
                )

                _ts2 = time.time()
                self.LOGGER.info(
                    f"{count} posts fetched in {round((_ts2-_ts1),ndigits=3)}s")

                self._task_manager()

                _ts3 = time.time()
                self.LOGGER.info(
                    f"{count} scores fetched in {round((_ts3-_ts2),ndigits=3)}s")

            self.LOGGER.info(
                f"Subreddits processed in {round((_ts3-_ts0),ndigits=3)}s")

            # self._save_bot_data()
            iterate -= 1
            time.sleep(self._bot_config.get('sleep-time'))


if __name__ == '__main__':
    bot = RedditBot()

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

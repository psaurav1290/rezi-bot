import praw
import json
import re
import requests

from requests.sessions import session
from utils.downloadfile import downloadDriveFile, downloadDriveFileAsyncio
from utils.callapi import getReziScore, getReziScoreAsyncio
import time


import concurrent.futures
import requests
import threading

from collections import deque

urlRegEx = re.compile(('https://drive.google.com/file/d/' + '\\b[-a-zA-Z0-9@:%._\\+~#?&=]{33}\\b' + '([-a-zA-Z0-9@:%._\\+~#?&//=]*)'))
MAX_CONNECTIONS = 5


def reziBot():
    botConfig = getConfigFromFile()
    if not botConfig:
        return
    botData = getDataFromFile(botConfig)

    reddit = login(botConfig['bot_name'])
    for subredditName in botConfig['subreddits']:
        subreddit = reddit.subreddit(subredditName)
        submissions = subreddit.new()
        checkedTime = processSubmissions(submissions, hotWord=botConfig['hot_word'], lastChecked=botData['last_checked'][subredditName], blacklistedUsers=botConfig['blacklisted_users'])
        if checkedTime: 
            botData['last_checked'][subredditName] = checkedTime

    # writeDataToFile(botData)


def getConfigFromFile(fileName='config.json'):
    # Gets data from the config.json file
    try:
        with open(fileName, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: {fileName} not found!")
        return None


def getDataFromFile(botConfig, dataFileName='data.json'):
    # Gets data from the data.json file
    try:
        with open(dataFileName, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        botData = {
            "last_checked": {
            }
        }
        for subreddit in botConfig['subreddits']:
            botData['last_checked'][subreddit] = 0.0
        return botData


def writeDataToFile(botData, dataFileName='data.json'):
    json_object = json.dumps(botData, indent=4)
    with open(dataFileName, 'w') as dataFile:
        dataFile.write(json_object)


def login(botName):
    return praw.Reddit(botName)


def getNewSubmissions(subreddit, limit=None):
    if limit:
        allNewSubmissions = subreddit.new(limit=limit)
    else:
        allNewSubmissions = subreddit.new()
    return allNewSubmissions


# ============= Post Process Thread =============
def processSubmissions(submissions, hotWord, lastChecked, blacklistedUsers):
    returnTime = None
    count = 0

    for submission in submissions:
        if not returnTime:
            returnTime = submission.created_utc
        # Breaking operation if LAST_CHECKED submission is reached
        if (submission.created_utc <= lastChecked):
            break
        # Filtering on the basis HOT_WORD and BLACKLISTED_USERS
        if all([hotWord == submission.title.lower()[:16], submission.author not in blacklistedUsers]):
            submissionAction(submission)
        count += 1
        if count == 2:
            break

    performThreadedDownload()
    return returnTime


def submissionAction(submission):
    if submission.selftext_html:
        match = re.search(urlRegEx, submission.selftext_html)
        if match:
            validSubmission(submission.selftext_html, match.span()[0], submission)
            return

    match = re.search(urlRegEx, str(submission.url))
    if match:
        validSubmission(submission.url, match.span()[0], submission)
        return

    # Invalid Submission
    invalidSubmissionAction(submission, "No Google Drive share link found in the post.")


def validSubmission(matchString, matchAt, submission):
    # URL Submission
    fileID = matchString[matchAt+32:matchAt+65]
    fileIDs.append(fileID)
    allSubmissions.append(submission)
# ____ end Post Process Thread ____


fileIDs = []
allSubmissions = []


# ============= Threading =============
thread_local = threading.local()


def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def performThreadedDownload():
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONNECTIONS) as executor:
        executor.map(asyncTask, allSubmissions, fileIDs)


def asyncTask(submission, fileID):
    try:
        session = get_session()
        file = downloadDriveFile(fileID, session)
        print(fileID)
        score = getReziScore(file, session)
        score = round(float(score)*100, 2)
        sendScoreAction(submission, score)
    except ValueError as errorMessage:
        invalidSubmissionAction(submission, errorMessage)
    except FileExistsError as errorMessage:
        invalidSubmissionAction(submission, errorMessage)
    # except:
    #     invalidSubmissionAction(submission, "Could not fetch your resume! Some unknown error occured.")

# ____ end Threading ____


def invalidSubmissionAction(submission, description=None):
    commentToSubmission(submission, f"{description}")


def sendScoreAction(submission, score):
    commentToSubmission(submission, f"Your resume score is {score}%.")


def commentToSubmission(submission, message):
    print(message)
    # submission.reply(message)


def deleteAllComments(submission):
    for comment in submission.comments:
        print('deleting')
        comment.delete()


def printSubmission(submission):
    print(submission.selftext_html)
    print('url:', submission.url)
    print('created_utc:', submission.created_utc)
    print('\n')


if __name__ == '__main__':
    start = time.time()
    reziBot()
    end = time.time()
    print('\n______', '\nTime elapsed:', end-start, 'seconds.', '\n______\n',)

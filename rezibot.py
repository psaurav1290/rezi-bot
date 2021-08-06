import praw
import json
import re
import requests

from utils.downloadfile import downloadFromDriveClient
from utils.callapi import getReziScore

import concurrent.futures

import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from collections import deque

import time

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
        if count == 10:
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


def getCredentials():
    SCOPES = [
        # 'https://www.googleapis.com/auth/drive.metadata.readonly',
        'https://www.googleapis.com/auth/drive.readonly'
    ]

    creds = None

    # The file token.json stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

# ============= Threading =============
def performThreadedDownload():
    creds = getCredentials()
    count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # executor.map(asyncTask, allSubmissions, fileIDs, creds)
        for submission,fileID in zip(allSubmissions, fileIDs):
            count += 1
            executor.submit(asyncTask, submission, fileID, creds, count)
            # asyncTask(submission, fileID, creds)


def asyncTask(submission, fileID, creds, count):
    try:
        start = time.time()
        file = downloadFromDriveClient(fileID, creds)
        print(count, time.time()-start)
        score = getReziScore(file)
        score = round(float(score)*100, 2)
        sendScoreAction(submission, f"{score} {count}")
    except ValueError as errorMessage:
        invalidSubmissionAction(submission, errorMessage)
    except FileNotFoundError as errorMessage:
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

import praw
import json
import re
from utils.downloadfile import downloadDriveFile
from utils.callapi import getReziScore
import time

urlRegEx = re.compile(('https://drive.google.com/file/d/' + '\\b[-a-zA-Z0-9@:%._\\+~#?&=]{33}\\b' + '([-a-zA-Z0-9@:%._\\+~#?&//=]*)'))


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


def invalidSubmissionAction(submission, description=None):
    commentToSubmission(submission, f"{description}\nPlease enter the link in the format https://drive.google.com/file/d/<33 character fileID>/...")


def sendScoreAction(submission, score):
    commentToSubmission(submission, f"Your resume score is {score}%.")


def urlFound(matchString, matchAt, submission):
    # URL Submission
    fileID = matchString[matchAt+32:matchAt+65]
    try:
        file = downloadDriveFile(fileID)
        score = getReziScore(file)
        score = round(float(score)*100, 2)
        sendScoreAction(submission, score)
    except ValueError as errorMessage:
        invalidSubmissionAction(submission, errorMessage)
    except FileExistsError as errorMessage:
        invalidSubmissionAction(submission, errorMessage)
    except:
        invalidSubmissionAction(submission, "Could not fetch your resume! Some unknown error occured.")


def submissionAction(submission):
    if submission.selftext_html:
        match = re.search(urlRegEx, submission.selftext_html)
        if match:
            urlFound(submission.selftext_html, match.span()[0], submission)
            return

    match = re.search(urlRegEx, str(submission.url))
    if match:
        urlFound(submission.url, match.span()[0], submission)
        return

    # Invalid Submission
    invalidSubmissionAction(submission, "No Google Drive share link found in the post.")


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


def processSubmissions(submissions, hotWord, lastChecked, blacklistedUsers):
    returnTime = None

    for submission in submissions:
        if not returnTime:
            returnTime = submission.created_utc
        # Filtering on the basis of LAST_CHECKED
        if (submission.created_utc <= lastChecked):
            break
        # Filtering for HOT_WORD and BLACKLISTED_USERS
        if all([hotWord == submission.title.lower(), submission.author not in blacklistedUsers]):
            submissionAction(submission)
            # printSubmission(submission)
            # deleteAllComments(submission)

    return returnTime


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


if __name__ == '__main__':
    reziBot()
    # for i in range(6):
    #     time.sleep(5)

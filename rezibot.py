import praw
import json
import re
from utils.downloadfile import downloadDriveFile
from utils.callapi import getReziScore
import time


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
    commentToSubmission(submission, f"Please follow the format that bot understands. {description}")
    print(f"Please follow the format that bot understands. {description}")


def sendScoreAction(submission, score):
    commentToSubmission(submission, f"Your resume score is {score}%.")
    print(f"Your resume score ris {score}%.")


def submissionAction(submission):
    if (submission.selftext == ''):
        # Invalid Submission
        invalidSubmissionAction(submission, "Write the resume url in the post body.")
    else:
        urlRegEx = re.compile(('href="\\b([-a-zA-Z0-9@:%._\\+~#?&//=]*)"'))
        match = re.search(urlRegEx, submission.selftext_html)
        if match:
            # URL Submission
            URL = submission.selftext_html[match.span()[0]:match.span()[1]][6:-1]

            # Drive ID extraction
            driveRegEx = re.compile(('/\\b[-a-zA-Z0-9@:%._\\+~#?&=]{33}\\b'))
            match = re.search(driveRegEx, URL)
            if match:
                fileID = URL[match.span()[0]+1:match.span()[1]]
                file = downloadDriveFile(fileID)
                if file:
                    score = getReziScore(file)
                    if score:
                        score = float(score[:6])*100
                        sendScoreAction(submission, score)
                    else:
                        invalidSubmissionAction(submission, "Could not fetch your score!")
                else:
                    invalidSubmissionAction(submission, "Could not fetch your resume!")

            else:
                # Invalid Submission
                invalidSubmissionAction(submission, "Currently we accept Google Drive share links only.")

        else:
            # Invalid Submission
            invalidSubmissionAction(submission, "No URL found in the post body.")


def commentToSubmission(submission, message):
    submission.reply(message)


def deleteAllComments(submission):
    for comment in submission.comments:
        print('deleting')
        comment.delete()


def printSubmission(submission):
    print(submission.title, submission.selftext_html, end="\n\n", sep='\n')


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
            printSubmission(submission)
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
        print('\n\t---END---\n')

    writeDataToFile(botData)


if __name__ == '__main__':
    for i in range(6):
        reziBot()
        time.sleep(5)

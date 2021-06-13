import praw
import json


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


def invalidSubmissionAction(submission):
    commentToSubmission(submission['object'], "Please follow the format that bot understands.")
    print("Please follow the format that bot understands.")


def submissionAction(submission):
    if (submission.selftext == ''):
        # Invalid Submission
        invalidSubmissionAction(submission)
    elif (submission.selftext.strip()[:4] == 'http'):
        # URL Submission
        url = submission.selftext.strip()
    else:
        # Text Submission
        text = submission.selftext.strip()


def commentToSubmission(submission, message):
    submission.reply(message)


def printSubmission(submission):
    print(submission.title, submission.selftext or submission.url, submission.created_utc, end="\n\n", sep='\n')


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

        # return submission.created_utc

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
    reziBot()

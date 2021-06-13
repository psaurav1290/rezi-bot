import praw

BOT_NAME = 'luke_bot'
SUBREDDIT_NAMES = [
    'testlukebot',
]
HOT_WORD = '!roast my resume'
# HOT_WORD = ''
BLACKLISTED_USERS = [
    'Luke_Stone_',
]
LAST_CHECK = 1623580136.0


def login(botName=BOT_NAME):
    return praw.Reddit(botName)


def getNewSubmissions(subreddit, limit=None):
    if limit:
        allNewSubmissions = subreddit.new(limit=limit)
    else:
        allNewSubmissions = subreddit.new()
    return allNewSubmissions


def getDataFromSubmission(submission):
    if (submission.selftext == ''):
        returnData = {
            'type': 'invalid',
            'object': submission
        }
    elif (submission.selftext.strip()[:4] == 'http'):
        returnData = {
            'type': 'url',
            'data': submission.selftext.strip(),
            'object': submission
        }
    else:
        returnData = {
            'type': 'text',
            'data': submission.selftext.strip(),
            'object': submission
        }
    return returnData


def commentToSubmission(submission, message):
    submission.reply(message)


def printSubmission(submission):
    print(submission.title, submission.selftext or submission.url, submission.selftext_html, end="\n\n", sep='\n')


def processSubmissions(submissions, hotWord=HOT_WORD, afterUtc=LAST_CHECK):
    for submission in submissions:
        # Filtering on the basis of LAST_CHECKED
        if (submission.created_utc <= afterUtc):
            break
        # Filtering for HOT_WORD and BLACKLISTED_USERS
        if all([hotWord == submission.title,submission.author not in BLACKLISTED_USERS]):
            submission = getDataFromSubmission(submission)
            if (submission['type']=='invalid'):
                commentToSubmission(submission['object'], "Please follow the format that bot understands.")
            elif (submission['type']=='text'):
                pass
            elif (submission['type']=='text'):
                pass

            printSubmission(submission['object'])


def reziBot():
    reddit = login()
    for subredditName in SUBREDDIT_NAMES:
        subreddit = reddit.subreddit(subredditName)
        submissions = subreddit.new()
        processSubmissions(submissions)
        print('\n\t---END---\n')
        


if __name__ == '__main__':
    reziBot()

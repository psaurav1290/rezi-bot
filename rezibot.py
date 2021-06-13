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


def getNewSubmissions(subreddit, limit=None, hotWord=HOT_WORD, afterUtc=LAST_CHECK):
    if limit:
        allNewSubmissions = subreddit.new(limit=limit)
    else:
        allNewSubmissions = subreddit.new()

    submissions = []
    # Return filterd new submissions whose title or text contains the hotword
    for submission in allNewSubmissions:
        if (submission.created_utc <= LAST_CHECK):
            break
        elif (hotWord == submission.title[:len(hotWord)] and not any([submission.author in BLACKLISTED_USERS])):
            submissions.append(submission)
    return submissions


def getDataFromSubmissions(submissions):
    returnList = []
    for submission in submissions:
        if (submission.selftext==''):
            returnList.append({
                'type': 'invalid',
                'object': submission
            })
        elif (submission.selftext.strip()[:4] == 'http'):
            returnList.append({
                'type': 'url',
                'data': submission.selftext.strip(),
                'object': submission
            })
        else:
            returnList.append({
                'type': 'text',
                'data': submission.selftext.strip(),
                'object': submission
            })
    return returnList


def commentToSubmission(submission, message):
    submission.reply(message)


def printSubmission(submissions):
    for submission in submissions:
        submission = submission['object']
        print(submission.title, submission.selftext or submission.url, submission.selftext_html, end="\n\n", sep='\n')
    print('\n\t---END---\n')


def reziBot():
    reddit = login()
    for subredditName in SUBREDDIT_NAMES:
        subreddit = reddit.subreddit(subredditName)
        submissions = getNewSubmissions(subreddit=subreddit)
        if len(submissions) == 0:
            continue
        submissions = getDataFromSubmissions(submissions)
        printSubmission(submissions)


if __name__ == '__main__':
    reziBot()

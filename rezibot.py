import praw

BOT_NAME = 'luke_bot'
SUBREDDIT_NAMES = [
    'testlukebot',
]
HOT_WORD = '!roast my resume'
BLACKLISTED_USERS = [
    "Luke_Stone_",
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


def commentToSubmission(submission, message):
    submission.reply(message)


def printSubmission(submissions):
    for submission in submissions:
        print(submission.title, "-", submission.created_utc, "-", submission.selftext, "-", submission.author)
    print("---END---\n")



def reziBot():
    reddit = login()
    for subredditName in SUBREDDIT_NAMES:
        subreddit = reddit.subreddit(subredditName)
        submissions = getNewSubmissions(subreddit=subreddit, hotWord='')
        # printSubmission(submissions)


if __name__ == '__main__':
    reziBot()

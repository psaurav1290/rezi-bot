import praw

subredditName = 'BotTestingPlace'
hotWord = '!roast score'


def login(botName='luke_bot'):
    return praw.Reddit(botName)


def getNewItems(subreddit, limit=None, hotWord=hotWord):
    if limit:
        allNewItems = subreddit.new(limit=limit)
    else:
        allNewItems = subreddit.new()

    # Return all new item if there is no hotword filter
    if not hotWord:
        return allNewItems

    items = []
    # Return filterd new items whose title or text contains the hotword
    for item in subreddit.new(limit=limit):
        if any((hotWord in item.title, hotWord in item.selftext)):
            items.append(item)
    return items


def reziBot():
    reddit = login()
    subreddit = reddit.subreddit(subredditName)
    items = getNewItems(subreddit=subreddit, limit=100, hotWord=None)


if __name__ == '__main__':
    reziBot()

import praw
from praw.models import InlineImage
import random

links = [
    ('https://drive.google.com/file/d/1T4zgVlI3kKXvWiqmRCzECI8PVLtML7ID/view?usp=sharing', 'front-end engineer'),
    ('https://drive.google.com/file/d/1JIIZvQ281AZx7CnWjB_c6SAO2icb9XGI/view?usp=sharing', 'front-end engineer1'),
    ('https://drive.google.com/file/d/1d2vlzInTlQNwFZaFuRB3i2LJTuZF6t86/view?usp=sharing', 'Resume-Saurav'),
    ('https://drive.google.com/file/d/19bl2gWTVIPeI5x4rMFha4YLPUwO-sK67/view?usp=sharing', 'Resume-Saurav-2'),
    ('https://drive.google.com/file/d/1rTZD3zWrEu1VAlPM-kq0Mhy4ESC7pNN2/view?usp=sharing', 'Resume-Saurav-3')
]

badlinks = [
    ('https://drive.google.com/file/d/1rTZD3zWrEu1VAlPM-kq0Mhy4C7pNN2/view?usp=sharing', 'Short File ID'),
    ('https://drive.google.com/file/d/1rTZD3zWrEu1VAlPM-kq0Mhrey4C7pNN2/view?usp=sharing', 'Wrong File ID')
]


def runBot():
    reddit = login('luke_bot')
    reddit.validate_on_submit = True
    subreddit = reddit.subreddit('testlukebot')
    # deleteSubmissions(subreddit)
    # makeSubmissions(subreddit)
    # utcSubmissions(subreddit)
    deleteComments(subreddit)


def login(botName):
    return praw.Reddit(botName)


def makeSubmissions(subreddit):
    for i in range(50):
        choice = random.choice(links)
        print((subreddit.submit(
            "!roast my resume",
            selftext=f"{choice[1]}\n{choice[0]}"
        )).selftext)


def deleteSubmissions(subreddit):
    for submission in subreddit.new():
        print(submission.selftext or submission.url)
        submission.delete()
        break


def utcSubmissions(subreddit):
    count = 1
    for submission in subreddit.new():
        print(count, submission.created_utc)
        count += 1

def deleteComments(subreddit):
    for submission in subreddit.new():
        for comment in submission.comments:
            print(comment.body)
            comment.delete()


if __name__ == '__main__':
    runBot()

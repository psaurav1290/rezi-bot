
# [ReziBOT](https://github.com/psaurav1290/rezi-bot)

It is basic Reddit bot whose sole duty is to crawl across the given set of subreddits and find the hot-word. As soon as it get the hot-word it triggers the action of fetching the resume from the shared link, and commenting back the score of the resume. Currently the service supports only Google Drive and Docdroid share URLs whereas the modular structure of code allows to add any new service seamlessly.

### Key Features
 1. The code base heavily exploits the **object oriented** aspect of Python programming language. Most of the following features are a direct result of this approach
 2. **Easy addition of new services**: as easy as extending the interface class
 3. **Logging** of messages is already implemented
 4. **Custom logger** can be built and implemented for each class just by inheriting the appropriate logger class
 5. **Multi-threading** is used to speed up the bot by concurrently running the network processes
 6. Bot behavior is **easily customizable** since the bot loads all configuration from config.json
 7. **Debug mode** available in bot configuration
 8. This will also allow **easy testing and analysis** of the bot
 9. Respects user privacy. Users can **privately share resume file** with author's google account since the bot accesses the drive files using author's credentials.
 10. **Custom exception classes**: error codes can be later added to each class as class variable
 11. Most of the **exceptions are handled** and logged correctly.
 12. Supports **user blacklisting** such that post from certain users may be ignored without banning them.

## Initial Setup

Clone the repository and install the libraries in *requirements.txt*. Alternatively you can run-
`pip install praw google-api-python-client google-auth-httplib2 google-auth-oauthlib`

**Create .env-**
Create a `.env` file and declare the API endpoint as-

`/.env`
>```
>REZI_SCORE_API_ENDPOINT="https://.../scoreFromFile/"
>```

**Set up OAuth2 credentials to access Reddit API**
To register the app follow the [Steps to register an app on Reddit](https://praw.readthedocs.io/en/latest/tutorials/reply_bot.html#step-1-getting-started). Create a `praw.ini` file and enter the OAuth2 credentials obtained after registering the app in the following format-

`/praw.ini`

>```
>[<Name of Bot>]
>client_id=<14-char>
>client_secret=<30-char>
>password=<user-password>
>username=<user-id>
>user_agent=<os>:<botname>:v1.0 (by u/<user-id>)
>```

Example of a  `/praw.ini` file-
>```
>[Rezi_Bot]
>client_id=XXXXXXXXXXXXX
>client_secret=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
>password=passwd#@123
>username=authorusername
>user_agent=windows:rezi_bot:v2.0 (by r/authorusername)
>```


**Set up OAuth2 credentials to access Drive Files**
Using step 3 and 4 of [Python Quickstart | Google Drive API](https://developers.google.com/drive/api/v3/quickstart/python#prerequisites) get the *client_secret.json*. Precisely
1. [create a project and enable the drive API](https://developers.google.com/workspace/guides/create-project) followed by
2. [configuring the OAuth consent screen](https://developers.google.com/workspace/guides/create-credentials#configure_the_oauth_consent_screen) and
3. Creating the OAuth client ID credential for a [web application](https://developers.google.com/workspace/guides/create-credentials#web-application).

Place the client secret JSON file in `/credentials/drive/client_secret.json`.

**Bot Configuration JSON**
The `/config.json` defines the behavior of the bot.
1. **loops** : Number of times the bot runs (*this behavior and the associated code should be altered according to deployment environment, usually in production the bot runs infinitely at certain intervals*).
2. **sleep-time** : Interval between two iterations
3. **debug**: Takes value 0 (false) and 1(true). In debugging mode, all messages will be logged comments won't be posted online but on in the log file itself. When debugging will be disabled, any message below INFO level will be ignored and comments will be actually posted online on Reddit.
4. **bot-name**: Name of the bot as in `./praw.ini`
5. **subreddits**: The list of subreddits that the bot covers. e.g - if the subreddit is `r/redditdev` just enlist `"redditdev"`
6. **hotWord**: The hot-word which triggers the bot. It searches for it in the title or content of the post.
7. **blacklistedUsers**: The users who are not banned on subreddit but are to be ignored.
8. **limit**: Number of posts to fetch.
*(Note- Keep this 0 to fetch maximum number of recent posts)*
10. **maxThread**: Maximum number of threads that run simultaneously in the `ThreadPoolExecutor` to accomplish the task. This can be altered according to the production environment to achieve maximum efficiency.

## Basic Flow
![(i) Flowchart of the event loop (ii) Lifecycle of Task Object](https://raw.githubusercontent.com/psaurav1290/rezi-bot/master/media/flowchart-1.png)
## About the Author -
This project was made on a freelance contract with **[Rezi | AI-Powerd Free ATS Resume Builder](https://www.rezi.ai/)**. This project helped me a lot in honing my skills and writing clean modular code. I also learned how to write a good readme file. I also discovered several aspecs of Object Oriented Programming, accquired in-depth knowledge about achieving concurrency using multi-threading, fetching files and API responses using requests.

 Saurav Priyadarshi
 [LinkedIn](linkedin.com/in/sauravpriyadarshi90/) | [Github](github.com/psaurav1290/)

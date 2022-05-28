import random

import praw
import time

ignore_list = []


class CommentReplyBot(praw.reddit.Reddit):
    """The CommentReplyBot class creates an authorised reddit instance, and will respond to comments with keywords"""
    def __init__(self, client_id, client_secret, username, password, user_agent, key_and_quotes, bot_id,
                 cooldown):
        super().__init__()
        # things needed to connect / general account info
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.user_agent = user_agent
        self.id = bot_id

        # all the different types of quotes
        self.key_and_quotes = key_and_quotes

        # the cooldown for the bot
        self.cooldown = cooldown
        # initiate and connect to reddit using the values just set up.
        self.reddit = praw.Reddit(client_id=self.client_id,
                                  client_secret=self.client_secret,
                                  username=self.username,
                                  password=self.password,
                                  user_agent=self.user_agent)
        print(f"{self.username} is running as a comment replier")

    def comment_select(self, comment):
        for key in self.key_and_quotes:  # Run this for every key in the quote dictionary
            if key in comment.body.lower():
                print("Key word found")
                reply = random.choice(self.key_and_quotes[key])
                return reply
        return None

    def comment_find(self, subreddits):
        for comment in self.reddit.subreddit(subreddits).stream.comments(skip_existing=True):
            if comment.author.id == self.id:  # check if the comment is one of ours
                print(f"Comment from {self.username} found.")
            elif comment.author.name in ignore_list:
                print("Ignored user found")
            else:
                reply = self.comment_select(comment)

                if reply is not None:
                    comment.reply(reply)
                    time.sleep(self.cooldown)

    def comment_del(self, comment_id):  # this deletes a comment that our account made. Used for double comments.
        comment = self.reddit.comment(comment_id.strip())  # make a comment using the id
        comment.delete()  # delete the comment


class CommentLogger(praw.reddit.Reddit):
    """The CommentLogger creates a read-only reddit instance that will log comments into the specified file."""
    def __init__(self, client_id, client_secret, user_agent, filepath, subreddits, keywords=None, ):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.filepath = filepath
        self.subreddits = subreddits
        self.keywords = keywords

        self.reddit = praw.Reddit(client_id=self.client_id,
                                  client_secret=self.client_secret,
                                  user_agent=self.user_agent)
        print(f"Comment Logger running, pasting comments into {self.filepath}")

    def logger(self, comment_body):  # this function saves the comment into the file
        with open(self.filepath, "a") as file:
            file.write(comment_body)

    def comment_finder(self):   # this function looks for comments
        for comment in self.reddit.subreddit(self.subreddits).stream.comments(skip_existing=True):
            self.logger(comment.body)

    def comment_logger_run(self):   # this function combines the above 2 functions
        while True:
            self.comment_finder()

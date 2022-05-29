import random
import requests
import praw
import time
import os

ignore_list = []


class CommentReplyBot:
    """The CommentReplyBot class creates an authorised reddit instance, and will respond to comments with keywords"""

    def __init__(self, client_id, client_secret, username, password, user_agent, key_and_quotes, bot_id,
                 cooldown):
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


class CommentLogger:
    """The CommentLogger creates a read-only reddit instance that will log comments into the specified file."""

    def __init__(self, client_id, client_secret, user_agent, filepath, subreddits, keywords=None, ):

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

    def comment_finder(self):  # this function looks for comments
        for comment in self.reddit.subreddit(self.subreddits).stream.comments(skip_existing=True):
            print(comment.body)
            self.logger(comment.body)

    def run(self):  # this function combines the above 2 functions
        while True:
            self.comment_finder()


class PostLogger:
    """The PostLogger creates a read-only reddit instance that will download posts into the specified folder. Text
    only posts will create a markup file. Gallery posts will create a new folder. """

    def __init__(self, client_id, client_secret, user_agent, filepath, subreddits):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.filepath = filepath
        self.subreddits = subreddits

        self.reddit = praw.Reddit(client_id=self.client_id,
                                  client_secret=self.client_secret,
                                  user_agent=self.user_agent)
        print(f"PostLogger running, downloading into {self.filepath}")

    @staticmethod
    def image_downloader(image_url, file_path):  # this is what actually downloads the images.
        img_data = requests.get(image_url).content  # access the image
        image_name = str(image_url).split("/")  # split the url to get the file name
        image_name = image_name[len(image_name) - 1]

        with open(f'{file_path}\\{image_name}', 'wb') as handler:  # save the image
            handler.write(img_data)
            handler.close()
        print("Image Downloaded.")

    @staticmethod
    def video_downloader(video_url, file_path):  # currently unused and not working
        # create response object
        video = requests.get(video_url, stream=True)
        # download started
        with open(file_path, 'wb') as f:
            for chunk in video.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    @staticmethod
    def valid_name_maker(submission_title):
        # turn the submission title into the name of the file
        valid_characters = "abcdefghijklmnopqrstuvwxyz1234567890()_- "
        valid_name = ""
        for element in str(submission_title):
            if element.lower() in valid_characters:
                valid_name = valid_name + element

        return str(valid_name)

    def gallery_downloader(self, submission):   # this function places images from galleries into their own folder.

        folder_name = self.valid_name_maker(submission.title)
        gallery_folder = f'{self.filepath}\\{folder_name}'

        if not os.path.exists(gallery_folder):  # check that the folder doesn't already exist
            os.makedirs(gallery_folder)
        else:
            return  # TODO: Add "(x)" at the end of filename if folder already exists, where x is the number of folders
            # with that name

        gallery = []
        gallery_ids = [i['media_id'] for i in submission.gallery_data['items']]
        for ids in gallery_ids:  # extract the image urls from the gallery
            url = submission.media_metadata[ids]['p'][0]['u']
            url = url.split("?")[0].replace("preview", "i")
            gallery.append(url)

        for img in gallery:     # run the downloader for all the images in the gallery list we just made
            self.image_downloader(gallery_folder, img)

    def text_file_writer(self, submission_title, body_text):  # turn the submission title into the name of the file
        valid_name = self.valid_name_maker(submission_title)
        with open(f'{self.filepath}\\{valid_name}.md', 'w+', encoding="utf8") as file:  # create a file
            file.write(body_text)  # write in the text
            file.close()

    def run(self):
        for submission in self.reddit.subreddit(self.subreddits).stream.submissions():
            submission_text = submission.selftext  # get the text of the post
            url = submission.url  # get the url of the post
            if len(submission_text) > 0:
                self.text_file_writer(submission_title=submission.title,
                                      body_text=submission_text)

            elif "i.redd.it" in url:  # check if the submission links to an image
                self.image_downloader(url, self.filepath)

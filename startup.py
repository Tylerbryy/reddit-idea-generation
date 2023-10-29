import praw
import openai
import json
import os
from dotenv import load_dotenv
from halo import Halo
from docx import Document

# Load API keys from .env file
load_dotenv()

# Reddit API setup
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="script by @tylergibbs"
)

# OpenAI API setup
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to fetch posts from a subreddit
def fetch_posts(subreddit_name, post_type="hot", limit=15):
    subreddit = reddit.subreddit(subreddit_name)
    if post_type == "hot":
        return subreddit.hot(limit=limit)
    elif post_type == "new":
        return subreddit.new(limit=limit)
    elif post_type == "top":
        return subreddit.top(limit=limit)
    else:
        raise ValueError("Invalid post type specified. Choose 'hot', 'new', or 'top'.")

# Function to generate startup ideas using OpenAI with retries
@Halo(text='Processing', spinner='dots')
def generate_startup_idea(post_title, post_content):
    retries = 0
    while retries < 10:  # Maximum 10 retries
        try:
            messages = []
            messages.append({"role": "user", "content": f"Here is a Reddit post titled '{post_title}' with the content: '{post_content}'. Can you suggest a startup idea based on this post?"})

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"API Error: {e}")
            retries += 1
            if retries >= 10:
                return None
# Main script execution
subreddit_name = input("Enter the subreddit name: ")
post_type = input("Enter the type of posts to fetch (hot, new, top): ").lower()
# Function to save ideas to a DOCX file
def save_to_docx(ideas, filename=f"startup_ideas_{subreddit_name}_{post_type}.docx"):
    doc = Document()
    doc.add_heading('Startup Ideas', 0)

    for idea in ideas:
        doc.add_heading(idea['post_title'], level=1)
        doc.add_paragraph(idea['startup_idea'])

    doc.save(filename)
    print(f"Startup ideas have been saved to '{filename}'.")


try:
    posts = fetch_posts(subreddit_name, post_type=post_type)
except ValueError as e:
    print(e)
    exit()

ideas = []
for post in posts:
    print(f"Analyzing post: {post.title}")
    idea = generate_startup_idea(post.title, post.selftext)
    if idea:
        ideas.append({
            "post_title": post.title,
            "startup_idea": idea
        })
    else:
        print("No viable startup idea found or API limit reached for this post.\n")

# Ask user for preferred output format
output_format = input("Choose the output format (docx or json): ").lower()

if output_format == "docx":
    save_to_docx(ideas)
elif output_format == "json":
    # Output results to a JSON file
    with open(f'startup_ideas_{subreddit_name}_{post_type}.json', 'w', encoding='utf-8') as f:
        json.dump(ideas, f, ensure_ascii=False, indent=4)
    print("Startup ideas have been saved to 'startup_ideas.json'.")
else:
    print("Invalid output format selected. Please choose either 'docx' or 'json'.")

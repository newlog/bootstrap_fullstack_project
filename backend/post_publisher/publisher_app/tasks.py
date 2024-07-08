from celery import shared_task
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
#from .models import Post

WORDPRESS_URL = "https://your-wordpress-site.com/wp-json/wp/v2"
USERNAME = "your_username"
APPLICATION_PASSWORD = "your_application_password"

@shared_task
def publish_post(post_id):
    post = Post.objects.get(id=post_id)
    if post.platform == 'wordpress':
        url = f"{WORDPRESS_URL}/posts"
        data = {
            "title": post.title,
            "content": post.content,
            "status": "publish"
        }
        response = requests.post(url, json=data, auth=HTTPBasicAuth(USERNAME, APPLICATION_PASSWORD))
        
        if response.status_code == 201:
            print(f"Successfully published post: {post.title}")
        else:
            print(f"Failed to publish post: {post.title}. Status code: {response.status_code}")
            print(f"Response: {response.json()}")
    else:
        print(f"Unsupported platform: {post.platform}")


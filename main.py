import json
import urllib.parse
import os
import toml
import requests
import time

from wordpress_xmlrpc import Client
from xmlrpc.client import ProtocolError
from wordpress_xmlrpc import WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost

# Kafkai APIs
BASE_URL = 'https://app.kafkai.com/api/v1'
LOGIN_URL = BASE_URL+'/user/login'
GENERATE_URL = BASE_URL+'/articles/generate'
GET_ARTICLE_URL = BASE_URL+'/articles/'

kafkai_email = ''
kafkai_password = ''
websites = []

auth_token = ''
article_title = ''
article_body = ''


def loadConfig():
    global kafkai_email, kafkai_password, websites
    print('\nStep-X: Load the configurations for the Kafkai and websites')
    try:
        data = toml.load("config.txt")

        kafkai_email = data['kafkai_email']
        kafkai_password = data['kafkai_password']
        websites = data['websites']

        print(f'\tKafkai Email: "{kafkai_email}"')
        print(f'\tKafkai Password: "{kafkai_password}"')
        print('\tWebsites:-')
        print(json.dumps(websites, indent=4))

    except:
        print('\tERROR: config.txt file is missing or incorrect format.')
        exit()


def kafkai_login():
    global auth_token
    print('\nStep-0: Login to the Kafkai')
    try:
        resp = requests.post(
            LOGIN_URL, json={'email': kafkai_email, 'password': kafkai_password})

        if resp.status_code == 200:
            result = resp.json()
            if "token" in result:
                auth_token = result['token']
                return True
        else:
            print('\tERROR: ', resp.text)

    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


def generate_article(niche):
    try:
        resp = requests.post(
            GENERATE_URL,
            headers={"Authorization": "Bearer %s" % auth_token},
            json={'niche': niche, 'title': ''})

        if resp.status_code == 200:
            result = resp.json()
            if "id" in result:
                return result['id']
        else:
            print('\tERROR: ', resp.text)

    except requests.exceptions.RequestException as e:
        print('\tERROR: ', e)


def get_generated_article(article_id):
    global article_title, article_body
    try:
        resp = requests.get(GET_ARTICLE_URL+article_id,
                            headers={"Authorization": "Bearer %s" % auth_token})

        if resp.status_code == 200:
            result = resp.json()
            if "state" in result:
                if result['state'] != "Pending":
                    article_title = result['title']
                    article_body = result['body']
                    return True
        else:
            print('\tERROR: ', resp.text)

    except requests.exceptions.RequestException as e:
        print('\tERROR: ', e)


def post_new_article(wp, title, desc):
    post = WordPressPost()
    post.title = title
    post.content = desc
    post.post_status = 'publish'
    post.id = wp.call(NewPost(post))


if __name__ == "__main__":
    # Step-X: Load the configurations for the Kafkai and websites
    loadConfig()

    # Step-0: Login to the Kafkai
    if kafkai_login() and auth_token != '':
        print('\tLogin successfully.')

        for idx, website in enumerate(websites):
            # Step-1: Generate articles
            print(f'\nStep-1: (Web#{idx+1}) Generate an article')
            print('\tWebsite URL: ', website['url'])
            print('\tWebsite Niche: ', website['niche'])

            article_id = generate_article(website['niche'])
            if article_id:
                print('\tWait for a min.')
                time.sleep(60)

                # Step-2: Get the generated article
                print(f'\nStep-2: (Web#{idx+1}) Get the generated article')
                print('\tArticle ID: ', article_id)
                article_title = ''
                article_body = ''
                if get_generated_article(article_id) and article_title != '' and article_body != '':
                    print('\tArticle Title: ', article_title)

                    # Step-3: Login to WordPress website
                    print(
                        f'\nStep-3: (Web#{idx+1}) Login to WordPress website')
                    url = urllib.parse.urljoin(website['url'], 'xmlrpc.php')
                    wp = Client(url,
                                website['username'],
                                website['password'])

                    # Step-3: Post the generated article
                    print(
                        f'\nStep-4: (Web#{idx+1}) Post the generated article')
                    post_new_article(wp, article_title, article_body)

                else:
                    print('\tFailed to get generated article.')
            else:
                print('\tFailed to generate an article.')

            print('\n')

    else:
        exit()

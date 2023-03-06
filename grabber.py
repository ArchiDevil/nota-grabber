import requests


def signin(sess: requests.Session,
           url: str,
           username: str,
           password: str) -> None:
    sess.post(url, timeout=10, data={
        'login[login]': username,
        'login[pass]': password,
    })


def grab_page(sess: requests.Session,
              url: str) -> str:
    return sess.get(url, timeout=10).text

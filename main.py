import argparse
import json
from pathlib import Path
import time
from typing import Callable

import requests

from html_parser import parse_chapters, parse_pages, parse_segments
from grabber import signin, grab_page


def run_tasks(tasks: list[Callable]):
    while tasks:
        time.sleep(0.25)  # wait 250 ms to avoid spamming
        print(f'Tasks left: {len(tasks)}')
        task = tasks.pop()
        task()


def task_parse_page(tasks: list[Callable],
                    sess: requests.Session,
                    page_link: str):
    # print(f'Parsing {page_link}')
    page = grab_page(sess, page_link)
    doc = [{
        'original': segment['original'],
        'translation': segment['translation'],
    } for segment in parse_segments(page)]
    book_id = page_link.split('/')[-2]
    chapter_id = page_link.split('/')[-1].split('?')[0]
    page_id = page_link.split('=')[-1]
    output_path = Path('.') / 'books' / book_id / f'{chapter_id}'
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / f'{page_id}.json'
    with open(json_path, 'w', encoding='utf-8') as fp:
        json.dump(doc, fp, ensure_ascii=False, indent=2)


def task_parse_chapter(tasks: list[Callable],
                       sess: requests.Session,
                       chapter_link: str):
    # print(f'Parsing {chapter_link}')
    page = grab_page(sess, chapter_link)
    for page in parse_pages(page):
        page_link = chapter_link + page['href']
        tasks.append(lambda pl=page_link: task_parse_page(tasks, sess, pl))


def task_parse_book(tasks: list[Callable],
                    login: str,
                    password: str,
                    book_id: str):
    sess = requests.Session()
    signin(sess, 'http://notabenoid.org/', login, password)

    book_dir = Path('.') / 'books' / book_id
    book_dir.mkdir(parents=True, exist_ok=True)

    page = grab_page(sess, f'http://notabenoid.org/book/{book_id}')
    for chapter in parse_chapters(page):
        chapter_link = 'http://notabenoid.org' + chapter['href']
        tasks.append(
            lambda cl=chapter_link: task_parse_chapter(tasks, sess, cl))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--login', type=str, required=True)
    parser.add_argument('--password', type=str, required=True)
    parser.add_argument('--book', type=str, required=True)

    args = parser.parse_args()
    login = args.login
    password = args.password
    book_id = args.book

    tasks = []
    tasks.append(lambda: task_parse_book(tasks, login, password, book_id))
    run_tasks(tasks)


if __name__ == '__main__':
    main()
import argparse
import json
from pathlib import Path
import sys
import time
from typing import Callable

import requests
from tqdm import tqdm

from html_parser import parse_chapters, parse_pages, parse_segments, parse_book
from grabber import signin, grab_page


def file_filepath(text: str) -> str:
    text = text.replace('/', '_').replace(':', '_').replace('?', '_')
    text = text.replace('|', '_').replace('*', '_').replace('<', '_')
    text = text.replace('>', '_').replace('"', '_').replace('“', '_')
    return text.replace('!', '_').replace('”', '')


def run_tasks(tasks: list[Callable]):
    for i in tqdm(range(len(tasks)), desc='Parsing pages: '):
        time.sleep(0.1)  # to avoid spamming
        task = tasks[i]
        task()


def task_parse_page(sess: requests.Session,
                    page_link: str,
                    chapter_path: Path):
    page = grab_page(sess, page_link)
    doc = [{
        'original': segment['original'],
        'translation': segment['translation'],
    } for segment in parse_segments(page)]
    page_id = page_link.split('=')[-1]
    json_path = chapter_path / f'{page_id}.json'
    with open(json_path, 'w', encoding='utf-8') as fp:
        json.dump(doc, fp, ensure_ascii=False, indent=2)


def get_chapter_tasks(sess: requests.Session,
                      chapter_link: str,
                      chapter_path: Path):
    tasks: list[Callable] = []
    page = grab_page(sess, chapter_link)
    for page in parse_pages(page):
        page_link = chapter_link + page['href']
        tasks.append(lambda pl=page_link,
                     cp=chapter_path: task_parse_page(sess, pl, cp))
    return tasks


def get_book_tasks(login: str, password: str, book_id: str):
    print('Getting book pages...')
    sess = requests.Session()
    signin(sess, 'http://notabenoid.org/', login, password)

    page = grab_page(sess, f'http://notabenoid.org/book/{book_id}')
    book_name = file_filepath(parse_book(page)['name'])

    book_path = Path('.') / 'books' / f'{book_id} - {book_name}'
    book_path.mkdir(parents=True, exist_ok=True)

    tasks: list[Callable] = []

    for chapter in tqdm(parse_chapters(page), desc='Getting pages: '):
        time.sleep(0.1) # to avoid spamming
        chapter_id = chapter['href'].split('/')[-1]
        chapter_name = file_filepath(chapter['text'])
        chapter_path = book_path / f'{chapter_id} - {chapter_name}'
        chapter_path.mkdir(parents=True, exist_ok=True)

        chapter_link = 'http://notabenoid.org' + chapter['href']
        tasks += get_chapter_tasks(sess, chapter_link, chapter_path)

    return tasks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='config.json', type=str)
    parser.add_argument('-b', '--book', type=str, required=True)

    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print('No config file provided.')
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as fp:
        config = json.load(fp)

    if not config.get('login') or not config.get('password'):
        print('No login or password provided.')
        sys.exit(1)

    login = config['login']
    password = config['password']
    book_id = args.book

    tasks = get_book_tasks(login, password, book_id)
    run_tasks(tasks)


if __name__ == '__main__':
    main()

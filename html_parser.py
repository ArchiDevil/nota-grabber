from typing import Literal

from bs4 import BeautifulSoup
import bs4


TChapterKeys = Literal['href', 'text']
TPageKeys = Literal['href', 'text']


def parse_chapters(html: str) -> list[dict[TChapterKeys, str]]:
    soup = BeautifulSoup(html, 'html.parser')
    chapters = soup.find_all('td', class_='t')
    return [{
        'href': chapter.a['href'],
        'text': chapter.a.text
    } for chapter in chapters]


def parse_pages(html: str) -> list[dict[TPageKeys, str]]:
    soup = BeautifulSoup(html, 'html.parser')
    pages_list = soup.find('div', class_='chic-pages')

    first_page = [{
        'href': '?Orig_page=1',
        'text': '1'
    }]

    if not pages_list:
        return first_page

    assert isinstance(pages_list, bs4.Tag)

    links = pages_list.find_all('a')
    assert links

    return first_page + [
        {
            'href': link['href'],
            'text': link.text
        } for link in links if link.text != '→']


def parse_segments(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    originals = soup.find_all('td', class_='o')
    translations = soup.find_all('td', class_='t')
    return [
        {
            'original': o.find('p', class_='text').text,
            'translation': t.find('p', class_='text').text
        } for o, t in zip(originals, translations)]


TBookKeys = Literal['name']

def parse_book(html: str) -> dict[TBookKeys, str]:
    soup = BeautifulSoup(html, 'html.parser')
    h1 = soup.find('h1')
    assert h1 and isinstance(h1, bs4.Tag)
    return {
        'name': h1.text
    }

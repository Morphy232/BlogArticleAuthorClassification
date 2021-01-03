"""
The file `scrapper.py` contains all the necessary classes, including Article, ArticleEncoder and Scrapper
to scrap page `kosmonautix.cz` and then dump the result into a json format.
"""

from dataclasses import dataclass
from datetime import datetime
import json
import locale
import time
import requests

from typing import List, Optional
from bs4 import BeautifulSoup


@dataclass
class Article:
    """Dataclass that describes an article.

    Attributes:
        title: string that represents title of the article
        author: string that represents author of the article
        date: datetime that represents release date of the article
        content_paragraphs: list of strings that represents all the content in paragraphs
    """

    title: Optional[str]
    author: Optional[str]
    date: Optional[datetime]
    content_paragraphs: Optional[List[str]]


class ArticleEncoder(json.JSONEncoder):
    """Encoder that is derived from JSONEncoder and is used to encode datetime and Article dataclass to json format."""

    def default(self, obj):
        if isinstance(obj, Article):
            return obj.__dict__
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Base class default() raises TypeError:
        return json.JSONEncoder.default(self, obj)


class Scrapper:
    """Scrapper that is used to scrap given count of articles from kosmonautix.cz page.

    Attributes:
        article_count: a positive int indicating how many articles are to be scrapped, by default 1.000
        start_page: a positive int indicating page from where to start, by default is 1
        sleep_time: seconds to sleep between each request to not get banned, by default is 0
        verbose: bool that indicates whether scrapper should print out information, by default is False
        parser: string of parser to be used by BeatifulSoap, by defaul is "lxml"
    """

    __url_prefix: str = "https://kosmonautix.cz/page/"

    __date_format: str = "%d. %B %Y"

    __article_selector_prefix: str = "div #content div >"
    __link_selector_suffix: str = "h2.title > a"
    __title_selector_suffix: str = "h2.title"
    __author_selector_suffix: str = "div.postdate > a.author"
    __date_selector_suffix: str = "div.postdate"
    __content_selector_suffix: str = "div.entry p"

    __link_selector: str = f"{__article_selector_prefix} {__link_selector_suffix}"
    __title_selector: str = f"{__article_selector_prefix} {__title_selector_suffix}"
    __author_selector: str = f"{__article_selector_prefix} {__author_selector_suffix}"
    __date_selector: str = f"{__article_selector_prefix} {__date_selector_suffix}"
    __content_selector: str = f"{__article_selector_prefix} {__content_selector_suffix}"

    def __init__(
        self,
        article_count: int = 1000,
        start_page: int = 1,
        sleep_time: int = 0,
        verbose: bool = False,
        parser: str = "lxml",
    ):
        """Initializes all attributes of scrapper described in class docstring."""

        if verbose:
            print(f"Initializing verbose scrapper.")
        self.__article_count: int = article_count
        self.__start_page: int = start_page
        self.__sleep_time: int = sleep_time
        self.__verbose: bool = verbose
        self.__parser: str = parser
        self.__article_links: List[str] = []
        self.__articles: List[Article] = []
        locale.setlocale(locale.LC_TIME, "cs_CZ.utf8")

    def __extract_page_article_links(self, page_url: str, maximum: int) -> int:
        """Extracts up to maximum article links from given page url and returns amount of links extracted."""

        res = requests.get(page_url)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, self.__parser)

        article_title_nodes = soup.select(self.__link_selector)
        extracted = 0
        for article_title_node in article_title_nodes:
            if extracted == maximum:
                break

            link_url = article_title_node.attrs.get("href")
            if link_url is not None:
                self.__article_links.append(link_url)
                extracted += 1

        if self.__verbose:
            print(f"Extracted {extracted} article links from page {page_url}")
        return extracted

    def __extract_all_article_links(self):
        """Extracts all article links from url specified as url prefix constant in the class."""

        if self.__verbose:
            print("Extracting all article links")
        extracted_count = 0
        current_page = self.__start_page
        while extracted_count < self.__article_count:
            url = f"{self.__url_prefix}{current_page}"
            try:
                extracted_count += self.__extract_page_article_links(
                    url, self.__article_count - extracted_count
                )
            except Exception as e:  # extracting article links failed for given page failed so stop
                if self.__verbose:
                    print(
                        f"Exception while extracting links for page {current_page} occured."
                    )
                    print(e)
                break
            time.sleep(self.__sleep_time)
            current_page += 1

    def __extract_node_text(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """Extracts text from given node specified by a soup and selector."""

        candidates = soup.select(selector)
        if not candidates:
            return None
        text = candidates[0].get_text()
        return text.strip() if text is not None else None

    def __extract_article_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extracts article title based on title selector constant specified in the class."""

        return self.__extract_node_text(soup, self.__title_selector)

    def __extract_article_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extracts article author based on author selector constant specified in the class."""

        return self.__extract_node_text(soup, self.__author_selector)

    def __extract_article_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extracts article date based on date selector constant specified in the class."""

        date_raw = self.__extract_node_text(soup, self.__date_selector)
        if date_raw is None:
            return None
        date_raw = " ".join(date_raw.split(" ")[:3])
        return datetime.strptime(date_raw, self.__date_format)

    def __extract_article_content(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extracts list of paragraphs as content based on content selector constant specified in the class."""

        paragraph_nodes = soup.select(self.__content_selector)
        if paragraph_nodes is None:
            return None
        # get texts of all nodes and strip trailing spaces
        paragraph_node_texts = [node.getText().strip() for node in paragraph_nodes]

        # check last 3 paragraphs if they are not source paragraphs (in czech 'Zdroje')
        # also check if the paragraph does not include phrase 'Přeloženo'
        # (source of translated article)
        pop = 0
        for i in range(1, 4):
            if len(paragraph_node_texts) < i:
                break
            lower_text = paragraph_node_texts[-i].lower()
            if lower_text.startswith("zdroje") or lower_text.startswith("přeloženo"):
                pop += 1

        # remove all the paragraphs that are not considered text
        for i in range(pop):
            paragraph_node_texts.pop()

        # filter out paragraphs that are for some reason None or empty
        return [*filter(lambda p: p is not None and p != "", paragraph_node_texts)]

    def __extract_article(self, url: str) -> Article:
        """Extracts a single article based on given url."""

        if self.__verbose:
            print(f"Extracting article from url {url}")
        res = requests.get(url)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, self.__parser)
        return Article(
            self.__extract_article_title(soup),
            self.__extract_article_author(soup),
            self.__extract_article_date(soup),
            self.__extract_article_content(soup),
        )

    def __extract_all_articles(self) -> List[Article]:
        """Extracts and returns all articles based on article links."""

        if self.__verbose:
            print(f"Extracting all articles.")
        for url in self.__article_links:
            self.__articles.append(self.__extract_article(url))
            time.sleep(self.__sleep_time)
        return self.__articles

    @property
    def articles(self) -> List[Article]:
        """Articles getter."""

        return self.__articles

    def reset(self, reset_links: bool = True) -> "Scrapper":
        """Resets downloaded articles and can also reset links, then returns reference to self for chaining."""

        if self.__verbose:
            print(f"Resetting parser.")
        self.__articles = []
        if reset_links:
            self.__article_links = []
        return self

    def run(self) -> List[Article]:
        """Runs the scrapper and returns list of articles."""

        if self.__verbose:
            print(f"Running scrapper.")
        # if articles are non-empty then return them
        if self.__articles:
            return self.__articles

        # extract all article links in case they are empty
        if not self.__article_links:
            self.__extract_all_article_links()

        # extract all articles from previously extracted article links
        return self.__extract_all_articles()

    def scrap_article(self, url: str) -> Optional[Article]:
        """Scraps article from given url and returns None if the url is not responding."""

        try:
            return self.__extract_article(url)
        except BaseException:
            return None

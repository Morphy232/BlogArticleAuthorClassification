"""
Usage: python3 main.py ARTICLE_COUNT OUTPUT_PATH SLEEP

Scraps ARTICLE_COUNT articles from `kosmonautix.cz` and stores them into OUTPUT_PATH.

ARTICLE_COUNT - positive int that describes count of articles to scrap
OUTPUT_PATH - string path, where to store the json result
SLEEP - non-negative int that describes seconds to sleep between each request
"""

import sys
import json
import dataclasses
import scrapper


def main() -> int:
    """Runs the main."""

    if "-h" in sys.argv or "--help" in sys.argv:
        print(f"Usage: python3 {sys.argv[0]} ARTICLE_COUNT OUTPUT_PATH SLEEP")
        return 0

    if len(sys.argv) < 4:
        print("Not enough arguments.")
        return 1
    try:
        article_count: int = int(sys.argv[1])
        output_path: str = sys.argv[2]
        sleep: int = int(sys.argv[3])
        if sleep < 0 or article_count < 0 or output_path.strip() == "":
            raise BaseException
    except BaseException:
        print("Parsing input failed.")
        return 1

    # scrap articles
    articles = scrapper.Scrapper(article_count, 1, sleep_time=sleep, verbose=True).run()

    # dump into json
    out_file = open(output_path, "w")
    json.dump(
        articles, out_file, indent=6, ensure_ascii=False, cls=scrapper.ArticleEncoder
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Scrapper

Script that is used to scrap articles from `kosmonautix.cz`.

## Synopsis

```
user$ python3 main.py ARTICLE_COUNT OUTPUT_PATH SLEEP
...
Scraps ARTICLE_COUNT articles from `kosmonautix.cz` and stores them into OUTPUT_PATH.
```

## Options and Arguments

* `ARTICLE_COUNT`: positive int that describes count of articles to scrap
* `OUTPUT_PATH`: string path, where to store the json result
* `SLEEP`: non-negative int that describes seconds to sleep between each request

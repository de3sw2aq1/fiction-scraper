# fiction-scraper

> A variety of scrapers for online fiction and fanfiction

`fiction-scraper` can download a online stories for offline reading. With built-in Pandoc integration you can easily create EPUB ebooks to read anywhere.

## Usage

Use it something like this:

```
$ ./fiction-scraper -o ra.epub https://qntm.org/ra
```

Or here's the full usage info:

```
usage: fiction-scraper [-h] [-o OUTPUT] [-p] [-v] [-d] URL

A variety of scrapers for online fiction and fanfiction

positional arguments:
  URL                   URL of story to download

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file for the story. Unless Pandoc is disabled,
                        the story will be postprocesed using Pandoc. Pandoc
                        will autodetect the output file format from the file
                        extension. If omitted, HTML will be written to
                        standard output.
  -p, --no-pandoc       Don't postprocess story with Pandoc, HTML output only
  -v, --verbose         Verbose output
  -d, --debug           Debug output

Suppported sites and sample URLs:

  City of Roses         http://thecityofroses.com/
  Keira Marcos fanfiction http://keiramarcos.com/fan-fiction/harry-potter-the-soulmate-bond/
  Sam Huges fiction     https://qntm.org/ra
  Starwalker            http://www.starwalkerblog.com/
  Worm                  https://parahumans.wordpress.com/

Note, some sites may have multiple stories at additional URLs.
```

`fiction-scraper` may be able to download specific "book" or section of a site instead of the entrire story if you pass it the book's URL.

If requ need Kindle version of your ebook in .mobi format, you need to use an external tool. [Calibre] or [kindlegen] should be able to process the EPUB files created with Pandoc.

## Installation

First [install Poetry] and [Pandoc], then from this directory just run:

```
$ poetry install
```

You must run `fiction-scraper` you must from inside the virtualenv:

```
$ poetry shell
$ ./fiction-scraper -o ra.epub https://qntm.org/ra
```

I may get around to writing a setup.py and removing the poetry dependency for users if enough people use this.

## Supported Sites

*  [City of Roses](http://thecityofroses.com/) 
*  Any [Keira Marcos fanfiction](http://keiramarcos.com/fan-fiction/)
*  [Sam Huges's (qntm.org) fiction](https://qntm.org/fiction)
*  [Starwalker](http://www.starwalkerblog.com/) by Melanie Edmonds
*  [Worm](https://parahumans.wordpress.com/) by John McCrae, a.k.a. Wildbow

## License

All code is MIT licensed. But most of the downloaded stories are not! Stories downloaded with `fiction-scraper` should not be freely distributed without permission of their author.

[Calibre]: https://calibre-ebook.com/
[kindlegen]: https://www.amazon.com/gp/feature.html?docId=1000765211
[install Poetry]: https://github.com/sdispater/poetry#installation
[Pandoc]: https://pandoc.org/

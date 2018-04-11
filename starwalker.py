import os
import sys
from tempfile import NamedTemporaryFile
from lxml.html import builder as E
import requests
import scraper

URL_ALL = 'http://www.starwalkerblog.com/'
URL_SUMMARY = 'http://www.starwalkerblog.com/about/about-starwalker/'
URL_COVER = 'http://www.starwalkerblog.com/wp-content/uploads/2012/07/Spiral2_sm.jpg'
EXTRA_PAGES = [
    'http://www.starwalkerblog.com/cast/',
    'http://www.starwalkerblog.com/colonies/',
    'http://www.starwalkerblog.com/terminology/',
    'http://www.starwalkerblog.com/about/about-the-author/'
]

CHAPTER_LEVEL = 3

def heading(level, text, **kwargs):
    return E.E('h'+str(level), text, **kwargs)


def process_subcategories(document, url, level=0):
    doc = document.fetch_doc(url)
    categories = doc.get_element_by_id('categories')

    if url == URL_ALL:
        category = categories
        document.metadata['title'] = 'Starwalker'
    else:
        category = categories.xpath('.//li[a[@href=$url]]', url=url)
        if not category:
            raise LookupError('Could not find category in TOC')

        category = category[0]
        title, = category.xpath('a/text()')

        if level == 0:
            document.metadata['title'] = 'Starwalker ' + str(title)
        else:
            document.write(heading(level, title))

    subcategory_urls = category.xpath('ul/li/a/@href')

    # "4.4: Rosetta" contains both chapters and the 
    # subcategory "Book 4 Alt Timeline"
    if not subcategory_urls or url == 'http://www.starwalkerblog.com/category/4-black-star/rosetta/':
        # Add ?order=asc because some categories are in reverse order
        process_category(document, url+'?order=asc')

    for subcategory_url in subcategory_urls:
        # Skip author's notes
        if subcategory_url == 'http://www.starwalkerblog.com/category/authors-notes/':
            continue
        # Reduce nesting level of alt timeline
        elif subcategory_url == 'http://www.starwalkerblog.com/category/4-black-star/rosetta/book-4-alt-timeline/':
            process_subcategories(document, subcategory_url, level)
        else:
            process_subcategories(document, subcategory_url, level+1)

    # Extra pages if all sections are included
    if url == URL_ALL:
        for url in EXTRA_PAGES:
            process_page(document, url, level=1)


def process_category(document, url):
    doc = document.fetch_doc(url)

    for page_url in doc.xpath('//h3/a/@href'):
        process_page(document, page_url, category_url=url)

    prev_page = doc.cssselect('.navigation .alignleft a')
    if prev_page:
        process_category(document, prev_page[0].get('href'))


def process_page(document, url, category_url=None, level=CHAPTER_LEVEL):
    doc = document.fetch_doc(url)

    # If we are processing Alt timeline pages when we only want Rosetta pages, skip them
    # The page's category will be more specific than the desired category_url
    for c in doc.xpath('//a[@rel="category tag"]'):
        if category_url and not category_url.startswith(c.get('href')):
            return

    title, = doc.xpath('//h3[@class="posttitle"]/a/text()')
    document.write(heading(level, title))

    # Blog posts use .entry and pages use .entrytext
    content, = doc.cssselect('.entrytext, .entry')

    # Remove share links
    for tag in content.cssselect('.reaction_buttons, .sharedaddy'):
        tag.getparent().remove(tag)

    # Convert headings (only from EXTRA_PAGES) to <h4>
    for tag in content.iter():
        if tag.tag[0] == 'h':
            tag.tag = 'h'+str(CHAPTER_LEVEL+1)

    document.write(*content)


def process_summary(document):
    doc = document.fetch_doc(URL_SUMMARY)
    summary_paragraphs = doc.xpath('//div[@class="entrytext"]/p')
    summary = '\n\n'.join(p.text_content().strip() for p in summary_paragraphs)
    document.metadata['description'] = summary


def process_cover_image():
    cover = NamedTemporaryFile(suffix='.jpg', delete=False)
    cover.write(
        requests.get(URL_COVER).content
    )
    cover.close()
    return cover.name


def main():
    if len(sys.argv) < 2 or not sys.argv[-1].startswith('http://www.starwalkerblog.com/'):
        print('Usage:', sys.argv[0], '[PANDOC_ARGS, ...]', 'URL', file=sys.stderr)
        print('Where URL is:', file=sys.stderr)
        print('  the URL http://www.starwalkerblog.com/', file=sys.stderr)
        print('  or a specific category link from the table of contents', file=sys.stderr)
        sys.exit(1)
    
    pandoc_args = sys.argv[1:-1]
    url = sys.argv[-1]

    try:
        cover = process_cover_image()

        # Set EPUB chapter level to 3 (CHAPTER_LEVEL) because there are categories
        with scraper.Document('--epub-chapter-level', str(CHAPTER_LEVEL), *pandoc_args) as d:
            process_summary(d)
            process_subcategories(d, url)

            d.metadata['author'] = 'Melanie Edmonds'
            d.metadata['cover-image'] = cover
            # TODO: add stylesheets (for <pre> tags, etc)
    finally:
        os.unlink(cover)


if __name__ == '__main__':
    main()

import logging
import sys

from lxml.html import document_fromstring, tostring, clean, builder as E
import requests

from utils.pandoc import Pandoc

logging.basicConfig()
logger = logging.getLogger('keiramarkos')
logger.setLevel(logging.INFO)

clean = clean.Cleaner(
    remove_tags=('div', 'span', 'a'),
    safe_attrs=clean.Cleaner.safe_attrs - {'class', 'width', 'height'}
)

pandoc = None

# TODO: write generic filter to convert dashes to <hr>

def write(*elements):
    for e in elements:
        pandoc.write(tostring(e))

def process_index(url):
    logger.info('Processing story: %s', url)
    doc = document_fromstring(requests.get(url).content)

    title = str(doc.xpath('//meta[@property="og:title"]/@content')[0])
    pandoc.metadata['title'] = title
    pandoc.metadata['author'] = 'Keira Markos'

    content, = doc.find_class('entry-content')
    index_div = content.find_class('wordpress-post-tabs')
    chapter_links = content.xpath('.//a[contains(text(), "Chapter")]')

    if index_div:
        # FIXME: a couple stories actually put the whole text of the story
        # in wordpress-post-tabs, not just links
        chapter_links = index_div[0].xpath('.//div[starts-with(@id, "tabs-")][1]//a')
        content.remove(index_div[0])
    elif chapter_links:
        logger.warning('Using terrible heuristics to find chapter links')
        for link in chapter_links:
            # This also kills the tail text, but that is actually desirable
            link.getparent().remove(link)
    else:
        # This is a single chapter story
        process_chapter(url, strip_authors_note=False)
        return

    clean(content)
    write(*content.getchildren())

    for link in chapter_links:
        write(E.H1(link.text_content()))
        process_chapter(link.get('href'))

def process_chapter(url, strip_authors_note=True):
    logger.info('Processing chapter: %s', url)
    doc = document_fromstring(requests.get(url).content)

    content, = doc.find_class('entry-content')

    # Remove author's note, etc
    if strip_authors_note:
        first_tag = content.getchildren()[0]
        if 'Title:' in first_tag.text_content():
            content.remove(content.getchildren()[0])

    # Remove blog share links
    for div in content.find_class('sharedaddy'):
        content.remove(div)

    # Remove link to next chapter (any link in last paragraph)
    last_link = content.xpath('*[last()]//a')
    if last_link:
        logger.debug('Removing last_link: %s', tostring(last_link[0], encoding=str))
        last_link[0].getparent().remove(last_link[0])

    # Find any other links back to the series index
    # This catches some links after "The End" sometimes
    other_link = content.xpath('*//a[starts-with(@href, "http://keiramarcos.com/fan-fiction")]')
    if other_link:
        logger.debug('Removing other_link: %s', tostring(other_link[0], encoding=str))
        other_link[0].getparent().remove(other_link[0])

    clean(content)
    write(*content.getchildren())

def main():
    global pandoc

    if len(sys.argv) < 2 or not sys.argv[-1].startswith('http://keiramarcos.com/fan-fiction/'):
        print('Usage:', sys.argv[0], '[PANDOC_ARGS, ...]', 'URL', file=sys.stderr)
        print('Where URL is a link to a story from http://keiramarcos.com/fan-fiction/', file=sys.stderr)
        sys.exit(1)
    
    pandoc_args = sys.argv[1:-1]
    url = sys.argv[-1]

    logger.info('Starting Pandoc')
    with Pandoc(*pandoc_args) as p:
        pandoc = p
        process_index(url)

if __name__ == '__main__':
    main()
import sys
from lxml.html import clean, builder as E
import scraper

clean = clean.Cleaner(
    remove_tags=('div', 'span', 'a'),
    safe_attrs=clean.Cleaner.safe_attrs - {'class', 'width', 'height'}
)

# TODO: write generic filter to convert dashes to <hr>

def process_index(document, url):
    doc = document.fetch_doc(url)
    title = str(doc.xpath('//meta[@property="og:title"]/@content')[0])
    document.metadata['title'] = title
    document.metadata['author'] = 'Keira Markos'

    content, = doc.find_class('entry-content')
    index_div = content.find_class('wordpress-post-tabs')
    chapter_links = content.xpath('.//a[contains(text(), "Chapter")]')

    if index_div:
        # FIXME: a couple stories actually put the whole text of the story
        # in wordpress-post-tabs, not just links
        chapter_links = index_div[0].xpath('.//div[starts-with(@id, "tabs-")][1]//a')
        content.remove(index_div[0])
    elif chapter_links:
        for link in chapter_links:
            # This also kills the tail text, but that is actually desirable
            link.getparent().remove(link)
    else:
        # This is a single chapter story
        process_chapter(document, url, strip_authors_note=False)
        return

    clean(content)
    document.write(*content.getchildren())

    for link in chapter_links:
        document.write(E.H1(link.text_content()))
        process_chapter(document, link.get('href'))

def process_chapter(document, url, strip_authors_note=True):
    doc = document.fetch_doc(url)

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
        last_link[0].getparent().remove(last_link[0])

    # Find any other links back to the series index
    # This catches some links after "The End" sometimes
    other_link = content.xpath('*//a[starts-with(@href, "http://keiramarcos.com/fan-fiction")]')
    if other_link:
        other_link[0].getparent().remove(other_link[0])

    clean(content)
    document.write(*content.getchildren())

def main():
    if len(sys.argv) < 2 or not sys.argv[-1].startswith('http://keiramarcos.com/fan-fiction/'):
        print('Usage:', sys.argv[0], '[PANDOC_ARGS, ...]', 'URL', file=sys.stderr)
        print('Where URL is a link to a story from http://keiramarcos.com/fan-fiction/', file=sys.stderr)
        sys.exit(1)
    
    pandoc_args = sys.argv[1:-1]
    url = sys.argv[-1]

    with scraper.Document(*pandoc_args) as d:
        process_index(d, url)

if __name__ == '__main__':
    main()

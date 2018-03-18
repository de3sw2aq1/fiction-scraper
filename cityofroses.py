import logging
import sys

from lxml.html import document_fromstring, tostring, clean, builder as E
import requests

from utils.pandoc import Pandoc


logging.basicConfig()
logger = logging.getLogger('cityofroses')
logger.setLevel(logging.INFO)

pandoc = None

def write(*elements):
    for e in elements:
        pandoc.write(tostring(e))

def process_index(url):
    logger.info('Processing story: %s', url)
    doc = document_fromstring(requests.get(url).content)

    pandoc.metadata['title'] = str(doc.xpath('//meta[@property="og:site_name"]/@content')[0])
    pandoc.metadata['author'] = 'Kip Manley'

    contents = doc.get_element_by_id('thecontents')

    for link in contents.xpath('h2/a/@href'):
        process_chapter(link)

def process_chapter(url):
        logger.info('Processing chapter: %s', url)
        doc = document_fromstring(requests.get(url).content)
        doc.make_links_absolute(url)

        title, = doc.xpath('//title/text()')
        title = title.split(' | ')[-1]
        write(E.H1(title))

        content = doc.get_element_by_id('content')

        # Replace empty <h6> tags with <br>
        for h6 in content.xpath('//h6'):
            hr = E.HR()
            h6.addprevious(hr)
            h6.getparent().remove(h6)

        for tag in content.iterchildren():
            # Start of section
            if tag.tag == 'h3':
                section_title = tag.text_content()
                write(E.H2(section_title))

            # Section content
            elif tag.get('class') == 'grafset':
                write(*tag.getchildren())
            
            # End note
            elif tag.get('class') == 'endnote':
                # Change <p> into a <blockquote>
                tag.tag = 'blockquote'
                write(tag)

def main():
    global pandoc

    pandoc_args = sys.argv[1:]
    url = 'http://thecityofroses.com/contents'

    logger.info('Starting Pandoc')

    # Set EPUB chapter level to 2 because the story is broken into sections
    with Pandoc('--epub-chapter-level=2', *pandoc_args) as p:
        pandoc = p
        process_index(url)

if __name__ == '__main__':
    main()
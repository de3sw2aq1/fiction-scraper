import sys
from lxml.html import clean, builder as E
from . import Spider

# Cleaner to remove id attribute
clean = clean.Cleaner(
    safe_attrs=clean.Cleaner.safe_attrs - {'id'}
)
    
class qntm(Spider):
    domain = 'qntm.org'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._heading_ids = set()

    def parse(self, url=None, level=1):
        if not url:
            url = self.url
        self.info(f'Parsing page: {url}' )

        doc = self.fetch(url)
        doc.rewrite_links(self._rewrite_links)

        if level == 1:
            title = doc.xpath('//h2')[0].text_content().strip()
            self.metadata['title'] = title
            self.metadata['author'] = 'Sam Hughes'
        
        content = doc.get_element_by_id('content')

        today_in = content.xpath('h3[starts-with(text(), "Today in ") or text() = "Contents" or text() = "Or just read it here for free!"]')
        if today_in:
            # This is a "subdirecory" listing

            # Output any summary/into if present
            for tag in content:
                # Stop when we reach a heading: <h3>, <h4>, etc.
                # Sometimes this loses an extra intro paragraph, but we usually
                # don't want it.
                if tag.tag[0] == "h":
                    break

                # Skip tag if it says "Read from top to bottom"
                if "Read from top to bottom" in tag.text_content():
                    continue

                yield tag
            
            chapter_level = level
                        
            # import ipdb; ipdb.set_trace()
            # Parse each linked page in the "subdirectory"
            for tag in today_in[0].itersiblings():
                # Skip tag if it says "Read from top to bottom"
                if "Read from top to bottom" in tag.text_content():
                    continue

                elif tag.tag == 'ul':
                    for link in tag.xpath('li/a[1]'):
                        # Fine Structure has a "Chronological cut" which is a
                        # subdirectory that repeats previous chapters in an
                        # alternate order. Skip it.
                        if link.get('href') == 'https://qntm.org/chronological':
                            continue

                        # Add id attributes to headings to allow internal links
                        heading_id = link.get('href').split('/')[-1]
                        self._heading_ids.add(heading_id)

                        yield self._heading(chapter_level, link.text, id=heading_id)
                        yield from self.parse(link.get('href'), chapter_level+1)
                        # This loses any text outside the <a> in the <li>, but
                        # unless we add a table of contents for appendices, there's
                        # nowhere to put it anyway.

                elif tag.tag == 'h4':
                    # Found a subheading like "Appendices"
                    # Output it and change chapter_level
                    yield self._heading(level, tag.text_content().strip())
                    chapter_level = level + 1

                else:
                    # Reached end of the "subdirectory"
                    break

        else:
            # This is a chapter

            # Chapters contain headings too, do we need to decrement them?
            # In practice, chapters don't nest more than one level, so leaving
            # the <h3> and <h4> tags inside chapters is okay. And thankfully
            # there don't seem to be any <h1> or <h2> tags within the content.

            # Remove prevously/next links
            remove = content.xpath('h4[a/text()="Previously"]')
            remove.extend(content.xpath('h4[starts-with(text(), "Next:")]'))
            for tag in remove:
                tag.getparent().remove(tag)

            for tag in content.iter():
                # Ra has meaningul text alignment, convert text-align styles to classes
                style = tag.get('style')
                if style and 'text-align: center' in style:
                    div = E.DIV(E.CLASS('center-aligned'))
                    tag.addprevious(div)
                    div.insert(0, tag)
                elif style and 'text-align: right' in tag.get('style'):
                    div = E.DIV(E.CLASS('right-aligned'))
                    tag.addprevious(div)
                    div.insert(0, tag)

                # Empty <h3> tags render as a rule on qntm.org, convert them to <hr> tags
                if tag.tag == 'h3' and len(tag) == 0 and tag.text_content().strip() == "":
                    tag.tag = 'hr'
                
                # TODO: conditionally output comments?
                # Ra has lots of HTML comments with fun details
                # Transform them into real tags maybe?

            # TODO: add stylesheet that includes alignment classes
            # TODO: add stylesheet with default left alignment for Ra
    
            clean(content)
            yield from content
    
    # Convert internal links into a fragment linking to the anchor
    def _rewrite_links(self, link):
        if link.startswith('https://qntm.org/'):
            id_ = link.split('/')[-1]
            if id_ in self._heading_ids:
                return '#' + id_

        return link

    def _heading(self, level, text, **kwargs):
        return E.E('h'+str(level), text, **kwargs)

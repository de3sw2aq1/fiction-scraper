from lxml.html import builder as E
from .. import Spider, filters


# TODO: conditionally output comments?
# Ra has lots of HTML comments with fun details
# Transform them into real tags maybe?

# TODO: add stylesheet with default left alignment for Ra

# TODO: add .scene-break css class to draw * symbol


def scene_breaks(root):
    # Empty <h3> tags appear as a rule on qntm.org
    for e in root.xpath('.//h3'):
        if len(e) == 0 and e.text_content().strip() == "":
            e.addprevious(E.HR())
            e.drop_tree()

    # Other stories use a centered orange * as a scene break
    for e in root.xpath('.//h4'):
        if e.text_content().strip() == "*":
            e.addprevious(E.HR(E.CLASS('scene-break')))
            e.drop_tree()


def rewrite_links(root):
    """Make links internal to the document.

    During parsing ids are added to headings.
    """

    heading_ids = root.xpath('*//@id')

    def rewrite(link):
        if link.startswith('https://qntm.org/'):
            id_ = link.split('/')[-1]
            if id_ in heading_ids:
                return '#' + id_
        return link

    root.rewrite_links(rewrite)


def heading(level, text, **kwargs):
    return E.E('h'+str(level), text, **kwargs)


class Qntm(Spider):
    name = 'Sam Huges fiction'
    domain = 'qntm.org'
    url = 'https://qntm.org/ra'
    filters = (
        scene_breaks,
        filters.text_alignment,
        rewrite_links,
        *filters.DEFAULT_FILTERS)

    def parse(self, url, level=1):
        doc = self.fetch(url)

        if level == 1:
            title = doc.xpath('//h2')[0].text_content().strip()
            self.metadata['title'] = title
            self.metadata['author'] = 'Sam Hughes'

        content = doc.get_element_by_id('content')
        today_in = content.xpath(
            """h3[starts-with(text(), "Today in ") or
            text() = "Contents" or
            text() = "Or just read it here for free!"]""")
        if today_in:
            # This is a "subdirectory" listing

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

                        yield heading(chapter_level, link.text, id=heading_id)
                        yield from self.parse(link.get('href'), chapter_level+1)
                        # This loses any text outside the <a> in the <li>, but
                        # unless we add a table of contents for appendices, there's
                        # nowhere to put it anyway.

                elif tag.tag == 'h4':
                    # Found a subheading like "Appendices"
                    # Output it and change chapter_level
                    yield heading(level, tag.text_content().strip())
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

            # Remove previously/next links
            remove = content.xpath('h4[a/text()="Previously"]')
            remove.extend(content.xpath('h4[starts-with(text(), "Next:")]'))
            for tag in remove:
                tag.getparent().remove(tag)

            yield from content

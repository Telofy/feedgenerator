# -*- encoding: utf-8 -*-
"""
Syndication feed generation library -- used for generating RSS, etc.

Sample usage:

>>> import feedgenerator
>>> feed = feedgenerator.Rss201rev2Feed(
...     title=u"Poynter E-Media Tidbits",
...     link=u"http://www.poynter.org/column.asp?id=31",
...     feed_url=u"http://test.org/rss",
...     description=u"A group weblog by the sharpest minds in online media/journalism/publishing.",
...     language=u"en",
... )
>>> feed.add_entry(
...     title="Hello",
...     link=u"http://www.holovaty.com/test/",
...     description="Testing."
... )
>>> fp = open('test.rss', 'w')
>>> feed.write(fp, 'utf-8')
>>> fp.close()

For definitions of the different versions of RSS, see:
http://diveintomark.org/archives/2004/02/04/incompatible-rss

CHANGES:
   - from webhelpers: add published property for entries to atom feed
"""

import datetime
import json
import urlparse
import uuid
from feedgenerator.utils.xmlutils import SimplerXMLGenerator
from feedgenerator.utils.encoding import force_unicode, iri_to_uri
from feedgenerator.utils import datetime_safe
from feedgenerator.utils.timezone import is_aware

def rfc2822_date(date):
    # We can't use strftime() because it produces locale-dependant results, so
    # we have to map english month and day names manually
    months = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',)
    days = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
    # Support datetime objects older than 1900
    date = datetime_safe.new_datetime(date)
    # We do this ourselves to be timezone aware, email.Utils is not tz aware.
    dow = days[date.weekday()]
    month = months[date.month - 1]
    time_str = date.strftime('%s, %%d %s %%Y %%H:%%M:%%S ' % (dow, month))
    if is_aware(date):
        offset = date.tzinfo.utcoffset(date)
        timezone = (offset.days * 24 * 60) + (offset.seconds // 60)
        hour, minute = divmod(timezone, 60)
        return time_str + "%+03d%02d" % (hour, minute)
    else:
        return time_str + '-0000'

def rfc3339_date(date):
    # Support datetime objects older than 1900
    date = datetime_safe.new_datetime(date)
    if is_aware(date):
        time_str = date.strftime('%Y-%m-%dT%H:%M:%S')
        offset = date.tzinfo.utcoffset(date)
        timezone = (offset.days * 24 * 60) + (offset.seconds // 60)
        hour, minute = divmod(timezone, 60)
        return time_str + "%+03d:%02d" % (hour, minute)
    else:
        return date.strftime('%Y-%m-%dT%H:%M:%SZ')

def new_random_urn():
    return unicode(uuid.uuid4().urn)

def get_tag_uri(url, date):
    """
    Creates a TagURI.

    See http://diveintomark.org/archives/2004/05/28/howto-atom-id
    """
    bits = urlparse.urlparse(url)
    d = ''
    if date is not None:
        d = ',%s' % datetime_safe.new_datetime(date).strftime('%Y-%m-%d')
    return u'tag:%s%s:%s/%s' % (bits.hostname, d, bits.path, bits.fragment)

def minimized(dictionary):
    """Removes None entries from (the first level of) a dictionary."""
    return dict((key, value)
                for key, value in dictionary.iteritems()
                if value is not None)

def partition(dictionary, keys1, keys2):
    partition1 = dict((key, value)
                      for key, value in dictionary.iteritems()
                      if key in keys1)
    partition2 = dict((key, value)
                      for key, value in dictionary.iteritems()
                      if key in keys2)
    return partition1, partition2


class ConflictingDefinitionsException(ValueError):
    pass


class SyndicationFeed(list):
    """Base class for all syndication feeds. Subclasses should provide write()"""

    def __str__(self):
        return self.write_string()

    def __unicode__(self):
        return str(self).decode('utf-8')

    def root_attributes(self):
        """
        Return extra attributes to place on the root (i.e. feed/channel) element.
        Called from write().
        """
        return {}

    def add_entries(self, *entries):
        """Bulk-adds entries"""
        self.extend(map(self.prepare_entry, entries))

    def add_root_elements(self, handler):
        """
        Add elements in the root (i.e. feed/channel) element. Called
        from write().
        """
        pass

    def entry_attributes(self, entry):
        """
        Return extra attributes to place on each entry (i.e. entry/entry) element.
        """
        return {}

    def add_entry_elements(self, handler, entry):
        """
        Add elements on each entry (i.e. entry/entry) element.
        """
        pass

    def write(self, outfile, encoding=u'utf-8'):
        """
        Outputs the feed in the given encoding to outfile, which is a file-like
        object. Subclasses should override this.
        """
        raise NotImplementedError

    def write_string(self, encoding=u'utf-8'):
        """
        Returns the feed in the given encoding as a string.
        """
        from StringIO import StringIO
        s = StringIO()
        self.write(s, encoding)
        return s.getvalue()

    def latest_post_date(self):
        """
        Returns the latest entry's pubdate. If none of them have a pubdate,
        this returns the current date/time.
        """
        updates = [entry['pubdate']
                   for entry in self
                   if entry.has_key('pubdate')]
        if len(updates) > 0:
            updates.sort()
            return updates[-1]
        else:
            return datetime.datetime.now()


class Enclosure(object):
    "Represents an RSS enclosure"
    def __init__(self, url, length, mime_type):
        "All args are expected to be Python Unicode objects"
        self.length, self.mime_type = length, mime_type
        self.url = iri_to_uri(url)


class RssFeed(SyndicationFeed):

    mime_type = 'application/rss+xml; charset=utf-8'

    def __init__(self, title, link, description, language=None, author_email=None,
            author_name=None, author_link=None, subtitle=None, categories=None,
            feed_url=None, feed_copyright=None, feed_guid=None, ttl=None, **kwargs):
        to_unicode = lambda s: force_unicode(s, strings_only=True)
        if categories:
            categories = [force_unicode(c) for c in categories]
        if ttl is not None:
            # Force ints to unicode
            ttl = force_unicode(ttl)
        self.meta = minimized({
            'title': to_unicode(title),
            'link': iri_to_uri(link),
            'description': to_unicode(description),
            'language': to_unicode(language),
            'author_email': to_unicode(author_email),
            'author_name': to_unicode(author_name),
            'author_link': iri_to_uri(author_link),
            'subtitle': to_unicode(subtitle),
            'categories': categories or (),
            'feed_url': iri_to_uri(feed_url),
            'feed_copyright': to_unicode(feed_copyright),
            'id': feed_guid or link,
            'ttl': ttl,
        })
        self.meta.update(kwargs)

    def add_entry(self, title, link, description, author_email=None,
        author_name=None, author_link=None, pubdate=None, comments=None,
        unique_id=None, enclosure=None, categories=(), entry_copyright=None,
        ttl=None, **kwargs):
        """
        Adds an entry to the feed. All args are expected to be Python Unicode
        objects except pubdate, which is a datetime.datetime object, and
        enclosure, which is an instance of the Enclosure class.
        """
        to_unicode = lambda s: force_unicode(s, strings_only=True)
        if categories:
            categories = [to_unicode(c) for c in categories]
        if ttl is not None:
            # Force ints to unicode
            ttl = force_unicode(ttl)
        entry = minimized({
            'title': to_unicode(title),
            'link': iri_to_uri(link),
            'description': to_unicode(description),
            'author_email': to_unicode(author_email),
            'author_name': to_unicode(author_name),
            'author_link': iri_to_uri(author_link),
            'pubdate': pubdate,
            'comments': to_unicode(comments),
            'unique_id': to_unicode(unique_id),
            'enclosure': enclosure,
            'categories': categories or (),
            'entry_copyright': to_unicode(entry_copyright),
            'ttl': ttl,
        })
        entry.update(kwargs)
        self.append(entry)

    def write(self, outfile, encoding='utf-8'):
        handler = SimplerXMLGenerator(outfile, encoding)
        handler.startDocument()
        handler.startElement(u"rss", self.rss_attributes())
        handler.startElement(u"channel", self.root_attributes())
        self.add_root_elements(handler)
        self.write_entries(handler)
        self.endChannelElement(handler)
        handler.endElement(u"rss")

    def rss_attributes(self):
        return {u"version": self._version,
                u"xmlns:atom": u"http://www.w3.org/2005/Atom"}

    def write_entries(self, handler):
        for entry in self:
            handler.startElement(u'entry', self.entry_attributes(entry))
            self.add_entry_elements(handler, entry)
            handler.endElement(u"entry")

    def add_root_elements(self, handler):
        handler.addQuickElement(u"title", self.meta['title'])
        handler.addQuickElement(u"link", self.meta['link'])
        handler.addQuickElement(u"description", self.meta['description'])
        if self.meta.has_key('feed_url'):
            handler.addQuickElement(u"atom:link", None,
                    {u"rel": u"self", u"href": self.meta['feed_url']})
        if self.meta.has_key('language'):
            handler.addQuickElement(u"language", self.meta['language'])
        for cat in self.meta['categories']:
            handler.addQuickElement(u"category", cat)
        if self.meta.has_key('feed_copyright'):
            handler.addQuickElement(u"copyright", self.meta['feed_copyright'])
        handler.addQuickElement(u"lastBuildDate", rfc2822_date(self.latest_post_date()).decode('utf-8'))
        if self.meta.has_key('ttl'):
            handler.addQuickElement(u"ttl", self.meta['ttl'])

    def endChannelElement(self, handler):
        handler.endElement(u"channel")


class RssUserland091Feed(RssFeed):
    _version = u"0.91"
    def add_entry_elements(self, handler, entry):
        handler.addQuickElement(u"title", entry['title'])
        handler.addQuickElement(u"link", entry['link'])
        if entry['description'] is not None:
            handler.addQuickElement(u"description", entry['description'])


class Rss201rev2Feed(RssFeed):
    # Spec: http://blogs.law.harvard.edu/tech/rss
    _version = u"2.0"
    def add_entry_elements(self, handler, entry):
        handler.addQuickElement(u"title", entry['title'])
        handler.addQuickElement(u"link", entry['link'])
        if entry['description'] is not None:
            handler.addQuickElement(u"description", entry['description'])

        # Author information.
        if entry.has_key("author_name") and entry.has_key("author_email"):
            handler.addQuickElement(u"author", "%s (%s)" % \
                (entry['author_email'], entry['author_name']))
        elif entry.has_key("author_email"):
            handler.addQuickElement(u"author", entry["author_email"])
        elif entry.has_key("author_name"):
            handler.addQuickElement(
                u"dc:creator",
                entry["author_name"],
                {u"xmlns:dc": u"http://purl.org/dc/elements/1.1/"})
        if entry.has_key('pubdate'):
            handler.addQuickElement(u"pubDate", rfc2822_date(entry['pubdate']).decode('utf-8'))
        if entry.has_key('comments'):
            handler.addQuickElement(u"comments", entry['comments'])
        if entry.has_key('unique_id'):
            handler.addQuickElement(u"guid", entry['unique_id'])
        if entry.has_key('ttl'):
            handler.addQuickElement(u"ttl", entry['ttl'])

        # Enclosure.
        if entry.has_key('enclosure'):
            handler.addQuickElement(u"enclosure", '',
                {u"url": entry['enclosure'].url, u"length": entry['enclosure'].length,
                    u"type": entry['enclosure'].mime_type})

        # Categories.
        for cat in entry['categories']:
            handler.addQuickElement(u"category", cat)


class Atom1Feed(SyndicationFeed):
    # Spec: http://atompub.org/2005/07/11/draft-ietf-atompub-format-10.html
    mime_type = 'application/atom+xml; charset=utf-8'
    ns = u"http://www.w3.org/2005/Atom"

    def __init__(self, entries=[], **kwargs):
        """Initializes an Atom feed.

        id -- a permanent, universally unique identifier
        title -- a human-readable title
        updated -- datetime of most recent modification
        authors -- list of dicts for authors (optional)
        author -- convenience shortcut for name of author (optional)
        links -- list of dicts of references to Web resources (optional)
        link -- convenience shortcut to href of link with rel self (optional)
        categories -- list of dicts for categories (optional)
        contributors -- list of dicts for entities who contributed (optional)
        generator -- agent used to generate a feed (optional)
        subtitle -- human-readable description or subtitle (optional)
        icon -- an image that provides iconic visual identification (optional)
        logo -- an image that provides visual identification (optional)
        rights -- rights held in and over an entry or feed (optional)
        """
        kwargs = minimized(kwargs)
        for key in ('summary', 'content'):
            if kwargs.has_key(key) and not kwargs.get(key, {}).get('text'):
                del kwargs[key]
        assert kwargs.has_key('title')
        for link in kwargs.get('links', []):
            assert link.has_key('href')
        for author in kwargs.get('authors', []):
            assert author.has_key('name')
        if not kwargs.has_key('id'):
            kwargs['id'] = new_random_urn()
        if kwargs.has_key('link'):
            # Optimization for frequent use case
            kwargs['links'] = tuple(kwargs.get('links', ()))
            kwargs['links'] += ({'rel': 'self', 'href': kwargs['link']},)
            del kwargs['link']
        if kwargs.has_key('author'):
            kwargs['authors'] = tuple(kwargs.get('authors', ()))
            kwargs['authors'] += ({'name': kwargs['author']},)
            del kwargs['author']
        self.meta = kwargs
        self.extend(map(self.prepare_entry, entries))

    def add_entry(self, **kwargs):
        """Creates/adds an entry to the feed.

        id -- a permanent, universally unique identifier
        title -- a human-readable title
        updated -- datetime of most recent modification
        published -- datetime of an event early in the life of the entry (optional)
        summary --  short summary, abstract, or excerpt (optional)
        content -- contains or links to the content of the entry (optional)
        authors -- list of dicts for authors (optional)
        author -- convenience shortcut for name of author (optional)
        links -- list of dicts of references to Web resources (optional)
        link -- convenience shortcut to href of link with rel alternate (optional)
        categories -- list of dicts for categories (optional)
        contributors -- list of dicts for entities who contributed (optional)
        rights -- rights held in and over an entry or feed (optional)
        source -- dict of source feed meta data (optional)
        """
        entry = self.prepare_entry(kwargs)
        self.append(entry)

    def prepare_entry(self, entry):
        entry = minimized(entry)
        for key in ('summary', 'content'):
            if entry.has_key(key) and not entry.get(key, {}).get('text'):
                del entry[key]
        for link in entry.get('links', []):
            assert link.has_key('href')
        for author in entry.get('authors', []):
            assert author.has_key('name')
        assert entry.has_key('title')
        assert entry.has_key('updated')
        if not self.meta.get('authors'):
            assert entry.get('authors') or entry.get('author'), (
                u'If the feed does not have an author, '
                u'each entry must have one.')
        if not entry.has_key('id'):
            entry['id'] = new_random_urn()
        # Optimizations for frequent use cases
        if entry.has_key('link'):
            entry['links'] = tuple(entry.get('links', ()))
            entry['links'] += ({'rel': 'alternate', 'href': entry['link']},)
            del entry['link']
        if entry.has_key('author'):
            entry['authors'] = tuple(entry.get('authors', ()))
            entry['authors'] += ({'name': entry['author']},)
            del entry['author']
        return entry

    def write(self, outfile, encoding='utf-8'):
        handler = SimplerXMLGenerator(outfile, encoding)
        handler.startDocument()
        handler.startElement(u'feed', self.root_attributes())
        self.add_root_elements(handler)
        self.write_entries(handler)
        handler.endElement(u"feed")

    def root_attributes(self):
        if self.meta.has_key('language'):
            return {u"xmlns": self.ns, u"xml:lang": self.meta['language']}
        else:
            return {u"xmlns": self.ns}

    @staticmethod
    def map_key(key):
        return {'links': 'link',
                'authors': 'author',
                'contributors': 'contributor',
                'categories': 'category'}.get(key, key)

    def add_element(self, handler, key, content, attributes=None):
        handler.addQuickElement(key, content, attributes or {})

    def add_nested_element(self, handler, key, elements=None, attributes=None):
        elements = elements if elements is not None else {}
        attributes = attributes if attributes is not None else {}
        handler.startElement(key, attributes)
        for subkey, content in elements.iteritems():
            handler.addQuickElement(subkey, content)
        handler.endElement(key)

    def add_plain_elements(self, handler, key, values):
        for value in values:
            self.add_nested_element(handler, key, elements=value)

    def add_self_closing_elements(self, handler, key, values):
        for value in values:
            self.add_nested_element(handler, key, attributes=value)

    def add_text_construct_element(self, handler, key, value):
        content, attributes = partition(value, ('text',), ('type',))
        content = content['text']
        self.add_element(handler, key, content, attributes)

    def add_date_element(self, handler, key, content):
        self.add_element(handler, key, content.isoformat() + 'Z')

    def add_root_elements(self, handler):
        cases = {
            'id': self.add_element,
            'title': self.add_element,
            'updated': self.add_date_element,
            'authors': self.add_plain_elements,
            'links': self.add_self_closing_elements,
            'categories': self.add_self_closing_elements,
            'contributors': self.add_plain_elements,
            'generator': self.add_text_construct_element,
            'subtitle': self.add_element,
            'icon': self.add_element,
            'logo': self.add_element,
            'rights': self.add_text_construct_element,
        }
        for key, value in self.meta.iteritems():
            cases[key](handler, self.map_key(key), value)
        if not 'updated' in self.meta:
            handler.addQuickElement(
                u'updated',
                max([entry['updated'] for entry in self] \
                    + [datetime.datetime.utcnow()]).isoformat() + u'Z')

    def write_entries(self, handler):
        for entry in self:
            handler.startElement(u"entry", self.entry_attributes(entry))
            self.add_entry_elements(handler, entry)
            handler.endElement(u"entry")

    def add_entry_elements(self, handler, entry):
        cases = {
            'id': self.add_element,
            'title': self.add_element,
            'updated': self.add_date_element,
            'published': self.add_date_element,
            'summary': self.add_text_construct_element,
            'content': self.add_text_construct_element,
            'authors': self.add_plain_elements,
            'links': self.add_self_closing_elements,
            'categories': self.add_self_closing_elements,
            'contributors': self.add_plain_elements,
            'rights': self.add_text_construct_element,
            'source': self.add_plain_elements,
        }
        for key, value in entry.iteritems():
            cases[key](handler, self.map_key(key), value)


# This isolates the decision of what the system default is, so calling code can
# do "feedgenerator.DefaultFeed" instead of "feedgenerator.Atom1Feed".
DefaultFeed = Atom1Feed

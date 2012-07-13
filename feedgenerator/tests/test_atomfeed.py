# -*- encoding: utf-8 -*-
import unittest
import requests
from datetime import datetime
from feedgenerator.generator import Atom1Feed


class TestAtom1Feed(unittest.TestCase):

    encoding = u'utf8'

    feed_kwargs = {
        'title': u'Feed Generator Updates',
        'subtitle': u'Updates about releases of the feedgenerator package.',
        'link': u'https://github.com/ametaireau/feedgenerator'}

    feed_item_kwargs = {
        'title': u'New Release',
        'link': u'https://github.com/ametaireau/feedgenerator',
        'authors': [{'name': u'Twilight Sparkle'}],
        'summary': {'text': u'Release notes for the feed generator.'},
        'content': {'text': u'Content with <strong>bold</strong> text.',
                    'type': 'html'},
        'updated': datetime.utcnow()}

    def test_feed(self):
        feed = Atom1Feed(**self.feed_kwargs)
        self.assertIn(self.feed_kwargs['title'].encode(self.encoding),
                      feed.write_string(self.encoding),
                      u'Feed output does not contain feed title.')

    def test_feed_item(self):
        feed = Atom1Feed([self.feed_item_kwargs], **self.feed_kwargs)
        self.assertIn(self.feed_item_kwargs['title'].encode(self.encoding),
                      feed.write_string(self.encoding),
                      u'Feed output does not contain feed item title.')

    @unittest.skip('No need to waste their resources')
    def test_feed_item(self):
        feed = Atom1Feed([self.feed_item_kwargs], **self.feed_kwargs)
        feed_string = str(feed)
        response = requests.post(
            'http://validator.w3.org/feed/check.cgi',
            data={'rawdata': feed_string, 'manual': 1})
        for key, value in response.headers.iteritems():
            if key.startswith('x-w3c-validator-'):
                print u'{}: {}'.format(key, value)
        self.assertIn(u'<h2>Congratulations!</h2>',
                      response.text,
                      u'Feed invalid.\n\n%s' % feed_string)

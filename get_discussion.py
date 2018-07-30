#!/usr/bin/env python2

# usage: ./get_discussion.py <wiki_subdomain> <threads=50>
# e.g. ./get_discussion.py mywiki 100

import csv
import errno
import json
import os
import Queue
import requests
import re
import sys
import urllib
from threading import Thread

def get_comment_digests(s, url, share_id):
    m = None
    while not m:
        r = s.get('%s/share/view/%s' % (url, share_id))
        m = re.search(('<script type="text/javascript">\s*<!--\s*ws.namespace\(\'ws.attributes\'\);' +
        '\s*ws.namespace\(\'ws.stream\'\);\s*ws.attributes.sharePage = ([^\\n]+)'), r.content)
    
    return json.loads(m.groups(1)[0][:len(m.groups(1)[0]) - 1])['digests']

def scrape_topic(s, url, q, folder, raw_folder):
    while not q.empty():
        d = q.get()
        sys.stdout.write('Downloading share: %s\n' % d['id'])

        body = ''
        if 'rangeActions' in d:
            for ra in d['rangeActions']: 
                body += ('<b>%s</b> <small>%s</small><br><a href="%s">%s</a><br>%s<br>' % 
                (ra['name'], ra['dateCreated'], ra['diffUrl'], ra['rangeText'], d['description']))
        else:
            body = d['description']

        html = '<html><head><title>%s</title></head><body>' % d['title']
        html += ('<h3>%s</h3><a href="%s"><img src="%s" width="16" height="16"> <b>%s</b></a> <i>%s (%s)</i><br>%s<p>' % 
            (d['title'].encode('ascii', 'xmlcharrefreplace'), d['userCreated']['url'], d['userCreated']['imageUrl'], 
            d['userCreated']['username'], d['smartDate'], d['dateCreated'], body.encode('ascii', 'xmlcharrefreplace')))

        more = d['replyPages'][0]['more']
        for j in range(more, -1, -1):
            # sometimes the TES status page shows up instead, so keep trying until we get JSON
            while True:
                r = s.get('%s/share/replies/%s' % (url, d['id']), params={'page': j})

                try:
                    replies = json.loads(r.content)
                    break
                except:
                    continue

            with open(os.path.join(raw_folder, ('replies-%s.json' % d['id'])), 'w') as f:
                f.write(json.dumps(replies, indent=4, sort_keys=True) + '\n')

            replyDigests = replies['content']['digests']

            for rp in replyDigests:
                html += ('<a href="%s"><img src="%s" width="16" height="16"> <b>%s</b></a> <i>%s (%s)</i><br>%s<p>' % 
                (rp['userCreated']['url'], rp['userCreated']['imageUrl'], rp['userCreated']['username'], 
                rp['smartDate'], rp['dateCreated'], rp['body'].encode('ascii', 'xmlcharrefreplace')))
        with open(os.path.join(folder, ('%s.html' % d['id'])), 'w') as f:
            f.write(html.encode('utf-8') + '\n')
    
        q.task_done()

def main():
    url = 'http://%s.wikispaces.com' % sys.argv[1]
    num_threads = int(sys.argv[2]) if len(sys.argv) >= 3 else 50
    s = requests.Session()
    
    s.get(url)
    r = s.get('%s/space/content' % url, params={
        'utable': 'WikiTablePageList',
        'ut_csv': 1
    })

    content = list(csv.reader(r.content.splitlines(), delimiter=','))

    for c in content:
        if c[0] == 'page':
            print('Scraping page: %s' % c[1])
                
            m = None
            while not m:
                print('Getting total topics')
                r = s.get('%s/page/messages/%s' % (url, c[1]))
                if re.search('<td colspan="6" class="noDataHolder">No messages found.</td>', r.content):
                    break
                m = re.search('\d+ of (\d+)\s*</span></li>\s*<li>\s*<a href', r.content)

            # no messages
            if not m:
                print('No topics on this page. Moving on.')                
                continue

            total_topics = int(m.groups(1)[0])
            print('Expecting %d topic(s) from this page' % total_topics)
            expected_shares = []

            print('Enumerating share identifiers')
            for i in range(0, total_topics, 20):
                print('.'),
                sys.stdout.flush()
                matches = False
                while not matches:
                    r = s.get('%s/page/messages/%s' % (url, c[1]), params={'o': i})
                    matches = re.findall('<a href="/share/view/(\d+)" class=', r.content)
                
                for m in matches:
                    expected_shares.append(m)
            
            assert(len(expected_shares) == total_topics)
    
            folder = os.path.join(sys.argv[1], 'discussion', c[1])
            raw_folder = os.path.join(folder, 'raw')

            try:
                os.makedirs(raw_folder)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            
            print('\nRetrieving topics')
            
            i = 0
            q = Queue.Queue()
            found_shares = []
            while True:
                print('.'),
                sys.stdout.flush()

                r = s.get('%s/page/shares/%s' % (url, urllib.quote_plus(c[1])), params={
                    'page': i
                })

                shares = json.loads(r.content)

                with open(os.path.join(raw_folder, ('shares-page-%d.json' % i)), 'w') as f:
                    f.write(json.dumps(shares, indent=4, sort_keys=True) + '\n')

                digests = shares['content']['sharePage']['digests']

                if len(digests) == 0:
                    break
                
                for d in digests:
                    found_shares.append(d['id'])
                    q.put(d)
                
                i += 1

            sys.stdout.write('\n')
            
            if len(found_shares) != len(expected_shares):
                comment_shares = [x for x in expected_shares if x not in found_shares]
                for c in comment_shares:
                    cd = get_comment_digests(s, url, c)

                    with open(os.path.join(raw_folder, ('comment-digests-%s.json' % c)), 'w') as f:
                        f.write(json.dumps(cd, indent=4, sort_keys=True) + '\n')

                    for d in cd:
                        q.put(d)
            
            # sometimes we get topics from /page/shares/ that aren't on /page/messages/
            # maybe deleted ones?
            assert(q.qsize() >= len(expected_shares))

            for i in range(num_threads):
                t = Thread(target=scrape_topic, args=(s, url, q, folder, raw_folder))
                t.daemon = True
                t.start()
            
            q.join()

            total_saved_html = len([name for name in os.listdir(folder) if name.endswith('.html')])
            print('Saved %d HTML pages' % total_saved_html)
            assert(total_saved_html >= total_topics)

if __name__ == '__main__':
    main()

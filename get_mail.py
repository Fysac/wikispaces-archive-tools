#!/usr/bin/env python2

# usage: ./get_mail.py <username> <password>

import errno
import os
import Queue
import re
import requests
import sys
from threading import Thread

signin_url = 'https://wikispaces.com/site/signin'
auth_url = 'https://session.wikispaces.com/1/auth/login'
mail_list_url = 'https://www.wikispaces.com/mail/list'
mail_view_url = 'https://www.wikispaces.com/mail/view'
settings_url = 'https://www.wikispaces.com/user/edit'

folders = ['Inbox', 'Sent', 'Storage']

num_threads = 30

def download_message(s, username, folder, q):
    while not q.empty():
        msg_id = q.get()
        sys.stdout.write('Downloading message: %s\n' % msg_id)

        valid = False
        while not valid:      
            r = s.get('%s/%s/%s' % (mail_view_url, username, msg_id))
            valid = valid_response(r)

        with open(os.path.join(username, folder, 'view', msg_id + '.html'), 'w') as f:
            f.write(r.content + '\n')
        
        q.task_done()

def valid_response(r):
    return not re.search('<title>TES and THE Status</title>\s*<meta name="description"', r.content)

def login(s, username, password):
    valid = False
    while not valid:
        r = s.get(signin_url)
        valid = valid_response(r)
        
    form_token = re.search('name="wikispacesFormToken" value="(\w+)"', r.content).group(1)
    as_form_token = re.search('name="wikispacesASFormToken" value="(\w+)"', r.content).group(1)
    username_field = re.search(('<label class="sr-only">Username or Email</label>\s*' + 
        '<input type="text" class="form-control" name="(\w+)"'), r.content).group(1)
    password_field = re.search('<input id="passwordPassword" type="password" class="form-control" name="(\w+)"',
        r.content).group(1)
    unknown = re.search('<input type="hidden" name="(\w+)" value="(\d+)"/>', r.content)
    
    valid = False
    while not valid:
        r = s.post(auth_url, data={
            'wikispacesFormToken': form_token,
            'wikispacesASFormToken': as_form_token,
            username_field: username,
            password_field: password,
            unknown.group(1): unknown.group(2),
        })
        valid = valid_response(r)

    if ('/user/my/%s' % username.lower()) not in r.url.lower():
        sys.exit('Login failure.')
    
    # return the real (case-sensitive) username    
    return re.search('/user/my/((\w|-)+)', r.url).group(1)

def download_folder(s, username, folder):
    valid = False
    while not valid:
        r = s.get('%s/%s' % (mail_list_url, username), params={'folder': folder})
        valid = valid_response(r)

    m = re.search('<li class="nohover"><span>\s*\d+ - \d+ of (\d+)\s*</span></li>', r.content)
    if m is None:
        print('No messages in %s' % folder)
        return

    num_messages = int(m.group(1))
    print('%d messages found' % num_messages)

    m = None
    while not m:
        r = s.get('%s/%s' % (settings_url, username))
        m = re.search('<option label="\d+" value="\d+" selected="selected">(\d+)</option>', r.content)

    results_per_page = int(m.group(1))
    print('Getting %d results per page' % results_per_page)
    
    for i in range(0, num_messages, results_per_page):
        print('Downloading page: %d' % ((i / results_per_page) + 1))

        matches = []
        while len(matches) == 0:
            r = s.get('%s/%s' % (mail_list_url, username), params={
                'folder': folder,
                'o': i
            })
            
            with open(os.path.join(username, folder, 'list', str((i / results_per_page) + 1) + '.html'), 'w') as f:
                f.write(r.content + '\n')
            
            matches = re.findall(('<img src="([^"]+)" width="16" height="16" alt="([^"]+)" class="userPicture" /> ' +
                '([^\s]+)\s*</td>\s*<td><a href="([^"]+)"'), r.content)
            
            q = Queue.Queue()

            for m in matches:
                msg_id = m[3].split('/')[4]
                q.put(msg_id)
            
            for i in range(num_threads):
                t = Thread(target=download_message, args=(s, username, folder, q))
                t.daemon = True
                t.start()

            q.join()

def main():
    username = sys.argv[1]
    password = sys.argv[2]

    s = requests.Session()
    username = login(s, username, password)
    
    for f in folders:
        try:
            os.makedirs(os.path.join(username, f, 'list'))
            os.makedirs(os.path.join(username, f, 'view'))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
            pass

    for f in folders:
        print('Working on: %s' % f)
        download_folder(s, username, f)

if __name__ == '__main__':
    main()

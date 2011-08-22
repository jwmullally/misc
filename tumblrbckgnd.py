#!/usr/bin/python

# tumblrbckgnd.py
# jm
#
# Take photos from a tumblr site and rotate them as the desktop background.
#
# This script evolved from an earlier beautifulsoup tumblr page parser, before 
# I found out about the json api. It could be replaced with some oneliner
# curl, awk, for, wget, feh' monster with enough effort.
#
# Examples:
#
#   ./tumblrbckgnd.py --random http://thisisnthappiness.com/
#
#   ./tumblrbckgnd.py http://fuckyeahearth.com/

#
# TODO add some title/text annotation/colors to the background with
# info from the tumblr feed.
#


import urllib2
import json
import random
import subprocess
import os
import optparse
import sys
import tempfile
import time

def tumblrphoto(tumblrurl, randomize=False, per_fetch=20, photo_size='1280'):
    """Generator: yield the URLs of images from photo posts of tumblrlog, given
    by the url 'tumblrurl'"""
    jsonurl = 'http://'+tumblrurl.split('http://')[-1].rstrip('/')+'/api/read/json?type=photo'
    try:
        html = urllib2.urlopen(jsonurl + '&num=1').read()
    except urllib2.URLError:
        raise urllib2.URLError('Unable to fetch: '+jsonurl+'&num=1')
    tumblr = json.loads(html[len('var tumblr_api_read = '):-len(';\n')])
    posts_total = tumblr['posts-total']
    ranges = range(0, posts_total, per_fetch)
    if randomize:
        random.shuffle(ranges) 
    for start in ranges:
        purl = jsonurl+'&start='+str(start)+'&num='+str(per_fetch)
        phtml = urllib2.urlopen(purl).read()
        ptumblr = json.loads(phtml[len('var tumblr_api_read = '):-len(';\n')])
        posts = ptumblr['posts']
        if randomize:
            random.shuffle(posts)
        for post in posts:
            if 'photo-url-'+photo_size not in post:
                print "Warning: no 'photo-url-"+photo_size+"' in photo post, continuing..."
                continue
            yield post['photo-url-'+photo_size]
    return


def imgurl_streamer_feh(urllist, delay=30):
    """Use 'feh' to display a slideshow of the images
    specified by urllist."""

    imgtmp,img = tempfile.mktemp(),tempfile.mktemp()
    fehproc = None

    try:
        for imgurl in urllist:
            subprocess.call(['wget', '-nv', '-O', imgtmp, imgurl])
            subprocess.call(['mv', '-f', imgtmp, img])
            if fehproc == None or fehproc.poll() != None:
                # Replace background --bg-center with -FZ for fullscreen
                fehproc = subprocess.Popen(['feh', '-R', '1', '--bg-center', img])
            time.sleep(delay)
    finally:
        if fehproc:
            fehproc.terminate()
        subprocess.call(['rm', '-f', imgtmp, img])

    return


def randrobin(iterators, randomize=False):
    """Cycle through multiple iterators, yielding a value from each one,
    until all are empty. Set randomize=True to randomly cycle between them."""
    iters = map(iter, iterators)
    x = -1
    while len(iters) > 0:
        if randomize:
            x = random.randint(0, len(iters)-1)
        else:
            x = (x+1)%len(iters)
        try:
            yield iters[x].next()
        except StopIteration:
            del iters[x]
            x -= 1
    return


def main():
    usage = '%prog [options] [TUMBLR_URL]...'
    descr = ('Grab photos from multiple tumblr feeds and cycle them as the X '
             'background.')
    parser = optparse.OptionParser(usage=usage, description=descr)
    parser.add_option('-d', '--delay', type='int', dest='delay', default=3600,
                      help='Delay (sec) between changing images. Default: 3600.')
    parser.add_option('-r', '--random', action='store_true', dest='randomize', 
                      default=False,
                      help='Show images in random order.')
    parser.add_option('-p', '--photo-size', dest='photo_size', default='1280',
                      help='Tumblr image size to fetch. Default: 1280.'
                           ' Other sizes: 75, 100, 250, 400, 500, 1280.')
    (opts, args) = parser.parse_args(sys.argv)
    urls = args[1:]

    photos = randrobin([tumblrphoto(url, opts.randomize, photo_size=opts.photo_size) for url in urls], opts.randomize)
    imgurl_streamer_feh(photos, opts.delay)
    return


if __name__ == '__main__':
    main()

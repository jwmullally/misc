#!/usr/bin/python
# alexa_demographics.py
# jwm 2011

# A script for fetching website demographic data from alexa.com.
#
# This module is really more useful for statistics gathering inside another 
# python script than as a command line tool.

from BeautifulSoup import BeautifulSoup
import lxml.etree
import urllib2
from StringIO import StringIO
import re


def _getsoup(url):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    try:
        html = opener.open(url).read()
    except urllib2.URLError:
        raise urllib2.URLError('Unable to fetch: '+url+'&num=1')
    try:
        parser = lxml.etree.HTMLParser()
        tree = lxml.etree.parse(StringIO(html), parser)
        fixedhtml = lxml.etree.tostring(tree.getroot(), method="html")
        soup = BeautifulSoup(fixedhtml)
    except:
        soup = BeautifulSoup(html)
    return soup


def _demog_box2dict(soup):
    headerstr = str(soup.findAll(attrs={'class': 'demog_header'})[0])
    header = re.search('<strong>(.+)</strong>', headerstr).group(1)
    demog_results = {}
    for demog in soup.findAll(attrs={'class': 'demog_percentages'}):
        result = {}
        label = str(demog.findAll(attrs={'class': 'demog_label'})[0].string)
        leftstr = demog.findAll(attrs={'class': 'demog_left'})[0].findAll(attrs={'class':'demog_stat'})[0]['style']
        result['bar'] = - float(re.search('width:([0-9\.]+)px', leftstr).group(1))
        rightstr = demog.findAll(attrs={'class': 'demog_right'})[0].findAll(attrs={'class':'demog_stat'})[0]['style']
        result['bar'] += float(re.search('width:([0-9\.]+)px', rightstr).group(1))
        tipstr = str(demog.findAll(attrs={'class': 'tooltip'})[0].findAll(attrs={'class': 'middle'})[0])
        result['tip'] = str(re.findall('(<strong>(.+?)</strong>)+', tipstr)[0][1])
        result['confidence'] = re.search('<strong>Confidence:</strong>\s*(\S+)\s*</span>', tipstr).group(1)
        demog_results[label] = result
    return (header, demog_results)

    
def get_demographics(site_url):
    """Return the demographics for website 'site_url' as a dict."""
    url = 'http://www.alexa.com/siteinfo/' + site_url
    print 'get_demographics(): Fetching:', url
    soup = _getsoup(url)
    demog_box_results = {}
    for demog_box in soup.findAll(attrs={'class': 'demog_box'}):
        header, demog_results = _demog_box2dict(demog_box)
        demog_box_results[header] = demog_results
    return demog_box_results


def get_topsites_urls(topsite_format_url, range_low, range_hi):
    """Return the list of website URLs for http://www.alexa.com/topsites/* site lists."""
    sites = []
    for k in range(range_low, range_hi):
        url = topsite_format_url % (';'+str(k) if k != 0 else '')
        print 'get_topurls(): Fetching:', url
        soup = _getsoup(url)
        for sitesoup in soup.findAll(attrs={'class': 'site-listing'}):
            rank = int(sitesoup.findAll(attrs={'class':'count'})[0].string)
            site = sitesoup.findAll('a')[0]['href'].split('/siteinfo/')[1]
            sites.append((rank, site))
    return sites


#######################################################################


def test():
    print 'Demographics for: smbc-comics.com:'
    print get_demographics( 'smbc-comics.com')
    print 'Demographics for: xkcd.org:'
    print get_demographics( 'xkcd.org')

    topurls = get_topsites_urls('http://www.alexa.com/topsites/category%s/Top/Computers', 0, 20)
    demogs = [[site, get_demographics(site)] for rank,site in topurls]
    print '\nTop->Computers  Gender->Male:'
    print sorted((demog[1]['Gender']['Male']['bar'], demog[0]) for demog in demogs)
    print '\nTop->Computers  Gender->Female:'
    print sorted((demog[1]['Gender']['Female']['bar'], demog[0]) for demog in demogs)
    # Where are the hot hacker girls they promised us man...
    return


def main():
    import sys, optparse

    usage = '%prog [options] [url] [demographic] [demographic section]'
    descr = ('Grab website visitor demographics from alexa.com.')
    parser = optparse.OptionParser(usage=usage, description=descr)
    parser.add_option('-l', '--list', action='store_true', dest='list', 
                      default=False, 
                      help='List the demographics available for a website. Default: False')
    parser.add_option('-t', '--test', action='store_true', dest='test', 
                      default=False,
                      help='Test the script. Default: False')
    (opts, args) = parser.parse_args(sys.argv)
    if opts.test:
        test()
        return

    prog, url, demog, demogsec = args + [None]*(4-len(args)) # pad out args
    if url == None:
        print parser.format_help()
        return

    urldemogs = get_demographics(url)
    print ''
    if opts.list:
        for demogkey in urldemogs.keys():
            demogsec_keys = ', '.join(sorted(urldemogs[demogkey].keys()))
            print demogkey + ': ' + demogsec_keys
        print ''

    if demog and demogsec:
        print urldemogs[demog][demogsec]
    elif demog:
        print urldemogs[demog]
    else:
        print urldemogs

    return
    

if __name__ == '__main__':
    main()


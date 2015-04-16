#!/usr/bin/env python2.7

# Full VT APIv2 functions added by Andriy Brukhovetskyy
# doomedraven -  Twitter : @d00m3dr4v3n
# No Licence or warranty expressed or implied, use however you wish!
# For more information look at:
#
# https://www.virustotal.com/en/documentation/public-api
# https://www.virustotal.com/en/documentation/private-api

__author__ = 'Andriy Brukhovetskyy - DoomedRaven'
__version__ = '2.0.8'
__license__ = 'GPLv3'

import os
import sys
import csv
import time
import json
import glob

import hashlib
import argparse
import requests
import ConfigParser
from re import match
import texttable as tt
from urlparse import urlparse
from operator import methodcaller
from datetime import datetime
from dateutil.relativedelta import relativedelta

 #InsecureRequestWarning: Unverified HTTPS request is being made.
try:
     from requests.packages.urllib3.exceptions import InsecureRequestWarning
     requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except AttributeError:
     pass

def private_api_access_error():
    print '\n[!] You don\'t have permission for this operation, Looks like you trying to access to PRIVATE API functions\n'
    sys.exit()


def get_adequate_table_sizes(scans, short=False, short_list=False):

    av_size_f = 14
    result_f = 6
    version_f = 9

    if scans:

        # Result len
        if short:
            av_size = max(map(lambda engine: len(
                engine) if engine is not None and engine in short_list else 0, scans))
            result = max(map(lambda engine: len(scans[engine]['result']) if scans[engine].has_key(
                'result') and scans[engine]['result'] is not None and engine in short_list else 0, scans))
            version = max(map(lambda engine: len(scans[engine]['version']) if scans[engine].has_key(
                'version') and scans[engine]['version'] is not None and engine in short_list else 0, scans))

        else:
            av_size = max(
                map(lambda engine: len(engine) if engine is not None else 0, scans))
            result = max(map(lambda engine: len(scans[engine]['result']) if scans[
                         engine].has_key('result') and scans[engine]['result'] is not None else 0, scans))
            version = max(map(lambda engine: len(scans[engine]['version']) if scans[
                          engine].has_key('version') and scans[engine]['version'] is not None else 0, scans))

        if result > result_f:
            result_f = result

        if av_size > av_size_f:
            av_size_f = av_size

        if version > version_f:
            version_f = version

    return av_size_f, result_f, version_f


def pretty_print(block, headers, sizes=False, align=False):

    tab = tt.Texttable()

    if isinstance(block, list):
        plist = []

        for line in block:

            if len(headers) == 1:
                plist.append([line])

            else:
                plist.append(
                    map(lambda key: line[key] if line.get(key) else ' -- ', headers)
                    )

        if len(plist) > 1 and isinstance(plist[0], list):
            tab.add_rows(plist)

        else:
            tab.add_row(plist[0])

    else:
        row = map(
            lambda key: block[key] if block.get(key) else ' -- ', headers)
        tab.add_row(row)

    tab.header(headers)

    if not align:
        align = map(lambda key: 'l', headers)

    if sizes:
        tab.set_cols_width(sizes)

    tab.set_cols_align(align)

    print tab.draw()


def pretty_print_special(rows, headers, sizes=False, align=False):
    tab = tt.Texttable()
    tab.add_rows(rows)

    if sizes:
        tab.set_cols_width(sizes)

    if align:
        tab.set_cols_align(align)

    tab.header(headers)

    print '\n', tab.draw()


def is_file(value):
    try:
        if isinstance(value, list):

            if os.path.isfile(value[0]):
                return True, value[0]

            else:
                return False, value[0]

        elif isinstance(value, basestring):

            if os.path.isfile(value):
                return True, value

            else:
                return False, value

    except IndexError:
        print '\n[!] You need to provide some arguments\n'
        sys.exit()


def jsondump(jdata, sha1):

    jsondumpfile = open('VTDL_{name}.json'.format(name=sha1), 'w')
    json.dump(jdata, jsondumpfile)
    jsondumpfile.close()

    print '\n\tJSON Written to File -- VTDL_{sha1}.json\n'.format(sha1=sha1)


def load_file(file_path):

    if file_path.endswith('.json'):

        try:
            log = open(file_path, 'r').read()
            jdata = json.loads(log)
            return jdata

        except TypeError:
            print '\n[!] Check your json dump file\n'

def print_results(jdata, undetected_downloaded_samples, detected_communicated,
  undetected_communicated_samples, detected_urls, detected_downloaded_samples, detected_referrer_samples, undetected_referrer_samples):

    if jdata.get('detected_downloaded_samples') and detected_downloaded_samples:

        print '\n[+] Latest detected files that were downloaded from this domain/ip\n'
        pretty_print(sorted(jdata['detected_downloaded_samples'], key=methodcaller('get', 'date'), reverse=True), [
                     'positives', 'total', 'date', 'sha256'], [15, 10, 20, 70], ['c', 'c', 'c', 'c'])

    if jdata.get('undetected_downloaded_samples') and undetected_downloaded_samples:

        print '\n[+] Latest undetected files that were downloaded from this domain/ip\n'
        pretty_print(sorted(jdata['undetected_downloaded_samples'], key=methodcaller('get', 'date'), reverse=True), [
                     'positives', 'total', 'date', 'sha256'], [15, 10, 20, 70], ['c', 'c', 'c', 'c'])

    if jdata.get('detected_communicating_samples') and detected_communicated:

        print '\n[+] Latest detected files that communicate with this domain/ip\n'
        pretty_print(sorted(jdata['detected_communicating_samples'], key=methodcaller('get', 'scan_date'), reverse=True), [
                     'positives', 'total', 'date', 'sha256'], [15, 10, 20, 70], ['c', 'c', 'c', 'c'])

    if jdata.get('undetected_communicating_samples') and undetected_communicated_samples:

        print '\n[+] Latest undetected files that communicate with this domain/ip\n'
        pretty_print(sorted(jdata['undetected_communicating_samples'], key=methodcaller('get', 'date'), reverse=True), [
                     'positives', 'total', 'date', 'sha256'], [15, 10, 20, 70], ['c', 'c', 'c', 'c'])

    if jdata.get('detected_communicating_samples') and detected_referrer_samples:

        print '\n[+] Latest detected referrer files\n'
        pretty_print(sorted(jdata['detected_referrer_samples']), [
                     'positives', 'total',  'sha256'], [15, 10, 70], ['c', 'c', 'c'])


    if jdata.get('undetected_communicating_samples') and undetected_referrer_samples:

        print '\n[+] Latest undetected referrer files\n'
        pretty_print(sorted(jdata['undetected_referrer_samples']), [
                     'positives', 'total',  'sha256'], [15, 10, 70], ['c', 'c', 'c'])


    if jdata.get('detected_urls') and detected_urls:

        url_size = max(
            map(lambda url: len(url['url']), jdata['detected_urls']))

        if url_size > 80:
            url_size = 80

        print '\n[+] Latest detected URLs\n'
        pretty_print(sorted(jdata['detected_urls'], key=methodcaller('get', 'scan_date'), reverse=True), [
                     'positives', 'total', 'scan_date', 'url'], [9, 5, 20, url_size], ['c', 'c', 'c', 'l'])


def get_detections(scans):

    plist = [[]]
    engines = ['Sophos', 'Kaspersky', 'TrendMicro']
    cont = 3
    other_engines = []

    for engine in engines:
        if scans.get(engine) and scans[engine].get('result'):
            plist.append([engine,
                          scans[engine]['result'],
                          scans[engine]['version'] if 'version' in scans[engine] and scans[engine]['version'] else ' -- ',
                          scans[engine]['update'] if 'update' in scans[engine] and scans[engine]['update'] else ' -- '
                          ])
            cont -= 1
            other_engines.append(engine)

    for engine in scans:
        if scans.get(engine) and scans[engine].get('result') and cont > 0:
            plist.append([engine,
                          scans[engine]['result'],
                          scans[engine]['version'] if 'version' in scans[engine] and scans[engine]['version'] else ' -- ',
                          scans[engine]['update'] if 'update' in scans[engine] and scans[engine]['update'] else ' -- '
                          ])
            cont -= 1
            other_engines.append(engine)

        elif cont == 0:
            break

    if cont != 3:
        av_size, result_size, version = get_adequate_table_sizes(
            scans, True, other_engines)
        pretty_print_special(plist,
                             ['Vendor name',  'Result',
                                 'Version', 'Last Update'],
                             [av_size, result_size, version, 11],
                             ['r', 'l', 'l', 'c']
                             )


def dump_csv(filename, scans):

    f = open('VTDL{0}.csv'.format(filename), 'w')
    writer = csv.writer(f, delimiter=',')
    writer.writerow(
        ('Vendor name', 'Detected', 'Result', 'Version', 'Last Update'))

    for x in sorted(scans):
        writer.writerow([x,
                         'True' if scans[x]['detected'] else 'False', scans[
                             x]['result'] if scans[x]['result'] else ' -- ',
                         scans[x]['version'] if scans[x].has_key(
                             'version') and scans[x]['version'] else ' -- ',
                         scans[x]['update'] if scans[x].has_key(
                             'update') and scans[x]['update'] else ' -- '
                         ])

    f.close()

    print '\n\tCSV file dumped as: VTDL{0}.csv'.format(filename)


def parse_report(jdata, hash_report, verbose, dump, csv_write, url_report=False, not_exit=False, ufilename=False):

    filename = ''

    if jdata['response_code'] != 1:

        if not not_exit:
            return False

        else:
            print '\n[-] Status : {info}\n'.format(info=jdata['verbose_msg'])
            sys.exit()

    if ufilename:
        print '\nLooking for:\n\t{0}'.format(ufilename)

    if jdata.get('scan_date'):
        print '\nScanned on : \n\t{0}'.format(jdata['scan_date'])
    if jdata.get('total'):
        print '\nDetections:\n\t {positives}/{total} Positives/Total'.format(positives=jdata['positives'], total=jdata['total'])

    if url_report:
        if jdata.get('url'):
            print '\nScanned url :\n\t {url}'.format(url=jdata['url'])

    else:
        if not verbose:
            get_detections(jdata['scans'])

        if 'md5' in jdata: print '\n\tResults for MD5    : {0}'.format(jdata['md5'])
        if 'sha1' in jdata: print '\tResults for SHA1   : {0}'.format(jdata['sha1'])
        if 'sha256' in jdata: print '\tResults for SHA256 : {0}'.format(jdata['sha256'])

    if verbose == True and jdata.get('scans'):
        print '\nVerbose VirusTotal Information Output:'
        plist = [[]]

        for x in sorted(jdata['scans']):

            plist.append([x,
                          'True' if jdata['scans'][x]['detected'] else 'False',
                          jdata['scans'][x]['result'] if jdata[
                              'scans'][x]['result'] else ' -- ',
                          jdata['scans'][x]['version'] if  'version' in jdata['scans'][x] and jdata['scans'][x]['version'] else ' -- ',
                          jdata['scans'][x]['update'] if 'update' in jdata['scans'][x] and jdata['scans'][x]['update'] else ' -- '
                          ])

        av_size, result_size, version = get_adequate_table_sizes(
            jdata['scans'])

        if version == 9:
            version_align = 'c'

        else:
            version_align = 'l'

        pretty_print_special(plist,
                             ['Vendor name', 'Detected', 'Result',
                                 'Version', 'Last Update'],
                             [av_size, 9, result_size, version, 12],
                             ['r', 'c', 'l', version_align, 'c']
                             )
        del plist

    if dump is True:
        jsondump(jdata, jdata['sha1'])

    if csv_write is True:
        filename = jdata['scan_id']
        dump_csv(filename, jdata['scans'])

    if jdata.get('permalink'):
        print "\n\tPermanent Link : {0}\n".format(jdata['permalink'])

    return True

# Static variable decorator for function


def static_var(varname, value):
    def decorate(func):

        setattr(func, varname, value)

        return func

    return decorate

# Track how many times we issue a request


@static_var("counter", 0)
# Track when the first request was sent
@static_var("start_time", 0)
def get_response(url, method="get", **kwargs):

    # Set on first request

    if get_response.start_time == 0:
        get_response.start_time = time.time()

    # Increment every request
    get_response.counter = 1

    jdata = ''
    response = ''

    while True:
        try:
            response = getattr(requests, method)(url, **kwargs)

        except requests.exceptions.ConnectionError:
            print '\n[!] Can\'t resolv hostname, check your internet conection\n'
            sys.exit()

        if response.status_code == 403:
            private_api_access_error()

        if response.status_code != 204 and hasattr(response, 'json'):

            try:
                jdata = response.json()

            except:
                jdata = response.json

            break

        # Determine minimum time we need to wait for limit to reset
        wait_time = 59 - int(time.time() - get_response.start_time)

        if wait_time < 0:
            wait_time = 60

        print "Reached per minute limit of {0:d}; waiting {1:d} seconds\n".format(get_response.counter, wait_time)

        time.sleep(wait_time)

        # Reset static vars
        get_response.counter = 0
        get_response.start_time = 0

    return jdata, response


class vtAPI():

    def __init__(self, apikey):

        self.params = {'apikey': apikey}
        self.base = 'https://www.virustotal.com/vtapi/v2/'

    def getReport(self, hash_report, allinfo=False, verbose=False, dump=False, csv_write=False, not_exit=False, filename=False, privateAPI=False):
        """
        A md5/sha1/sha256 hash will retrieve the most recent report on a given sample. You may also specify a scan_id (sha256-timestamp as returned by the file upload API)
        to access a specific report. You can also specify a CSV list made up of a combination of hashes and scan_ids (up to 4 items or 25 if you have private api with the
        standard request rate), this allows you to perform a batch request with one single call.
        """

        jdatas = list()
        result, name = is_file(hash_report)

        if result:
            jdata = load_file(name)
            if isinstance(jdata, list):
                jdatas = jdata
            else:
                jdatas = [jdata]

            dump = False

        else:

            if isinstance(hash_report, list) and len(hash_report) == 1:
                hash_reports = hash_report

            elif isinstance(hash_report, basestring):
                hash_reports = [hash_report]

            elif len(hash_report) > 1 and not isinstance(hash_report, basestring):

                if privateAPI:
                    start = -25
                    increment = 25

                else:
                    start = -4
                    increment = 4

                end = 0
                hash_reports = list()

                while True:

                    start += increment

                    if len(hash_report) > end + increment:
                        end += increment
                    elif len(hash_report) <= end + increment:
                        end = len(hash_report)

                    hash_reports.append(
                        ' '.join(map(lambda hreport: hreport, hash_report[start:end]))
                    )

                    if end == len(hash_report):
                        break

            for hashes_report in hash_reports:

                self.params['resource'] = hashes_report

                if allinfo:
                    self.params.setdefault('allinfo', allinfo)

                url = self.base + 'file/report'

                jdata, response = get_response(url, params=self.params)
                jdatas += jdata

        jdatas = filter(None, jdatas)
        if isinstance(jdatas, list) and jdatas == []:
            print 'Nothing found'
            return

        if  not isinstance(jdata, list):
            jdatas = [jdata]

        for jdata in jdatas:

            if jdata['response_code'] == 0 or jdata['response_code'] == -1:

                if not_exit:
                    return False

                else:
                    if jdata.get('verbose_msg'):
                        print '\n[!] Status : {verb_msg}\n'.format(verb_msg=jdata['verbose_msg'])
                    sys.exit()

            if allinfo == '1':

                if dump:
                    jsondump(jdata, name)

                if jdata.get('md5'):
                    print '\nMD5    : {md5}'.format(md5=jdata['md5'])
                if jdata.get('sha1'):
                    print 'SHA1   : {sha1}'.format(sha1=jdata['sha1'])
                if jdata.get('sha256'):
                    print 'SHA256 : {sha256}'.format(sha256=jdata['sha256'])
                if jdata.get('ssdeep'):
                    print 'SSDEEP : {ssdeep}'.format(ssdeep=jdata['ssdeep'])

                if jdata.get('scan_date'):
                    print '\nScan  Date     : {scan_date}'.format(scan_date=jdata['scan_date'])
                if jdata.get('first_seen'):
                    print 'First Submission : {first_seen}'.format(first_seen=jdata['first_seen'])
                if jdata.get('last_seen'):
                    print 'Last  Submission : {last_seen}'.format(last_seen=jdata['last_seen'])

                if jdata.get('submission_names'):
                    print '\nSubmission names:'
                    for name in jdata['submission_names']:
                        print '\t{name}'.format(name=name)

                if jdata.get('type'):
                    print '\nFile Type : {type_f}'.format(type_f=jdata['type'])
                if jdata.get('size'):
                    print 'File Size : {size}'.format(size=jdata['size'])
                if jdata.get('tags'):
                    print 'Tags: {tags}'.format(tags=', '.join(map(lambda tag: tag, jdata['tags'])))

                if jdata.get('additional_info'):
                    #[u'pe-resource-list', u'pe-resource-langs', u'pe-timestamp', u'imports', u'pe-entry-point', u'pe-resource-types', u'sections', u'pe-machine-type']
                    if jdata['additional_info']['magic']:
                        print 'Magic : {magic}'.format(magic=jdata['additional_info']['magic'])

                    if jdata['additional_info'].get('referers'):
                        print '\nReferers:'
                        for referer in jdata['additional_info']['referers']:
                            print '\t{referer}'.format(referer=referer)

                    if jdata['additional_info'].get('sigcheck'):

                        print '\nPE signature block:'
                        plist = [[]]

                        for sig in jdata['additional_info']['sigcheck']:
                            plist.append(
                                [sig, jdata['additional_info']['sigcheck'][sig].encode('utf-8')] # texttable unicode fail
                            )

                        pretty_print_special(plist, ['Name', 'Value'])
                        del plist

                    if jdata['additional_info'].get('exiftool'):

                        print '\nExifTool file metadata:'
                        plist = [[]]

                        for exiftool in jdata['additional_info']['exiftool']:
                            plist.append(
                                [exiftool, jdata['additional_info']['exiftool'][exiftool]])

                        pretty_print_special(plist, ['Name', 'Value'])
                        del plist

                    if jdata['additional_info'].get('sections'):
                        pretty_print_special(jdata['additional_info']['sections'],
                                             ['Name', 'Virtual address', 'Virtual size',
                                                 'Raw size', 'Entropy', 'MD5'],
                                             [10, 10, 10, 10, 10, 35],
                                             ['c', 'c', 'c', 'c', 'c', 'c']
                                             )

                    if jdata['additional_info'].get('imports'):

                        print '\nImports:'

                        for imported in jdata['additional_info']['imports']:

                            print '\t{0}'.format(imported)

                            for valor in jdata['additional_info']['imports'][imported]:
                                print '\t\t{0}'.format(valor)

                    if jdata['additional_info'].get('trid'):
                        print '\nTrID:'
                        print '\t{trid}'.format(trid=jdata['additional_info']['trid'].replace('\n', '\n\t'))

                if jdata.get('total'):
                    print '\nDetections:\n\t{positives}/{total} Positives/Total\n'.format(positives=jdata['positives'], total=jdata['total'])

                if jdata.get('scans'):

                    plist = [[]]
                    for x in jdata['scans']:
                        plist.append([x,  'True' if jdata['scans'][x][
                                     'detected'] else 'False', jdata['scans'][x]['result']])

                    pretty_print_special(plist,
                                         ['Name', 'Detected', 'Result'],
                                         [30, 9, 55],
                                         ['l', 'c', 'l'])

                    del plist

                if jdata.get('permalink'):
                    print '\nPermanent link : {permalink}\n'.format(permalink=jdata['permalink'])
                return True

            else:
                 result = parse_report(
                    jdata, hash_report, verbose, dump, csv_write, False, not_exit, filename)

        return result

    def rescan(self, hash_rescan, date=False, period=False, repeat=False, notify_url=False, notify_changes_only=False, delete=False):

        """
        This API allows you to rescan files in VirusTotal's file store without having to resubmit them, thus saving bandwidth.
        """

        if len(hash_rescan) == 1:
            hash_rescans = hash_rescan

        elif isinstance(hash_rescan, basestring):
            hash_rescans = [hash_rescan]

        elif len(hash_rescan) > 1 and not isinstance(hash_rescan, basestring):

                start = -25
                increment = 25
                end = 0
                hash_rescans = list()

                while True:

                    start += increment

                    if len(hash_rescan) > end + increment:
                        end += increment
                    elif len(hash_rescan) <= end + increment:
                        end = len(hash_rescan)

                    hash_rescans.append(
                        [', '.join(map(lambda hrescan: hrescan, hash_rescan[start:end]))]
                    )

                    if end == len(hash_rescan):
                        break

        url = self.base + 'file/rescan'

        for hash_part in hash_rescan:

            if os.path.exists(hash_part):
                hash_part = [
                    hashlib.md5(open(hash_part, 'rb').read()).hexdigest()]

            self.params.setdefault('resource', hash_part)

            if delete:
                url = url + '/delete'

            else:
                if date:
                    self.params.setdefault('date', date)

                if period:
                    self.params.setdefault('period', period)

                    if repeat:
                        self.params.setdefault('repeat', repeat)

                if notify_url:
                    self.params.setdefault('notify_url', notify_url)

                    if notify_changes_only:
                        self.params.setdefault(
                            'notify_changes_only', notify_changes_only)

            jdatas, response = get_response(url, params=self.params, method='post')

            if isinstance(jdatas, list) and not filter(None, jdatas):
                print 'Nothing found'
                return

            if not isinstance(jdatas, list):
                jdatas = [jdatas]

            for jdata in jdatas:

                if jdata['response_code'] == 0 or jdata['response_code'] == -1:
                    if jdata.get('verbose_msg'):
                        print '\n[!] Status : {verb_msg}\n'.format(verb_msg=jdata['verbose_msg'])

                else:
                    if jdata.get('sha256'):
                        print '[+] Check rescan result with sha256 in few minuts : \n\tSHA256 : {sha256}'.format(sha256=jdata['sha256'])
                    if jdata.get('permalink'):
                        print '\tPermanent link : {permalink}\n'.format(permalink=jdata['permalink'])

    def fileScan(self, files, verbose=False, notify_url=False, notify_changes_only=False, dump=False, csv_write=False, privateAPI=False, scan=False):
        """
        Allows to send a file to be analysed by VirusTotal.
        Before performing your submissions we encourage you to retrieve the latest report on the files,
        if it is recent enough you might want to save time and bandwidth by making use of it. File size limit is 32MB,
        in order to submmit files up to 200MB you must request an special upload URL.

        Before send to scan, file will be checked if not scanned before, for save bandwich and VT resources :)
        """

        result = False

        if len(files) == 1 and isinstance(files, list):

            if isinstance(files[0], basestring):
                pass
            else:
                if os.path.isdir(files[0]):
                    files = glob.glob('{files}'.format(files=files[0]))

        elif isinstance(files, basestring):
            if os.path.isdir(files[0]):
                files = glob.glob('{files}'.format(files=files))

        if notify_url:
            self.params.setdefault('notify_url', notify_url)

            if notify_changes_only:
                self.params.setdefault('notify_changes_only', notify_changes_only)

        url = self.base + 'file/scan'

        if not scan:
            for index, c_file in enumerate(files):
                if os.path.isfile(c_file):

                   files[index] = hashlib.md5(open(c_file, 'rb').read()).hexdigest()

        for submit_file in files:

            not_exit = True
            # Check all list of files, not only one
            result = self.getReport(
                    submit_file, False, verbose, dump, csv_write, not_exit, submit_file, privateAPI=privateAPI)

            if not result and scan == True:

                if (os.path.getsize(submit_file) / 1048576) <= 32:

                    if os.path.isfile(submit_file):

                        file_name = os.path.split(submit_file)[-1]
                        files = {"file": (file_name, open(submit_file, 'rb'))}

                        try:

                            jdata, response = get_response(
                                url, files=files, params=self.params, method="post")

                            if jdata['response_code'] == 0 or jdata['response_code'] == -1:
                                if jdata.get('verbose_msg'):
                                    print '\n[!] Status : {verb_msg}\n'.format(verb_msg=jdata['verbose_msg'])
                                return

                            if jdata.get('md5'):
                                print '\n\tResults for MD5    : {md5}'.format(md5=jdata['md5'])
                            if jdata.get('sha1'):
                                print '\tResults for SHA1   : {sha1}'.format(sha1=jdata['sha1'])
                            if jdata.get('sha256'):
                                print '\tResults for SHA256 : {sha256}'.format(sha256=jdata['sha256'])

                            if jdata.get('verbose_msg'):
                                print '\n\tStatus         : {verb_msg}'.format(verb_msg=jdata['verbose_msg'])
                            if jdata.get('permalink'):
                                print '\tPermanent link : {permalink}\n'.format(permalink=jdata['permalink'])

                        except UnicodeDecodeError:
                            print '\n[!] Sorry filaname is not utf-8 format, other format not suported at the moment'
                            print '[!] Ignored file: {file}\n'.format(file=submit_file)

                else:
                    print '[!] Ignored file: {file}, size is to big, permitted size is 32Mb'.format(file=submit_file)

            elif not result and scan == False:
                print '\nReport for file/hash : {0} not found'.format(submit_file)

    def url_scan_and_report(self, urls, key, verbose, dump=False, csv_write=False, add_to_scan='0', privateAPI=False):

        """
        Url scan:
        URLs can also be submitted for scanning. Once again, before performing your submission we encourage you to retrieve the latest report on the URL,
        if it is recent enough you might want to save time and bandwidth by making use of it.

        Url report:
        A URL will retrieve the most recent report on the given URL. You may also specify a scan_id (sha256-timestamp as returned by the URL submission API)
        to access a specific report. At the same time, you can specify a space separated list made up of a combination of hashes and scan_ids so as to perform a batch
        request with one single call (up to 4 resources or 25 if you have private api, per call with the standard request rate).
        """

        url_uploads = []
        result = False
        md5 = ''

        if os.path.basename(urls[0]) != 'urls_for_scan.txt':

            result, name = is_file(urls)

        else:
            result = False

            if os.path.isfile(urls[0]):
                urls = open(urls[0], 'rb').readlines()

        if result:
            jdata = load_file(name)
            dump = False

        else:

            if isinstance(urls, list) and len(urls) == 1:
                url_uploads = [urls]

            elif isinstance(urls, basestring):
                url_uploads = [urls]

            elif len(urls) > 1 and not isinstance(urls, basestring):

                if privateAPI:
                    start = -25
                    increment = 25
                else:
                    start = -4
                    increment = 4

                end = 0

                while True:

                    start += increment

                    if len(urls) > end + increment:
                        end += increment
                    elif len(urls) <= end + increment:
                        end = len(urls)

                    if key == 'scan':
                        url_uploads.append(
                            ['\n'.join(map(lambda url: url.replace(',', '').strip(), urls[start:end]))])

                    elif key == 'report':
                        url_uploads.append(
                            ['\n'.join(map(lambda url: url.replace(',', '').strip(), urls[start:end]))])

                    if end == len(urls):
                        break
        cont = 0

        for url_upload in url_uploads:

            cont += 1

            if key == 'scan':
                print 'Submitting url(s) for analysis: \n\t{url}'.format(url=url_upload[0].replace(', ', '\n\t'))
                self.params.setdefault('url', url_upload[0])
                url = self.base + 'url/scan'

            elif key == 'report':
                print '\nSearching for url(s) report: \n\t{url}'.format(url=url_upload[0].replace(', ', '\n\t'))
                self.params.setdefault('resource', url_upload[0])
                self.params.setdefault('scan', add_to_scan)
                url = self.base + 'url/report'

            jdata, response = get_response(url, params=self.params, method="post")

            if isinstance(jdata, list):

                for jdata_part in jdata:
                    if jdata_part is None:
                        print '[-] Nothing found'

                    elif 'response_code' in jdata_part and jdata_part['response_code'] == 0 or jdata_part['response_code'] == -1:
                        if jdata_part.get('verbose_msg'):
                            print '\n[!] Status : {verb_msg}\n'.format(verb_msg=jdata_part['verbose_msg'])
                    else:
                        if dump:
                            md5 = hashlib.md5(jdata_part['url']).hexdigest()

                        if key == 'report':
                            url_report = True
                            parse_report(
                                jdata_part, md5, verbose, dump, csv_write ,url_report)

                        elif key == 'scan':
                            if jdata_part.get('verbose_msg'):
                                print '\n\tStatus : {verb_msg}\t{url}'.format(verb_msg=jdata_part['verbose_msg'], url=jdata_part['url'])
                            if jdata_part.get('permalink'):
                                print '\tPermanent link : {permalink}'.format(permalink=jdata_part['permalink'])

            else:
                if jdata is None:
                    print '[-] Nothing found'

                elif  'response_code' in jdata and jdata['response_code'] == 0 or jdata['response_code'] == -1:
                    if jdata.get('verbose_msg'):
                        print '\n[!] Status : {verb_msg}\n'.format(verb_msg=jdata['verbose_msg'])

                else:
                    if dump:
                        md5 = hashlib.md5(jdata['url']).hexdigest()

                    if key == 'report':
                        url_report = True
                        parse_report(
                            jdata, md5, verbose, dump, csv_write, url_report)

                    elif key == 'scan':
                        if jdata.get('verbose_msg'):
                            print '\n\tStatus : {verb_msg}\t{url}'.format(verb_msg=jdata['verbose_msg'], url=jdata['url'])
                        if jdata.get('permalink'):
                            print '\tPermanent link : {permalink}'.format(permalink=jdata['permalink'])

            if cont % 4 == 0:
                print '[+] Sleep 60 seconds between the requests'
                time.sleep(60)

    def getIP(self, ips, dump=False, detected_urls=False, detected_downloaded_samples=False, undetected_downloaded_samples=False,
        detected_communicated=False, undetected_communicated=False, asn=False, detected_referrer_samples=False, undetected_referrer_samples=False, country=False, passive_dns=False):
        """
        A valid IPv4 address in dotted quad notation, for the time being only IPv4 addresses are supported.
        """
        jdatas = list()
        try:
            result, name = is_file(ips[0])

            if result:
                jdatas = [load_file(name)]
                dump = False
                md5 = ''

        except IndexError:
            print 'Something going wrong'
            return

        if not jdatas:

            if isinstance(ips, list) and len(ips) == 1:
                pass

            elif isinstance(ips, basestring):
                ips = [ips]

            ips = map(lambda ip: urlparse(ip).netloc if ip.startswith(('http://', 'https://')) else ip, ips)

            url = self.base + 'ip-address/report'
            for ip in ips:
                self.params.setdefault('ip', ip)

                jdata, response = get_response(url, params=self.params)
                jdatas.append((ip, jdata))

                self.params.pop('ip')

        for ip, jdata in jdatas:

            if jdata['response_code'] == 0 or jdata['response_code'] == -1:
                if jdata.get('verbose_msg'):
                    print '\n[-] Status {ip}: {verb_msg}\n'.format(verb_msg=jdata['verbose_msg'], ip=ip)

            elif jdata['response_code'] == 1:

                if jdata.get('verbose_msg'):
                    print '\n[+] Status {ip}: {verb_msg}'.format(verb_msg=jdata['verbose_msg'], ip=ip)

                if asn and jdata.get('asn'):
                    print '\n[+] ASN: {0}'.format(jdata['asn'])

                if country and jdata.get('country'):
                    print '\n[+] Country: {0}'.format(jdata['country'])

                print_results(jdata,
                              undetected_downloaded_samples,
                              detected_communicated,
                              undetected_communicated,
                              detected_urls,
                              detected_downloaded_samples,
                              detected_referrer_samples,
                              undetected_referrer_samples
                )

                if passive_dns and jdata.get('resolutions'):
                    print '\n[+] Lastest domain resolved\n'
                    pretty_print(sorted(jdata['resolutions'], key=methodcaller(
                        'get', 'last_resolved'), reverse=True), ['last_resolved', 'hostname'])

                if dump is True:
                    md5 = hashlib.md5(name).hexdigest()
                    jsondump(jdata, md5)

        return

    def getDomain(self, domains, dump=False, trendmicro=False, detected_urls=False, detected_downloaded_samples=False, undetected_downloaded_samples=False, alexa_domain_info=False,
        wot_domain_info=False, websense_threatseeker=False, bitdefender=False, webutation_domain=False,
        detected_communicated=False, undetected_communicated=False, pcaps=False, walk=False, whois=False,
        whois_timestamp=False, detected_referrer_samples=False, undetected_referrer_samples=False, passive_dns=False,
        subdomains=False, domain_siblings=False, categories=False, drweb_cat=False ,alexa_cat=False, alexa_rank=False, opera_info=False):
        """
        Get domain last scan, detected urls and resolved IPs
        """

        jdatas = list()

        try:
            result, name = is_file(domains[0])

            if result:
                jdatas = [load_file(name)]
                dump = False
                md5 = ''

        except IndexError:
            print '[-] Something going wrong'
            return

        if not jdatas:

            if isinstance(domains, list) and len(domains) == 1:
                    pass

            elif isinstance(domains, basestring):
                domains = [domains]

            domains = map(lambda domain: urlparse(domain).netloc if domain.startswith(('http://', 'https://')) else domain, domains)

            url = self.base + "domain/report"
            for domain in domains:
                self.params.setdefault('domain', domain)

                jdata, response = get_response(url, params=self.params)
                jdatas.append((domain, jdata))

        for domain, jdata in jdatas:
            if jdata['response_code'] == 0 or jdata['response_code'] == -1:
                if jdata.get('verbose_msg'):
                    print '\n[!] Status : {verb_msg} : {domain}\n'.format(verb_msg=jdata['verbose_msg'], domain=domain)

            if jdata.get('response_code') and jdata['response_code'] == 1:

                if jdata.get('verbose_msg'):
                    print '\nStatus : {verb_msg}'.format(verb_msg=jdata['verbose_msg'])

                if jdata.get('categories') and categories:

                    print '\n[+] Categories'
                    print '\t{0}'.format('\n\t'.join(jdata['categories']))

                if jdata.get('TrendMicro category') and trendmicro:

                    print '\n[+] TrendMicro category'
                    print '\t', jdata['TrendMicro category']

                if jdata.get('Websense ThreatSeeker category') and websense_threatseeker:

                    print '\n[+] Websense ThreatSeeker category'
                    print '\t', jdata['Websense ThreatSeeker category']

                if jdata.get('BitDefender category') and bitdefender:

                    print '\n[+] BitDefender category'
                    print '\t', jdata['BitDefender category']
                #ToDo add options to not show
                if jdata.get('Dr.Web category') and drweb_cat:

                    print '\n[+] Dr.Web category'
                    print '\t', jdata['Dr.Web category']

                if jdata.get('Alexa domain info') and alexa_domain_info:

                    print '\n[+] Alexa domain info'
                    print '\t', jdata['Alexa domain info']

                if jdata.get('Alexa category')  and alexa_cat:

                    print '\n[+] Alexa category'
                    print '\t', jdata['Alexa category']

                #ToDo add options to not show
                if jdata.get('Alexa rank') and alexa_rank:

                    print '\n[+] Alexa rank:'
                    print '\t', jdata['Alexa rank']

                #ToDo add options to not show
                if jdata.get('Opera domain info') and opera_info:

                    print '\n[+] Opera domain info'
                    print '\t', jdata['Opera domain info']

                if jdata.get('WOT domain info') and wot_domain_info:

                    print '\n[+] WOT domain info'
                    plist = [[]]

                    for jdata_part in jdata['WOT domain info']:
                        plist.append(
                            [jdata_part, jdata['WOT domain info'][jdata_part]])

                    pretty_print_special(
                        plist, ['Name', 'Value'], [25, 20], ['c', 'c'])

                    del plist

                if jdata.get('Webutation domain info') and webutation_domain:

                    print "\n[+] Webutation"
                    plist = [[]]

                    for jdata_part in jdata['Webutation domain info']:
                        plist.append(
                            [jdata_part, jdata['Webutation domain info'][jdata_part]]
                            )

                    pretty_print_special(
                        plist, ['Name', 'Value'], [25, 20], ['c', 'c'])

                    del plist

                if jdata.get('whois') and whois:
                    print '\n[+] Whois data:'
                    print '\t{0}'.format(jdata['whois'].replace('\n', '\n\t'))

                if  jdata.get('whois_timestamp') and whois_timestamp:
                    print '\n[+] Whois timestamp:'
                    print '\t{0}'.format(datetime.fromtimestamp(float(jdata['whois_timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))

                print_results(jdata,
                              undetected_downloaded_samples,
                              detected_communicated,
                              undetected_communicated,
                              detected_urls,
                              detected_downloaded_samples,
                              detected_referrer_samples,
                              undetected_referrer_samples
                )

                if jdata.get('pcaps') and pcaps:

                    print '\n'
                    pretty_print(jdata['pcaps'], ['pcaps'], [70], ['c'])

                if passive_dns and jdata.get('resolutions'):

                    print '\n[+] Passive DNS replication\n'
                    pretty_print(sorted(jdata['resolutions'], key=methodcaller(
                        'get', 'last_resolved'), reverse=True),
                        ['last_resolved', 'ip_address'],
                        [25, 20],
                        ['c', 'c']
                        )

                    if walk:
                        filter_ip = list()
                        for ip in sorted(jdata['resolutions'], key=methodcaller('get', 'last_resolved'), reverse=True):
                            if ip['ip_address'] not in filter_ip:
                                print '\n\n[+] Checking data for ip: {0}'.format(ip['ip_address'])

                                self.getIP([ip['ip_address']],
                                    dump,
                                    detected_urls,
                                    undetected_downloaded_samples,
                                    detected_communicated,
                                    undetected_communicated,
                                    detected_referrer_samples,
                                    detected_downloaded_samples,
                                    detected_downloaded_samples,
                                    undetected_referrer_samples
                                )

                if subdomains and jdata.get('subdomains'):
                    print '\n[+] Subdomains:'
                    print '\t{0}'.format('\n\t'.join(jdata['subdomains']))

                if domain_siblings and jdata.get('domain_siblings'):
                    print '\n[+] Domain siblings:'
                    print '\t{0}'.format('\n\t'.join(jdata['domain_siblings']))

                if dump is True:
                    md5 = hashlib.md5(name).hexdigest()
                    jsondump(jdata, md5)


    def clusters(self, value, dump=False, by_id=False):

        """
        VirusTotal has built its own in-house file similarity clustering functionality. At present,
        this clustering works only on PE files and is based on a very basic PE feature hash, which
        can be very often confused by certain compression and packing strategies. In other words,
        this clustering logic is no holly grail.

        This API offers a programmatic access to the clustering section of VirusTotal Intelligence:

        https://www.virustotal.com/intelligence/clustering/

        Please note that you must be logged in with a valid VirusTotal Community user with access
        to VirusTotal Intelligence in order to be able to view the clustering listing.

        All of the API responses are JSON objects, if no clusters were identified for the given
        time frame, this JSON will have a response_code property equal to 0, if there was some
        sort of error with your query this code will be set to -1, if your query succeded and
        file similarity clusters were found it will have a value of 1 and the rest of the JSON
        properties will contain the clustering information.
        """

        result, name = is_file(value)

        if result:
            jdata = load_file(name)
            dump = False

        else:
            url = self.base + 'file/clusters'

            if by_id:
                self.params.setdefault('query', 'cluster:{0}'.format(value))

            else:
                self.params.setdefault('date', name)

            jdata, response = get_response(url, params=self.params)

        if jdata['response_code'] == 0 or jdata['response_code'] == -1:
            if jdata.get('verbose_msg'):
                print '\n[!] Status : {verb_msg}\n'.format(verb_msg=jdata['verbose_msg'])
            return

        if jdata.get('verbose_msg'):
            print '\nStatus : {verb_msg}'.format(verb_msg=jdata['verbose_msg'])
        if jdata.get('size_top200'):
            print '\n\tSize top 200   : {size_top200}'.format(size_top200=jdata['size_top200'])
        if jdata.get('num_clusters'):
            print '\tNum Clusters   : {num_clusters}'.format(num_clusters=jdata['num_clusters'])
        if jdata.get('num_candidates'):
            print '\tNum Candidates : {num_candidates}'.format(num_candidates=jdata['num_candidates'])

        if jdata.get('clusters'):

            plist = [[]]

            for line in jdata['clusters']:
                plist.append(
                    [line['label'], line['avg_positives'], line['id'], line['size']])

            pretty_print_special(
                plist,
                ['Label', 'AV Detections', 'Id', 'Size'],
                [40, 15, 80, 8],
                ['l', 'c', 'l', 'c']
            )

        if dump:
            jsondump(jdata, 'clusters_{0}'.format(name))

    def comment(self, hash_co, action, dump=False, before_or_comment=False):
        """
        Add comment:
        The actual review, you can tag it using the "#" twitter-like syntax (e.g. #disinfection #zbot) and reference users using the "@" syntax (e.g. @VirusTotalTeam).

        Get comments:
        The application answers with the comments sorted in descending order according to their date. Please note that, for timeout reasons, the application will only
        answer back with at most 25 comments. If the answer contains less than 25 comments it means that there are no more comments for that item. On the other hand,
        if 25 comments were returned you should keep issuing further calls making use of the optional before parameter, this parameter should be fixed to the oldest
        (last in the list) comment's date token, exactly in the same way as returned by your previous API call (e.g. 20120404132340).
        """

        result, name = is_file(hash_co)

        if result:
            jdata = load_file(name)

        else:
            self.params.setdefault('resource', hash_co)

            if action == 'add':
                url = self.base + 'comments/put'
                self.params.setdefault('comment', before_or_comment)

                jdata, response = get_response(
                    url, params=self.params, method="post")

            elif action == 'get':
                url = self.base + 'comments/get'

                if before_or_comment:
                    self.params.setdefault('before', before_or_comment)

                jdata, response = get_response(url, params=self.params)

            else:
                print '\n[!] Support only get/add comments action \n'
                return

        if jdata['response_code'] == 0 or jdata['response_code'] == -1:
            if jdata.get('verbose_msg'):
                print '\n[!] Status : {verb_msg}\n'.format(verb_msg=jdata['verbose_msg'])
            sys.exit()

        if action == 'add':
            if jdata.get('verbose_msg'):
                print '\nStatus : {0}\n'.format(jdata['verbose_msg'])

        else:
            if jdata['response_code'] == 0:
                print '\n[!] This analysis doen\'t have any comment\n'

            else:
                if jdata.get('comments'):
                    for comment in jdata['comments']:

                        date_format = time.strptime(
                            comment['date'], '%Y%m%d%H%M%S')
                        date_formated = '{year}:{month}:{day} {hour}:{minuts}:{seconds}'.format(
                            year=date_format.tm_year, month=date_format.tm_mon,
                            day=date_format.tm_mday, hour=date_format.tm_hour,
                            minuts=date_format.tm_min, seconds=date_format.tm_sec
                            )

                        if comment.get('date'):
                            print 'Date    : {0}'.format(date_formated)
                        if comment.get('comment'):
                            print 'Comment : {0}\n'.format(comment['comment'])

    def download(self, hashes, intelligence, file_type=False):
        """
          About pcaps
          VirusTotal runs a distributed setup of Cuckoo sandbox machines that execute the files we receive.
          Execution is attempted only once, upon first submission to VirusTotal, and only Portable Executables
          under 10MB in size are ran. The execution of files is a best effort process, hence, there are no guarantees
          about a report being generated for a given file in our dataset.

          Files that are successfully executed may communicate with certain network resources, all this communication
          is recorded in a network traffic dump (pcap file). This API allows you to retrieve the network traffic dump
          generated during the file's execution.

          The md5/sha1/sha256 hash of the file whose network traffic dump you want to retrieve.
        """
        response = ''
        super_file_type = file_type

        result, name = is_file(hashes)

        if result:
            hashes = open(hashes, 'rb').readlines()

        if isinstance(hashes, list) and len(hashes) == 1:
            hashes = hashes
            print hashes

        elif isinstance(hashes, basestring):
            hashes = [hashes]

        for f_hash in hashes:

            f_hash = f_hash.strip()

            if f_hash != '':

                if f_hash.find(',') != -1:
                    file_type = f_hash.split(',')[-1]
                    f_hash = f_hash.split(',')[0]
                else:
                    file_type = super_file_type

                self.params.setdefault('hash', f_hash)

                #print '\nTrying to download: {0}'.format(f_hash)

                if not intelligence:

                    if file_type not in ('file', 'pcap'):
                        print '\n[!] File_type must be pcap or file\n'
                        return

                    if file_type == 'pcap':
                        _, response = get_response(
                            self.base + 'file/network-traffic', params=self.params)
                        name = 'VTDL_{hash}.pcap'.format(hash=f_hash)

                    elif file_type == 'file':
                        _, response = get_response(
                            self.base + 'file/download', params=self.params)
                        name = 'VTDL_{hash}.dangerous'.format(hash=f_hash)

                    if response.status_code == 404:
                        print '\n[!] File not found\n'
                        return

                else:
                    name = 'VTDL_{hash}.dangerous'.format(hash=f_hash)
                    _, response = get_response(
                            'https://www.virustotal.com/intelligence/download/', params=self.params)

                if len(response.content) > 0 and '{"response_code": 0, "hash":' not in response.content:
                    fo = open(name, "wb")
                    fo.write(response.content)
                    fo.close()
                    print '\tDownloaded to File -- {name}'.format(name=name)
                else:
                    try:
                        json_data = response.json()
                        print '\n\t{0}: {1}'.format(json_data['verbose_msg'], f_hash)
                    except:
                        print '\tFile can\'t be downloaded: {0}'.format(f_hash)

    def distribution(self, local_file, action, before=False, after=False, reports=False, limit=False, allinfo=False, dump=False):
        """
        Note that scan items are not kept forever in the distribution queue, they are automatically removed after 6 hours counting from the time
        they were put in the queue. You have a 6 hours time frame to get an item from the queue. The timestamp property value is what you need to
        iterate through your queue using the before and after call parameters.
        """

        result, name = is_file(local_file)

        if result:
            jdata = load_file(name)
            dump = False

        else:

            if before:
                self.params.setdefault('before', before)

            if after:
                self.params.setdefault('after', after)

            if limit:
                self.params.setdefault('limit', limit)

            if action == 'file':

                if reports:
                    self.params.setdefault('reports', str(reports).lower())

                url = self.base + 'file/distribution'

            elif action == 'url':

                if allinfo:

                    self.params.setdefault('allinfo', '1')

                url = self.base + 'url/distribution'

            jdata, response = get_response(url, params=self.params)

        if jdata['response_code'] == 0 or jdata['response_code'] == -1:
            if jdata.get('verbose_msg'):
                print '\n[!] Status : {verb_msg}\n'.format(verb_msg=jdata['verbose_msg'])
            return

        for vt_file in jdata:

            if action == 'file':

                try:
                    if vt_file.get('name'):
                        print '\n\nName   : {name}'.format(name=vt_file['name'])

                except UnicodeEncodeError:
                    print ''

                if vt_file.get('md5'):
                    print '\nMD5    : {md5}'.format(md5=vt_file['md5'])
                if vt_file.get('sha1'):
                    print 'SHA1   : {sha1}'.format(sha1=vt_file['sha1'])
                if vt_file.get('sha256'):
                    print 'SHA256 : {sha256}'.format(sha256=vt_file['sha256'])

                if vt_file.get('filetype'):
                    print '\nType   : {filetype}'.format(filetype=vt_file['filetype'])
                if vt_file.get('size'):
                    print 'Size   : {size}'.format(size=vt_file['size'])

                if vt_file.get('source_id'):
                    print 'Source Id  : {source_id}'.format(source_id=vt_file['source_id'])
                if vt_file.get('first_seen'):
                    print 'First Seen : {first_seen}'.format(first_seen=vt_file['first_seen'])
                if vt_file.get('last_seen'):
                    print 'Last  Seen : {last_seen}'.format(last_seen=vt_file['last_seen'])

                if vt_file.get('report'):

                    plist = [[]]

                    for key in vt_file['report']:
                        plist.append(
                          [key, 'True' if jdata[0]['report'][key][0] else 'False', jdata[0]['report'][key][1], jdata[0]['report'][key][2]]
                        )

                    pretty_print_special(
                        plist, ['Vendor name', 'Detection', 'Version', 'Update'])

                if vt_file.get('link'):
                    print '\nLink : {link}'.format(link=vt_file['link'])

            elif action == 'url':

                if vt_file.get('scan_date'):
                    print '\nScan Date : {scan_date}'.format(scan_date=vt_file['scan_date'])
                if vt_file.get('last_seen'):
                    print 'Last Seen : {last_seen}'.format(last_seen=vt_file['last_seen'])
                if vt_file.get('positives') and vt_file.get('total'):
                    print '\nDetections:\n\t{positives}/{total} Positives/Total\n'.format(positives=vt_file['positives'], total=vt_file['total'])

                if vt_file.get('score'):
                    print 'Score     : {score}'.format(score=vt_file['score'])
                if vt_file.get('url'):
                    print 'Url       : {url}'.format(url=vt_file['url'])

                if vt_file.get('timestamp'):
                    print 'Timestamp : {timestamp}'.format(timestamp=vt_file['timestamp'])

                if vt_file.get('additional_info'):

                    print '\n\nAdditional info:'
                    plist = [[]]

                    for key in vt_file['additional_info']:

                        if isinstance(vt_file['additional_info'][key], dict):
                            plist.append([key, ''.join(map(lambda key_temp:'{key_temp}:{value}\n'.format(
                                key_temp=key_temp, value=vt_file['additional_info'][key][key_temp]), vt_file['additional_info'][key]))])

                        elif isinstance(vt_file['additional_info'][key], list):
                            plist.append(
                                [key, '\n'.join(vt_file['additional_info'][key])])

                        else:
                            plist.append(
                                [key, vt_file['additional_info'][key]])

                    pretty_print_special(plist, ['Name', 'Value'], [40, 70])

                if vt_file.get('scans'):

                    plist = [[]]

                    for key in vt_file['scans']:

                        plist.append([key, 'True' if vt_file['scans'][key][
                                     'detected'] else 'False', vt_file['scans'][key]['result']])

                    pretty_print_special(
                        plist, ['Vendor name', 'Detection', 'Result'])

                if vt_file.get('permalink'):
                    print '\nPermanent link : {link}\n'.format(link=vt_file['permalink'])

        if dump:
            jsondump(jdata, 'distribution_{date}'.format(
                date=time.strftime("%Y-%m-%d")))

    def behaviour(self, search_hash, dump=False, network=False, process=False, summary=False):

        result, name = is_file(search_hash)

        if result:
            jdata = load_file(name)
            dump = False

        else:
            self.params.setdefault('hash', search_hash)
            url = self.base + 'file/behaviour'

            jdata, response = get_response(url, params=self.params)

        if 'response_code' in jdata and (jdata['response_code'] == 0 or jdata['response_code'] == -1):
            if jdata.get('verbose_msg'):
                print '\n[!] Status : {verb_msg}\n'.format(verb_msg=jdata['verbose_msg'])
            return

        if jdata['info']:
            print '\nInfo\n'

            pretty_print(
                jdata['info'], ['started', 'ended', 'duration', 'version'])

        if network:

            print '\nHTTP requests\n'

            if 'network' in jdata and 'http' in jdata['network']:
                for http in jdata['network']['http']:

                    if http.get('uri'):
                        print '\tURL        : {0}'.format(http['uri'])
                    if http.get('host'):
                        print '\tHost       : {0}'.format(http['host'])
                    # if http.get('port') : print 'port       : {0}'.format(http['port'])
                    # if http.get('path') : print 'path       :
                    # {0}'.format(http['path'])
                    if http.get('method'):
                        print '\tMethod     : {0}'.format(http['method'])
                    if http.get('user-agent'):
                        print '\tUser-agent : {0}'.format(http['user-agent'])
                    # if http.get('version') : print 'version    : {0}'.format(http['version'])
                    # if http.get('data')    : print 'data       : {0}'.format(http['data'].replace('\r\n\r\n', '\n\t').replace('\r\n','\n\t\t'))
                    # if http.get('body')    : print 'body       :
                    # {0}'.format(http['body'])
                    print '\n'

            if jdata['network']['hosts']:
                pretty_print(jdata['network']['hosts'], ['hosts'])

            if jdata['network']['dns']:
                print '\nDNS requests\n'
                pretty_print(jdata['network']['dns'],   ['ip', 'hostname'])

            if jdata['network']['tcp']:
                print '\nTCP Connections\n'

                unique = []

                for block in jdata['network']['tcp']:

                    if not [block['src'],  block['dst'], block['sport'], block['dport']] in unique:

                        unique.append(
                            [block['src'], block['dst'], block['sport'], block['dport']]
                        )

                pretty_print_special(unique,   ['src', 'dst', 'sport', 'dport'])

                del unique

            if jdata['network']['udp']:
                print '\nUDP Connections'

                unique = []

                for block in jdata['network']['udp']:

                    if not [block['src'],  block['dst'], block['sport'], block['dport']] in unique:

                        unique.append(
                            [block['src'], block['dst'], block['sport'], block['dport']]
                            )

                pretty_print_special(
                  unique,
                  ['src', 'dst', 'sport', 'dport']
                  )

                del unique

        if process:
            print '\nBehavior\n'
            print '\nProcesses\n'

            for process_id in jdata['behavior']['processes']:

                plist = []

                if process_id.get('parent_id'):
                    print '\nParent  Id : {0}'.format(process_id['parent_id'])
                if process_id.get('process_id'):
                    print 'Process Id : {0}'.format(process_id['process_id'])

                if process_id.get('first_seen'):

                    date_format = time.strptime(
                        process_id['first_seen'][:14], '%Y%m%d%H%M%S')
                    date_formated = '{year}:{month}:{day} {hour}:{minuts}:{seconds}'.format(year=date_format.tm_year, month=date_format.tm_mon,
                                                                                            day=date_format.tm_mday, hour=date_format.tm_hour,
                                                                                            minuts=date_format.tm_min, seconds=date_format.tm_sec)
                    print 'First Seen : {0}'.format(date_formated)

                if process_id.get('process_name'):
                    print '\nProcess Name : {0}'.format(process_id['process_name'])

                if process_id.get('calls'):

                    for process_part in process_id['calls']:

                        plist = [[]]

                        for key in process_part:

                            if isinstance(process_part[key], list):
                                if process_part[key] != [] and isinstance(process_part[key][0], dict):

                                    temp_list = []

                                    for part in process_part[key]:

                                        temp_list.append('\n'.join(map(lambda key_temp: '{key_temp}:{value}\n'.format(
                                            key_temp=key_temp, value=part[key_temp]), part.keys())))

                                    plist.append([key, ''.join(temp_list)])

                                    del temp_list
                                else:
                                    plist.append(
                                        [key, '\n'.join(process_part[key])])

                            elif isinstance(process_part[key], dict):

                                temp_list = []

                                for part in process_part[key]:
                                    temp_list += map(lambda key_temp: '{key_temp}:{value}\n'.format(
                                        key_temp=key_temp, value=part[key_temp]), part.keys())

                                plist.append([key, ''.join(temp_list)])

                                del temp_list
                            else:
                                plist.append([key, process_part[key]])

                        pretty_print_special(
                            plist, ['Name', 'Value'], [10, 50])

                        del plist

                    print '\n' + '=' * 20 + ' FIN ' + '=' * 20

            print '\nProcess Tree\n'
            for tree in jdata['behavior']['processtree']:
                for key in tree.keys():
                    print '\t{key}:{value}'.format(key=key, value=tree[key])
            print '\n'

        if summary:

            if jdata['behavior']['summary']['files']:
                print '\nOpened files\n'
                pretty_print(
                    sorted(jdata['behavior']['summary']['files']), ['files'], [100])

            if jdata['behavior']['summary']['keys']:
                print '\nSet keys\n'
                pretty_print(
                    sorted(jdata['behavior']['summary']['keys']), ['keys'], [100])


            if jdata['behavior']['summary']['mutexes'] is not None and jdata['behavior']['summary']['mutexes'] != [u'(null)']:
                print '\nCreated mutexes\n'
                pretty_print(
                    sorted(jdata['behavior']['summary']['mutexes']), ['mutexes'], [100]
                    )

        if dump is True:
            md5 = hashlib.md5(name).hexdigest()
            jsondump(jdata, md5)

def main():

    opt = argparse.ArgumentParser(
        'value', description='Scan/Search/ReScan/JSON parse')

    opt.add_argument(
        'value', nargs='*', help='Enter the Hash, Path to File(s) or Url(s)')
    opt.add_argument('-c', '--config-file', action='store',
                     default='~/.vtapi', help='Path to configuration file')

    opt.add_argument('-fs', '--file-search', action='store_true',
                     help='File(s) search, this option, don\'t upload file to VirusTotal, just search by hash, support linux name wildcard, example: /home/user/*malware*, if file was scanned, you will see scan info, for full scan report use verbose mode, and dump if you want save already scanned samples')
    opt.add_argument('-f',  '--file-scan', action='store_true', dest='files',
                     help='File(s) scan, support linux name wildcard, example: /home/user/*malware*, if file was scanned, you will see scan info, for full scan report use verbose mode, and dump if you want save already scanned samples')
    opt.add_argument('-u',  '--url-scan', action='store_true',
                     help='Url scan, support space separated list, Max 4 urls (or 25 if you have private api), but you can provide more urls, for example with public api,  5 url - this will do 2 requests first with 4 url and other one with only 1, or you can specify file filename must be urls_for_scan.txt, and one url per line')
    opt.add_argument('-ur', '--url-report', action='store_true',
                     help='Url(s) report, support space separated list, Max 4 (or 25 if you have private api) urls, you can use --url-report --url-scan options for analysing url(s) if they are not in VT data base, read previev description about more then max limits or file with urls')

    opt.add_argument('-d', '--domain-info',   action='store_true', dest='domain',
                     help='Retrieves a report on a given domain (PRIVATE API ONLY! including the information recorded by VirusTotal\'s Passive DNS infrastructure)')
    opt.add_argument('-i', '--ip-info', action='store_true', dest='ip',
                     help='A valid IPv4 address in dotted quad notation, for the time being only IPv4 addresses are supported.')
    opt.add_argument('-w', '--walk', action='store_true', default=False,
                     help='Work with domain-info, will walk throuth all detected ips and get information, can be provided ip parameters to get only specific information')
    opt.add_argument('-s', '--search', action='store_true',
                     help='A md5/sha1/sha256 hash for which you want to retrieve the most recent report. You may also specify a scan_id (sha256-timestamp as returned by the scan API) to access a specific report. You can also specify a space separated list made up of a combination of hashes and scan_ids Public API up to 4 items/Private API up to 25 items, this allows you to perform a batch request with one single call.')
    opt.add_argument('--report-all-info', action='store_true',
                     help='PRIVATE API ONLY! If specified and set to one, the call will return additional info, other than the antivirus results, on the file being queried. This additional info includes the output of several tools acting on the file (PDFiD, ExifTool, sigcheck, TrID, etc.), metadata regarding VirusTotal submissions (number of unique sources that have sent the file in the past, first seen date, last seen date, etc.), and the output of in-house technologies such as a behavioural sandbox.')
    opt.add_argument('-ac', '--add-comment', action='store_true',
                     help='The actual review, you can tag it using the "#" twitter-like syntax (e.g. #disinfection #zbot) and reference users using the "@" syntax (e.g. @VirusTotalTeam). supported hashes MD5/SHA1/SHA256')
    opt.add_argument('-gc', '--get-comments', action='store_true',
                     help='Either a md5/sha1/sha256 hash of the file or the URL itself you want to retrieve')
    opt.add_argument('--get-comments-before', action='store', dest='date', default=False,
                     help='PRIVATE API ONLY! A datetime token that allows you to iterate over all comments on a specific item whenever it has been commented on more than 25 times. Token format 20120725170000 or 2012-07-25 17 00 00 or 2012-07-25 17:00:00')

    opt.add_argument('-v', '--verbose', action='store_true',
                     dest='verbose', help='Turn on verbosity of VT reports')
    opt.add_argument('-j', '--dump',    action='store_true',
                     help='Dumps the full VT report to file (VTDL{md5}.json), if you (re)scan many files/urls, their json data will be dumped to separetad files')
    opt.add_argument('--csv', action='store_true', default = False,
                     help='Dumps the AV\'s detections to file (VTDL{scan_id}.csv)')

    rescan = opt.add_argument_group('Rescan options')
    rescan.add_argument('-r', '--rescan', action='store_true',
                        help='Allows you to rescan files in VirusTotal\'s file store without having to resubmit them, thus saving bandwidth, support space separated list, MAX 25 hashes, can be local files, hashes will be generated on the fly, support linux wildmask')
    rescan.add_argument('--delete',  action='store_true',
                        help='PRIVATE API ONLY! A md5/sha1/sha256 hash for which you want to delete the scheduled scan')
    rescan.add_argument('--date', action='store', dest='date',
                        help='PRIVATE API ONLY! A Date in one of this formats (example: 20120725170000 or 2012-07-25 17 00 00 or 2012-07-25 17:00:00) in which the rescan should be performed. If not specified the rescan will be performed immediately.')
    rescan.add_argument('--period', action='store',
                        help='PRIVATE API ONLY! Period in days in which the file should be rescanned. If this argument is provided the file will be rescanned periodically every period days, if not, the rescan is performed once and not repated again.')
    rescan.add_argument('--repeat', action='store',
                        help='PRIVATE API ONLY! Used in conjunction with period to specify the number of times the file should be rescanned. If this argument is provided the file will be rescanned the given amount of times, if not, the file will be rescanned indefinitely.')

    scan_rescan = opt.add_argument_group(
        'File scan/Rescan shared options  - PRIVATE API only!')
    scan_rescan.add_argument('--notify-url', action='store',
                             help='An URL where a POST notification should be sent when the scan finishes.')
    scan_rescan.add_argument('--notify-changes-only', action='store_true',
                             help='Used in conjunction with --notify-url. Indicates if POST notifications should be sent only if the scan results differ from the previous one.')

    domain_opt = opt.add_argument_group(
        'Domain/IP shared verbose mode options, by default just show resolved IPs/Passive DNS')
    domain_opt.add_argument('-wh',  '--whois', action='store_true', default=False,
                            help='Whois data')
    domain_opt.add_argument('-wht',  '--whois-timestamp', action='store_true', default=False,
                            help='Whois timestamp')
    domain_opt.add_argument('-pdn',  '--passive-dns', action='store_true', default=False,
                            help='Passive DNS resolves')
    domain_opt.add_argument('--asn', action='store_true', default=False,
                            help='ASN number')
    domain_opt.add_argument('--country', action='store_true', default=False,
                            help='Country')
    domain_opt.add_argument('--subdomains', action='store_true', default=False,
                            help='Subdomains')
    domain_opt.add_argument('--domain-siblings', action='store_true', default=False,
                            help='Domain siblings')
    domain_opt.add_argument('-cat','--categories', action='store_true', default=False,
                            help='Categories')
    domain_opt.add_argument('-alc', '--alexa-cat', action='store_true', default=False,
                            help='Alexa category')
    domain_opt.add_argument('-alk', '--alexa-rank', action='store_true', default=False,
                            help='Alexa rank')
    domain_opt.add_argument('-opi', '--opera-info', action='store_true', default=False,
                            help='Opera info')
    domain_opt.add_argument('--drweb-cat', action='store_true', default=False,
                            help='Dr.Web Category')
    domain_opt.add_argument('-adi', '--alexa-domain-info', action='store_true',
                            default=False, help='Just Domain option: Show Alexa domain info')
    domain_opt.add_argument('-wdi', '--wot-domain-info', action='store_true',
                            default=False, help='Just Domain option: Show WOT domain info')
    domain_opt.add_argument('-tm',  '--trendmicro', action='store_true',
                            default=False, help='Just Domain option: Show TrendMicro category info')
    domain_opt.add_argument('-wt',  '--websense-threatseeker', action='store_true',
                            default=False, help='Just Domain option: Show Websense ThreatSeeker category')
    domain_opt.add_argument('-bd',  '--bitdefender', action='store_true',
                            default=False, help='Just Domain option: Show BitDefender category')
    domain_opt.add_argument('-wd',  '--webutation-domain', action='store_true',
                            default=False, help='Just Domain option: Show Webutation domain info')
    domain_opt.add_argument('-du',  '--detected-urls', action='store_true',
                            default=False, help='Just Domain option: Show latest detected URLs')
    domain_opt.add_argument('--pcaps', action='store_true',
                            default=False, help='Just Domain option: Show all pcaps hashes')
    domain_opt.add_argument('-dds', '--detected-downloaded-samples',   action='store_true', default=False,
                            help='Domain/Ip options: Show latest detected files that were downloaded from this ip')
    domain_opt.add_argument('-uds', '--undetected-downloaded-samples', action='store_true', default=False,
                            help='Domain/Ip options: Show latest undetected files that were downloaded from this domain/ip')
    domain_opt.add_argument('-dc',  '--detected-communicated', action='store_true', default=False,
                            help='Domain/Ip Show latest detected files that communicate with this domain/ip')
    domain_opt.add_argument('-uc',  '--undetected-communicated', action='store_true', default=False,
                            help='Domain/Ip Show latest undetected files that communicate with this domain/ip')
    domain_opt.add_argument('-drs', '--detected-referrer-samples', action='store_true', default=False,
                            help='Undetected referrer sampels')
    domain_opt.add_argument('-urs', '--undetected-referrer-samples', action='store_true', default=False,
                            help='Undetected referrer sampels')


    behaviour = opt.add_argument_group('Behaviour options - PRIVATE API only!')
    behaviour.add_argument('--behaviour', action='store_true',  help='The md5/sha1/sha256 hash of the file whose dynamic behavioural report you want to retrieve.\
                       VirusTotal runs a distributed setup of Cuckoo sandbox machines that execute the files we receive. Execution is attempted only once, upon\
                       first submission to VirusTotal, and only Portable Executables under 10MB in size are ran. The execution of files is a best effort process,\
                       hence, there are no guarantees about a report being generated for a given file in our dataset. a file did indeed produce a behavioural report,\
                       a summary of it can be obtained by using the file scan lookup call providing the additional HTTP POST parameter allinfo=1. The summary will\
                       appear under the behaviour-v1 property of the additional_info field in the JSON report.This API allows you to retrieve the full JSON report\
                       of the file\'s execution as outputted by the Cuckoo JSON report encoder.')

    behaviour.add_argument('-bn', '--behavior-network',
                           action='store_true', help='Show network activity')
    behaviour.add_argument(
        '-bp', '--behavior-process', action='store_true', help='Show processes')
    behaviour.add_argument(
        '-bs', '--behavior-summary', action='store_true', help='Show summary')

    more_private = opt.add_argument_group('Additional PRIVATE API options')
    more_private.add_argument('--pcap', dest='download', action='store_const', const='pcap', default=False,
                              help='The md5/sha1/sha256 hash of the file whose network traffic dump you want to retrieve. Will save as VTDL_hash.pcap')
    more_private.add_argument('--download',  dest='download', action='store_const', const='file', default=False,
                                  help='The md5/sha1/sha256 hash of the file you want to download or txt file with hashes, or hash and type, one by line, for example: hash,pcap or only hash. Will save as VTDL_hash.dangerous')
    more_private.add_argument('--clusters', action='store_true',
                                  help='A specific day for which we want to access the clustering details, example: 2013-09-10')
    # more_private.add_argument('--search-by-cluster-id', action='store_true', help=' the id property of each cluster allows users to list files contained in the given cluster, example: vhash 0740361d051)z1e3z 2013-09-10')
    more_private.add_argument('--distribution-files', action='store_true',
                                  help='Timestamps are just integer numbers where higher values mean more recent files. Both before and after parameters are optional, if they are not provided the oldest files in the queue are returned in timestamp ascending order.')
    more_private.add_argument('--distribution-urls', action='store_true',
                                  help='Timestamps are just integer numbers where higher values mean more recent urls. Both before and after parameters are optional, if they are not provided the oldest urls in the queue are returned in timestamp ascending order.')

    dist = opt.add_argument_group(
            'Distribution options - PRIVATE API only!')
    dist.add_argument('--before', action='store',
                              help='File/Url option. Retrieve files/urls received before the given timestamp, in timestamp descending order.')
    dist.add_argument('--after', action='store',
                      help='File/Url option. Retrieve files/urls received after the given timestamp, in timestamp ascending order.')
    dist.add_argument('--reports', action='store_true', default=False,
                      help='Include the files\' antivirus results in the response. Possible values are \'true\' or \'false\' (default value is \'false\').')
    dist.add_argument('--limit', action='store',
                      help='File/Url option. Retrieve limit file items at most (default: 1000).')
    dist.add_argument('--allinfo', action='store_true',
                      help='will include the results for each particular URL scan (in exactly the same format as the URL scan retrieving API). If the parameter is not specified, each item returned will onlycontain the scanned URL and its detection ratio.')
    dist.add_argument('--massive-download', action='store_true',
                      default=False, help='Show information how to get massive download work')

    options = opt.parse_args()

    apikey = None
    api_type = False  # = Public
    intelligence = False

    try:
        confpath = os.path.expanduser(options.config_file)

        if os.path.exists(confpath):

            config = ConfigParser.RawConfigParser()
            config.read(confpath)

            if config.has_option('vt', 'apikey'):
                apikey = config.get('vt', 'apikey')

                if config.has_option('vt', 'type'):
                    api_type = config.get('vt', 'type')

                    if api_type not in ('public', 'private'):
                        api_type = False

                    elif  api_type == 'private':
                        api_type = True

                if config.has_option('vt', 'intelligence'):
                    intelligence = config.get('vt', 'intelligence')

        else:
            sys.exit('\nFile {0} don\'t exists\n'.format(confpath))

    except Exception:
        sys.exit('No API key provided and cannot read ~ / .vtapi. Specify an API key in vt.py or in ~ / .vtapi or in your file\n For mor information check https://github.com/doomedraven/VirusTotalApi')

    if apikey is None:
        sys.exit('No API key provided or can\'t read ~/.vtapi|config. Specify an API key in in ~/.vtapi|your config file\n For mor information check https://github.com/doomedraven/VirusTotalApi')

    vt = vtAPI(apikey)

    if options.date:
        options.date = options.date.replace( '-', '').replace(':', '').replace(' ', '')

    if options.verbose and (options.domain or options.ip or options.behaviour):
        options.detected_urls = options.undetected_downloaded_samples = options.wot_domain_info  = options.websense_threatseeker   = \
        options.detected_communicated = options.trendmicro = options.undetected_communicated = \
        options.alexa_domain_info = options.bitdefender = options.webutation_domain = options.pcaps = \
        options.detected_downloaded_samples = options.behavior_network = options.behavior_process = options.behavior_summary = options.whois =\
        options.asn = options.detected_referrer_samples = options.undetected_referrer_samples = options.country = options.passive_dns =\
        options.whois_timestamp = options.subdomains =  options.domain_siblings =\
        options.categories = options.drweb_cat = options.alexa_cat = options.alexa_rank = options.opera_info = True

    if options.files:
        vt.fileScan(options.value, options.verbose, options.notify_url,
                    options.notify_changes_only, options.dump, options.csv, api_type, scan=True)

    elif options.file_search:
        vt.fileScan(options.value, options.verbose, options.notify_url,
                    options.notify_changes_only, options.dump, options.csv, api_type)

    elif options.url_scan and not options.url_report:
        vt.url_scan_and_report(
            options.value, "scan", options.verbose, options.dump, options.csv, api_type)

    elif options.url_report:
        action = 0

        if options.url_scan:
            action = 1

        vt.url_scan_and_report(
            options.value, "report", options.verbose, options.dump, options.csv, action, api_type)

    elif options.rescan:

        if options.date:

            if len(options.date) < 14:
                print '\n[!] Date fotmar is: 20120725170000 or 2012-07-25 17 00 00 or 2012-07-25 17:00:00\n'
                return

            now = time.strftime("%Y:%m:%d %H:%M:%S")
            if now >= relativedelta(options.date):
                print '\n[!] Date must be greater then today\n'
                return

        vt.rescan(options.value, options.date, options.period, options.repeat,
                  options.notify_url, options.notify_changes_only, options.delete)

    elif options.domain or options.ip:

        if options.value[0].startswith('http'):
            options.value[0] = urlparse(options.value[0]).netloc

        if match('\w{1,3}\.\w{1,3}\.\w{1,3}\.\w{1,3}', options.value[0]):

            #paranoic check :)
            try:
                valid=len(filter(lambda(item):0<=int(item)<=255, options.value[0].strip().split("."))) == 4
            except ValueError:
                valid = False

            if valid:
                vt.getIP(options.value, options.dump, options.detected_urls, options.detected_downloaded_samples, options.undetected_downloaded_samples,
                        options.detected_communicated, options.undetected_communicated, options.asn, options.detected_referrer_samples, options.undetected_referrer_samples, options.country, options.passive_dns)

            else:
                vt.getDomain(options.value[0], options.dump, options.trendmicro, options.detected_urls, options.detected_downloaded_samples ,options.undetected_downloaded_samples, options.alexa_domain_info,
                            options.wot_domain_info, options.websense_threatseeker, options.bitdefender, options.webutation_domain, options.detected_communicated,
                            options.undetected_communicated, options.pcaps, options.walk, options.whois, options.whois_timestamp, options.detected_referrer_samples, options.undetected_referrer_samples, options.passive_dns,
                            options.subdomains, options.domain_siblings, options.categories, options.drweb_cat, options.alexa_cat, options.alexa_rank, options.opera_info)
        else:
                vt.getDomain(options.value[0], options.dump, options.trendmicro, options.detected_urls, options.detected_downloaded_samples, options.undetected_downloaded_samples, options.alexa_domain_info,
                            options.wot_domain_info, options.websense_threatseeker, options.bitdefender, options.webutation_domain, options.detected_communicated,
                            options.undetected_communicated, options.pcaps, options.walk, options.whois, options.whois_timestamp, options.detected_referrer_samples, options.undetected_referrer_samples, options.passive_dns,
                            options.subdomains, options.domain_siblings, options.categories, options.drweb_cat, options.alexa_cat, options.alexa_rank, options.opera_info)

    elif options.report_all_info:
        vt.getReport(options.value, '1', options.verbose, options.dump, api_type)

    elif options.search and not options.domain and not options.ip and not options.url_scan and not options.url_report:
        vt.getReport(
            options.value, '0', options.verbose, options.dump, options.csv, api_type)

    elif options.download:
        vt.download(options.value[0], intelligence, options.download)

    #elif options.pcap:
    #    vt.download(options.value[0], intelligence, 'pcap')

    elif options.behaviour:
        vt.behaviour(options.value[
                     0], options.dump, options.behavior_network, options.behavior_process, options.behavior_summary)

    elif options.distribution_files:
        vt.distribution(options.value, 'file', options.before,
                        options.after, options.reports, options.limit, False, options.dump)

    elif options.distribution_urls:
        vt.distribution(options.value, 'url', options.before, options.after,
                        options.reports, options.limit, options.allinfo, options.dump)

    elif options.massive_download:
        print """
                Check download help, if need more advanced download, give me a touch or check this:
                https://www.virustotal.com/es/documentation/scripts/vtfiles.py
              """
        return

    elif options.add_comment and len(options.value) == 2:
        vt.comment(options.value[0], 'add', options.dump, options.value[1])

    elif options.get_comments:
        vt.comment(options.value[0], 'get', options.dump, options.date)

    elif options.clusters:
        vt.clusters(options.value, options.dump)

    # elif options.search_by_cluster_id:
    #    vt.clusters(options.value, options.dump, True)

    else:
        sys.exit(opt.print_help())

if __name__ == '__main__':
    main()

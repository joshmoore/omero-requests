#!/usr/bin/env python
import logging
import argparse
import time
import sys

from fileinput import input
from orequests import OmeroRequests

PAGE = 200

COUNT_URL = "/mapr/api/{type}/count/?value={value}&page=1&group=3&_=1499775784739"
VALUE_URL = "/mapr/api/{type}/?value={value}&case_sensitive=false&orphaned=true&experimenter_id=-1&page=1&group=3&_=1499775784739"
COUNTER_URL = "/mapr/api/{type}/?value={value}&counter={counter}&id={value}&page=0&group=3&_=1499776040498"
SCREEN_URL = "/mapr/api/{type}/plates/?value={value}&counter={counter}&id={sid}&page=1&group=3&_=1499776472447"
PLATE_URL = "/mapr/api/{type}/images/?node=plate&value={value}&id={pid}&page=1&group=3&_=1499776472441"


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("type", action="store", type=str)
    parser.add_argument("-H", "--domain", action="store", type=str)
    parser.add_argument("-U", "--username", action="store", type=str)
    parser.add_argument("-P", "--password", action="store", type=str)
    parser.add_argument("-T", "--token", action="store", type=str)

    args = parser.parse_args(sys.argv[1:])
    domain = args.domain
    try:
        username = args.username
        password = args.password
    except:
        username = None
        password = None

    try:
        token = args.token
    except:
        token = None

    LOG_FILENAME = 'cache-annotation.log'
    logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


    print "Start"
    def do_call(oreq, url, extra=None):
        params = {'type': args.type, 'value': value}
        if extra is not None:
            params.update(extra)
        _url = oreq.prepare_url(url, params)
        print "-" * 20
        print _url
        grsps = oreq.async_requests(urls=[_url])
        for grsp in grsps:
            try:
                return grsp.json()
            except:
                return {"No json": str(grsp)}

    def batch(iterable, n=1):
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx:min(ndx + n, l)]

    with OmeroRequests() as oreq:
        oreq.configure(domain)
        oreq.connect(token=token, username=username, password=password)

        for line in input(["-"]):
            value = line.strip()
            rv = do_call(oreq, COUNT_URL)
            rv = do_call(oreq, VALUE_URL)
            cnt = rv["maps"][0]["extra"]["counter"]
            # print rv
            rv = do_call(oreq, COUNTER_URL, {"counter": cnt})
            # print rv
            for screen in rv["screens"]:
                rv2 = do_call(oreq, SCREEN_URL, {"counter": cnt, "sid": screen["id"]})
                print screen["name"]
                # print rv2

                # for plates in batch(rv2["plates"], 5):
                if True:
                    urls = []
                    for plate in rv2["plates"]:
                        print "\t", plate["name"]
                        urls.append(oreq.prepare_url(PLATE_URL, {'type': args.type, 'value': value,
                                                                 'counter': cnt, "pid": plate["id"]}))
                    start = time.time()
                    grsps = oreq.async_requests(urls=urls)
                    for grsp in grsps:
                        print grsp,
                        grsp.close()
                    stop = time.time()
                    print "\n", (stop-start)

#!/usr/bin/env python
import logging
import argparse
import time
import sys

from fileinput import input
from orequests import OmeroRequests

PAGE = 200

## Comments == Phenotypes
#            /mapr/api/{type}/count/?page=1&group=3
COUNT_URL = "/mapr/api/{type}/count/?value={value}&page=1&group=3"


ALL_URL = "/mapr/api/{type}/?case_sensitive=false&orphaned=true&experimenter_id=-1&page=1&group=3"

#           /mapr/api/{type}/?case_sensitive=false&orphaned=true&experimenter_id=-1&page=1&group=3
VALUE_URL = "/mapr/api/{type}/?value={value}&case_sensitive=false&orphaned=true&experimenter_id=-1&page=1&group=3"

#              /mapr/api/{type}/?counter=39471&id=CMPO_0000393&page=0&group=3
COUNTER_URL = "/mapr/api/{type}/?value={value}&counter={counter}&id={value}&page=0&group=3"

#             /mapr/api/{type}/plates/?counter=39375&value=CMPO_0000393&id=51&page=1&group=3
SCREEN_URL = "/mapr/api/{type}/plates/?value={value}&counter={counter}&id={sid}&page=1&group=3"

#            /mapr/api/{type}/images/?node=plate&value=CMPO_0000393&id=101&page=1&group=3
PLATE_URL = "/mapr/api/{type}/images/?node=plate&value={value}&id={pid}&page=1&group=3"

PROJECT_URL = "/mapr/api/{type}/datasets/?value={value}&case_sensitive=false&counter={counter}&id={pid}&page=1&group=3"

DATASET_URL = "/mapr/api/{type}/images/?value={value}&case_sensitive=false&node=dataset&id={did}&page=1&sizeXYZ=true&date=true&group=3"




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

    LOG_FILENAME = 'cache-hierarchy.log'
    logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


    print "Start"
    def do_call(oreq, url, extra=None):
        params = {'type': args.type}
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
        rv = do_call(oreq, ALL_URL)
        for map in rv["maps"]:
            id = map["id"]
            name = map["name"]
            cnt = map["extra"]["counter"]
            rv2 = do_call(oreq, COUNTER_URL, extra={"counter": cnt, "value": id})
            for project in rv2["projects"]:
                project_id = project["id"]
                project_name = project["name"]
                project_children = project["childCount"]
                rv3 = do_call(oreq, PROJECT_URL,
                              {"counter": cnt, "pid": project_id, "value": id})
                for dataset in rv3["datasets"]:
                    dataset_id = dataset["id"]
                    dataset_name = dataset["name"]
                    dataset_children = dataset["childCount"]
                    rv4 = do_call(oreq, DATASET_URL,
                                  {"did": dataset_id, "value": id})
                    for image in rv4["images"]:
                        image_id = image["id"]
                        image_name = image["name"]
                        image_fs = image["filesetId"]
                        print "IMAGE:%s\t%s" % (id, image_id)
            for screen in rv2["screens"]:
                screen_id = screen["id"]
                screen_name = screen["name"]
                screen_cnt = screen["extra"]["counter"]
                screen_children = screen["childCount"]
                rv3 = do_call(oreq, SCREEN_URL,
                              {"counter": cnt, "sid": screen_id, "value": id})
                for plate in rv3["plates"]:
                    plate_id = plate["id"]
                    plate_name = plate["name"]
                    plate_children = plate["childCount"]
                    rv4 = do_call(oreq, PLATE_URL,
                                  {"pid": plate_id, "value": id})
                    for image in rv4["images"]:
                        image_id = image["id"]
                        image_name = image["name"]
                        image_fs = image["filesetId"]
                        print "IMAGE:%s\t%s" % (id, image_id)

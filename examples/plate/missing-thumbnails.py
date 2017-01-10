import logging
import argparse
import sys

from orequests import OmeroRequests


PAGE = 200

WELLS_IMAGES_URL = "/webgateway/plate/{plate_id}/{run_id}/"


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--plate", action="store", type=long)
    parser.add_argument("-f", "--fields", action="store", type=int, default=1)

    parser.add_argument("-H", "--domain", action="store", type=str)
    parser.add_argument("-U", "--username", action="store", type=str)
    parser.add_argument("-P", "--password", action="store", type=str)
    parser.add_argument("-T", "--token", action="store", type=str)

    args = parser.parse_args(sys.argv[1:])
    domain = args.domain
    plate_id = args.plate
    child_count = args.fields
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

    LOG_FILENAME = 'thumbnails-plate-%s.log' % plate_id
    logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

    with OmeroRequests() as oreq:
        oreq.configure(domain)
        oreq.connect(token=token, username=username, password=password)

        plateurl = []
        for run_id in xrange(0, child_count):
            _u = oreq.prepare_url(WELLS_IMAGES_URL,
                                  {'plate_id': plate_id, 'run_id': run_id})
            plateurl.append(_u)
        grsps2 = oreq.async_requests(urls=plateurl)

        gridurls = []
        for grsp2 in grsps2:
            for row in grsp2.json()['grid']:
                for cell in row:
                    if cell is not None:
                        thumb_url = cell['thumb_url']
                        _u = oreq.prepare_url(thumb_url, no_prefix=True)
                        gridurls.append(_u)
        oreq.async_requests(urls=gridurls)

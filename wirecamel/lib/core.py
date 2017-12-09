# coding=utf-8
import json
import re
import urllib
import gzip
import iso8601
import pprint

from StringIO import StringIO
from dateutil import tz
from tabulate import tabulate


# Parse log file
def parse_logfile(log_file):
    headers_request = []
    headers_respons = []

    existing_methods = ['POST', 'GET', 'PUT', 'DELETE', 'HEAD']

    re_headers = re.compile(r'([a-zA-Z\-]+):\s+(.*)\r\n')
    re_request = re.compile(r'(.*) (.*) HTTP.*\r\n')

    # Temporary parts that will be added to headers (response and request)
    tmp_parts = {
        'req': {},
        'res': {}
    }

    # Booleans, used to know in which part we are
    parts = {
        'body': False,
        'body_chunked': False,
        'request': True,
        'response': False,
    }

    # Temporary body
    body_tmp = ""

    # Data chunk booleans and length
    data_chunk = {
        'chunked_data': False,
        'chunk': False,
        'chunk_length': 0
    }

    # Parsing each line
    for line in log_file.readlines():
        # Body not chunked parsing
        if parts['body']:
            # Setting body length to 0
            actual_bodylength = 0

            # Content length from request headers
            if parts['request'] and 'Content-Length' in headers_request[-1]:
                actual_bodylength = int(headers_request[-1]['Content-Length'])

            # Content length from response headers
            if parts['response'] and 'Content-Length' in headers_respons[-1]:
                actual_bodylength = int(headers_respons[-1]['Content-Length'])

            # Filling body
            if actual_bodylength != 0:
                if len(line) < (actual_bodylength - len(body_tmp)):
                    body_tmp += line
                    continue
                else:
                    # Adding the line to temp body and setting body part to false
                    body_tmp += line[:(actual_bodylength - len(body_tmp))]
                    parts['body'] = False

                    # If requests parsing
                    if parts['request']:
                        # Setting parts
                        parts['request'] = False
                        parts['response'] = True

                        # Checking if data is compressed or not
                        headers_request[-1]['body'] = decode_data(body_tmp, headers_request[-1])

                        # Emptying body tmp and continuing
                        body_tmp = ""
                        continue

                    if parts['response']:
                        # Setting parts
                        parts['request'] = True
                        parts['response'] = False

                        # Checking if gzip compressed data
                        headers_respons[-1]['body'] = decode_data(body_tmp, headers_respons[-1])

                        # Retrieving headers
                        method_str = line[(actual_bodylength - len(body_tmp)):]
                        m_method1 = re.match(re_request, method_str)

                        # Filling with extracted informations
                        if m_method1:
                            method = ''
                            for existing_method in existing_methods:
                                index = m_method1.group(1).find(existing_method)
                                if -1 != index:
                                    method = m_method1.group(1)[index:]
                                    break

                            headers_request.append({})
                            headers_request[len(headers_request) - 1]['Method'] = method
                            headers_request[len(headers_request) - 1]['URI'] = m_method1.group(2)

                        # Emptying body tmp
                        body_tmp = ""
                        continue

            # Otherwise, setting "Empty" one
            else:
                # Setting body part
                parts['body'] = False

                # Setting response and request parts
                if parts['response']:
                    parts['response'] = False
                    parts['request'] = True

                    headers_respons[-1]['body'] = 'Empty'
                else:
                    parts['response'] = True
                    parts['request'] = False

                    headers_request[-1]['body'] = 'Empty'

                continue

        # Body chunked parsing
        if parts['body_chunked']:
            if data_chunk['chunk']:
                # If line's length is lower than chunk length minus length of tmp body, adding line and continue
                if len(line.replace('\r\n', '')) < (data_chunk['chunk_length'] - len(body_tmp)):
                    body_tmp += line
                    continue

                # If not, adding the rest and setting chunk to false
                try:
                    body_tmp += uncompress_gzip(line[:(data_chunk['chunk_length'] - len(body_tmp))])
                except IOError:
                    body_tmp += line[:(data_chunk['chunk_length'] - len(body_tmp))]

                data_chunk['chunk'] = False
            else:
                if line != '\r\n':
                    try:
                        data_chunk['chunk_length'] = int(line.replace('\r\n', ''), 16)
                    except ValueError:
                        continue

                    if data_chunk['chunk_length'] != 0:
                        data_chunk['chunk'] = True
                        continue

        # Request headers parsing
        if parts['request']:
            # Regex objects
            m_method = re.match(re_request, line)
            m_header = re.match(re_headers, line)

            # Checking for method
            if m_method:
                tmp_parts['req']['Method'] = m_method.group(1)
                tmp_parts['req']['URI'] = urllib.unquote(m_method.group(2)).decode("utf-8")

            # Checking for header
            if m_header:
                tmp_parts['req'][m_header.group(1)] = m_header.group(2)

                # Checking if data is urlencoded
                if "Content-Type" == m_header.group(1) and "application/x-www-form-urlencoded" == m_header.group(2):
                    data_url_encoded = True

        # Response headers parsing
        if parts['response']:
            m = re.match(re_headers, line)
            if m:
                tmp_parts['res'][m.group(1)] = m.group(2)

                # Checking if data is chunked
                if "Transfer-Encoding" == m.group(1) and "chunked" == m.group(2).strip():
                    data_chunk['chunked_data'] = True

        # Break parts and data is not chunked
        if line == '\r\n' and not data_chunk['chunked_data']:
            # Setting body to true
            parts['body'] = True

            # Adding temporary request headers to main headers
            if parts['request']:
                push_tmp_part(tmp_parts['req'], headers_request)
                tmp_parts['req'] = {}

            # Adding temporary response headers to main headers
            if parts['response']:
                push_tmp_part(tmp_parts['res'], headers_respons)
                tmp_parts['res'] = {}

                # If content length is 0, no need to fill the body
                if "Content-Length" not in headers_respons[-1] or headers_respons[-1]['Content-Length'] == '0':
                    parts['body'] = False
                    parts['response'] = False
                    parts['request'] = True

                    headers_respons[-1]['body'] = "Empty"

            continue

        # If parts break and data is chunked
        if line == '\r\n' and data_chunk['chunked_data']:
            if parts['response'] and len(tmp_parts['res']) != 0:
                headers_respons.append(tmp_parts['res'])
                tmp_parts['res'] = {}
            if parts['request'] and len(tmp_parts['req']) != 0:
                headers_request.append(tmp_parts['req'])
                tmp_parts['req'] = {}

            if parts['body_chunked']:
                data_chunk['chunked_data'] = False
                if parts['response']:
                    parts['response'] = False
                    parts['request'] = True

                    try:
                        headers_respons[-1]['body'] = uncompress_gzip(body_tmp)
                    except IOError:
                        headers_respons[-1]['body'] = body_tmp

                elif parts['request']:
                    parts['request'] = False
                    parts['response'] = True

                    headers_request[-1]['body'] = body_tmp

                body_tmp = ""
                parts['body_chunked'] = False
            else:
                body_tmp = ""
                parts['body_chunked'] = True

    return {
        'requests': headers_request,
        'responses': headers_respons
    }


# Decompress data if needed
def decode_data(data, headers):
    if 'Content-Encoding' in headers:
        if 'gzip' == headers['Content-Encoding']:
            compressed_stream = StringIO(data)
            gzipper = gzip.GzipFile(fileobj=compressed_stream)
            to_return = gzipper.read()
        elif 'deflated' == headers['Content-Encoding']:
            # TODO: Deflated
            to_return = data
        else:
            to_return = data
    else:
        to_return = data

    # Checking if url encoded
    if "Content-Type" in headers and "application/x-www-form-urlencoded" == headers['Content-Type']:
        to_return = urllib.unquote(to_return).decode("utf-8")
        to_return = pretty_urlencoded(to_return)

    return to_return


# Decompress gzip data
def uncompress_gzip(data):
    compressed_stream = StringIO(data)
    gzipper = gzip.GzipFile(fileobj=compressed_stream)
    return gzipper.read()


# Try to prettify
def pretty_urlencoded(data_urlencoded):
    return data_urlencoded.replace('&', "\n").replace('=', " = ")


# Push tmp part to corresponding header
def push_tmp_part(tmp_data, headers):
    if len(headers) == 0:
        headers.append(tmp_data)
    else:
        if len(headers[-1]) != 2:
            headers.append(tmp_data)
        else:
            for key in tmp_data.keys():
                headers[-1][key] = tmp_data[key]


# Parse log filename and return informations
def parse_logfilename(filename):
    # Regex expression
    m = re.match(r'(.*)-(.*),(.*)-(.*),(.*)\.log', filename)

    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('Europe/Paris')

    # Datetime
    dateobject = iso8601.parse_date(m.group(1))

    # Telling that it's in UTC
    dateobject = dateobject.replace(tzinfo=from_zone)
    date_paris = dateobject.astimezone(to_zone)

    datefile = "{}:{}:{} {}/{}/{}".format(date_paris.hour, date_paris.minute, date_paris.second,
                                          date_paris.year, date_paris.month, date_paris.day)

    return {
        'date': datefile,
        'source_ip': m.group(2),
        'source_port': m.group(3),
        'destination_ip': m.group(4),
        'destination_port': m.group(5)
    }


# Render a printable version of headers generated
def printable_headers(headers):
    printable = ""
    table_print = []

    # If asking for responses or requests
    if 'requests' not in headers:
        for header_array in headers:
            for header_name in header_array:
                if header_name != 'body':
                    table_print.append([header_name, header_array[header_name]])
                else:
                    body_brut = header_array[header_name]

            printable += "==================================\n"
            printable += "\tHeaders:\n"
            printable += "==================================\n"
            printable += tabulate(table_print, tablefmt="simple")
            printable += "\n==================================\n"
            printable += "\tBody"
            printable += "\n==================================\n"

            try:
                body = json.loads(body_brut.decode("utf-8", "replace"))
                printable += json.dumps(body, sort_keys=True, indent=4)
            except ValueError:
                printable += body_brut.decode("utf-8", "replace")

            printable += "\n"
            table_print = []

    # Otherwise, asking for the stream
    else:
        for count in range(0, len(headers['requests'])):
            # Appending request
            for header in headers['requests'][count]:
                if header != 'body':
                    table_print.append([header, headers['requests'][count][header]])

            printable += "==================================\n"
            printable += "\tRequest\n"
            printable += "==================================\n"
            printable += tabulate(table_print, tablefmt="simple")
            printable += "\n==================================\n"
            printable += "\tBody"
            printable += "\n==================================\n"
            try:
                json_data = json.loads(headers['requests'][count]['body'].decode("utf-8", "replace"))
                printable += json.dumps(json_data, sort_keys=True, indent=4)
            except ValueError:
                printable += headers['requests'][count]['body'].decode("utf-8", "replace")
            except KeyError:
                pprint.pprint(headers['requests'][count])
                exit(1)
            printable += "\n"

            # Appending response
            table_print = []
            for header in headers['responses'][count]:
                if header != 'body':
                    table_print.append([header, headers['responses'][count][header]])

            printable += "\n==================================\n"
            printable += "\tResponse"
            printable += "\n==================================\n"
            printable += tabulate(table_print, tablefmt="simple")
            printable += "\n==================================\n"
            printable += "\tBody"
            printable += "\n==================================\n"
            try:
                json_data = json.loads(headers['responses'][count]['body'].decode("utf-8", "replace"))
                printable += json.dumps(json_data, sort_keys=True, indent=4)
            except ValueError:
                printable += headers['responses'][count]['body'].decode("utf-8", "replace")
            printable += "\n"

            table_print = []

    return printable

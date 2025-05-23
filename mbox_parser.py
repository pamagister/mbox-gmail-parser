import string

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from email_reply_parser import EmailReplyParser
from email.utils import parsedate_tz, mktime_tz

import ast
import datetime
import mailbox
import ntpath
import os
import quopri
import re
import rules
import sys
import unicodecsv as csv

# converts seconds since epoch to mm/dd/yyyy string
def get_date(date_header, date_format):
    if date_header is None:
        return None
    try:
        time_tuple = parsedate_tz(date_header)
        utc_seconds_since_epoch = mktime_tz(time_tuple)
        datetime_obj = datetime.datetime.fromtimestamp(utc_seconds_since_epoch)
        return datetime_obj.strftime(date_format)
    except Exception:
        return None

# clean content
def clean_content(content):
    content = quopri.decodestring(content)
    try:
        soup = BeautifulSoup(content, "html.parser", from_encoding="iso-8859-1")
    except Exception:
        return ''
    return ''.join(soup.find_all(string=True))

# get contents of email
def get_content(email):
    parts = []

    for part in email.walk():
        if part.get_content_maintype() == 'multipart':
            continue

        content = part.get_payload(decode=True)

        if content is None:
            part_contents = ""
        else:
            part_contents = EmailReplyParser.parse_reply(clean_content(content))

        parts.append(part_contents)

    return parts[0] if parts else ""

# get all emails in field
def get_emails_clean(field):
    matches = re.findall(r'\<?([a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,5})\>?', str(field))
    if matches:
        emails_cleaned = [match.lower() for match in matches]
        unique_emails = list(set(emails_cleaned))
        return sorted(unique_emails, key=str.lower)
    else:
        return []

# entry point
if __name__ == '__main__':
    argv = sys.argv

    if len(argv) != 2:
        print('usage: mbox_parser.py [path_to_mbox]')
        mbox_file = "example.mbox"
    else:
        mbox_file = argv[1]


    load_dotenv(verbose=True)
    file_name = ntpath.basename(mbox_file).lower()
    export_file_name = mbox_file + ".csv"
    export_file = open(export_file_name, "wb")

    # Load owner mapping if exists
    owners = []
    if os.path.exists(".owners"):
        with open('.owners', 'r') as ownerlist:
            owner_dict = ast.literal_eval(ownerlist.read())
        for owners_array_key in owner_dict:
            if owners_array_key in file_name:
                owners.extend(owner_dict[owners_array_key])

    # Load domain blacklist if exists
    blacklist_domains = []
    if os.path.exists(".blacklist"):
        with open('.blacklist', 'r') as blacklist:
            blacklist_domains = [domain.rstrip() for domain in blacklist.readlines()]

    writer = csv.writer(export_file, delimiter="\n", quotechar="\n")

    # --- COLLECT AND SORT EMAILS ---
    emails_with_dates = []

    for email in mailbox.mbox(mbox_file):
        try:
            time_tuple = parsedate_tz(email["date"])
            utc_seconds_since_epoch = mktime_tz(time_tuple)
        except Exception:
            utc_seconds_since_epoch = 0  # fallback if date is missing or unparsable
        emails_with_dates.append((utc_seconds_since_epoch, email))

    # Sort emails by timestamp
    emails_with_dates.sort(key=lambda tup: tup[0])

    # --- PROCESS SORTED EMAILS ---
    row_written = 0

    for _, email in emails_with_dates:
        date = get_date(email["date"], os.getenv("DATE_FORMAT"))
        sent_from = get_emails_clean(email["from"])
        sent_to = get_emails_clean(email["to"])
        cc = get_emails_clean(email["cc"])
        subject = re.sub('[\n\t\r]', ' -- ', str(email["subject"]))
        contents = get_content(email)

        row = rules.apply_rules(date, sent_from, sent_to, cc, subject, contents, owners, blacklist_domains)
        writer.writerow(row)
        row_written += 1

    report = (
        f"generated {export_file_name} for {row_written} messages "
        f"({rules.cant_convert_count} could not convert; {rules.blacklist_count} blacklisted)"
    )
    print(report)
    export_file.close()

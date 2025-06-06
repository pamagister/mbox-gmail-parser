import ast
import datetime
import mailbox
import ntpath
import os
import quopri
import re
import sys
from email.header import decode_header
from email.utils import parsedate_tz, mktime_tz
from math import inf

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from email_reply_parser import EmailReplyParser


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
def clean_content(content_bytes):
    # decode quoted-printable
    content_bytes = quopri.decodestring(content_bytes)

    # Try UTF-8 first, fallback to ISO-8859-1
    try:
        content_str = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content_str = content_bytes.decode("iso-8859-1", errors="replace")

    # HTML-Tags entfernen
    try:
        soup = BeautifulSoup(content_str, "html.parser")
    except Exception as e:
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
    matches = re.findall(
        r'\<?([a-zA-Z0-9_\-\.]+@[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,5})\>?', str(field)
    )
    if matches:
        emails_cleaned = [match.lower() for match in matches]
        unique_emails = list(set(emails_cleaned))
        return sorted(unique_emails, key=str.lower)
    else:
        return []


def decode_mime_header(value):
    if not value:
        return ''
    decoded_fragments = decode_header(value)
    result = ''
    for text, encoding in decoded_fragments:
        if isinstance(text, bytes):
            try:
                result += text.decode(encoding or 'utf-8', errors='replace')
            except Exception:
                result += text.decode('utf-8', errors='replace')
        else:
            result += text
    return result


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
    export_file_name = mbox_file + ".txt"

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
    max_days = -1
    if max_days <= 0:
        max_days = inf
    row_written = 0
    file_index = 1
    last_date = None
    f = None

    for _, email in emails_with_dates:
        # Compare with last file
        date_str = get_date(email["date"], os.getenv("DATE_FORMAT"))
        email_date = datetime.datetime.strptime(date_str, os.getenv("DATE_FORMAT"))

        if last_date is None or (email_date - last_date).days > max_days:
            if f:
                f.close()
            filename = f"{export_file_name}_{file_index:03}.txt"
            f = open(filename, 'wb')
            print(f"Write new wile: {filename}")
            file_index += 1
            last_date = email_date

        sent_from = "From: {}".format(get_emails_clean(email["from"]))
        date = "Date: {}".format(date_str)
        sent_to = "To: {}".format(get_emails_clean(email["to"]))
        cc = "Subject: {}".format(get_emails_clean(email["cc"]))
        subject = "Subject: {}".format(decode_mime_header((email["subject"])))
        contents = get_content(email)

        mailContent = [
            sent_from,
            sent_to,
            date,
            subject,
            '\n' + contents + '\n-----\n\n',
        ]
        f.write("\n".join(mailContent).encode("utf-8"))
        row_written += 1

    report = (
        f"generated {export_file_name} for {row_written} messages "
        f"({rules.cant_convert_count} could not convert; {rules.blacklist_count} blacklisted)"
    )
    print(report)

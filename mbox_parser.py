import argparse
import datetime
import mailbox
import os
import quopri
import re
from email.header import decode_header
from email.utils import parsedate_tz, mktime_tz

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from email_reply_parser import EmailReplyParser
from math import inf


def parse_date(date_header, date_format):
    if date_header is None:
        return None
    try:
        time_tuple = parsedate_tz(date_header)
        if time_tuple is None:
            return None
        timestamp = mktime_tz(time_tuple)
        return datetime.datetime.fromtimestamp(timestamp).strftime(date_format)
    except Exception:
        return None


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


def clean_content(content_bytes):
    content_bytes = quopri.decodestring(content_bytes)
    try:
        content_str = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content_str = content_bytes.decode("iso-8859-1", errors="replace")
    try:
        soup = BeautifulSoup(content_str, "html.parser")
        return ''.join(soup.find_all(string=True))
    except Exception:
        return ''


def extract_content(email):
    for part in email.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        content = part.get_payload(decode=True)
        if content:
            return EmailReplyParser.parse_reply(clean_content(content))
    return ''


def extract_emails(field):
    matches = re.findall(
        r'\<?([a-zA-Z0-9_\-.]+@[a-zA-Z0-9_\-.]+\.[a-zA-Z]{2,5})\>?', str(field)
    )
    unique_emails = sorted(set(match.lower() for match in matches))
    return unique_emails


def build_txt_output(email, options, date_format):
    lines = []

    if options["from"]:
        lines.append(
            "From: {}".format(', '.join(extract_emails(email.get("from", ""))))
        )
    if options["to"]:
        lines.append("To: {}".format(', '.join(extract_emails(email.get("to", "")))))
    if options["date"]:
        date_str = parse_date(email.get("date"), date_format)
        lines.append("Date: {}".format(date_str or "Unknown"))
    if options["subject"]:
        lines.append("Subject: {}".format(decode_mime_header(email.get("subject", ""))))

    content = extract_content(email)
    lines.append('\n' + content + '\n-----\n\n')
    return "\n".join(lines)


def build_csv_output(email, email_date_str, include_options):
    fields = []
    if include_options["from"]:
        fields.append('"{}"'.format(', '.join(extract_emails(email.get("from", "")))))
    if include_options["to"]:
        fields.append('"{}"'.format(', '.join(extract_emails(email.get("to", "")))))
    if include_options["date"]:
        fields.append('"{}"'.format(email_date_str or ""))
    if include_options["subject"]:
        fields.append(
            '"{}"'.format(
                decode_mime_header(email.get("subject", "")).replace('"', '""')
            )
        )
    content = extract_content(email).replace('"', '""').replace('\n', ' ').strip()
    fields.append(f'"{content}"')
    return fields


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Parse mbox file and export to text or CSV."
    )

    parser.add_argument(
        "--from",
        dest="from_",
        default="ON",
        choices=["ON", "OFF"],
        help="Include 'From' field in output (default: ON)",
    )
    parser.add_argument(
        "--to",
        default="ON",
        choices=["ON", "OFF"],
        help="Include 'To' field in output (default: ON)",
    )
    parser.add_argument(
        "--date",
        default="ON",
        choices=["ON", "OFF"],
        help="Include 'Date' field in output (default: ON)",
    )
    parser.add_argument(
        "--subject",
        default="ON",
        choices=["ON", "OFF"],
        help="Include 'Subject' field in output (default: ON)",
    )
    parser.add_argument(
        "--format",
        default="txt",
        choices=["txt", "csv"],
        help="Output format: txt or csv (default: txt)",
    )
    parser.add_argument(
        "--max_days",
        type=int,
        default=-1,
        help="Max number of days per output file (default: unlimited)",
    )
    parser.add_argument("mbox_file", help="Path to mbox file")

    return parser.parse_args()


def main():
    args = parse_arguments()
    load_dotenv(verbose=True)

    date_format = os.getenv("DATE_FORMAT", "%Y-%m-%d")
    mbox_path = args.mbox_file
    base_output_name = os.path.splitext(os.path.basename(mbox_path))[0]
    file_extension = args.format
    output_template = f"{base_output_name}_{{:03d}}.{file_extension}"

    include_options = {
        "from": args.from_ == "ON",
        "to": args.to == "ON",
        "date": args.date == "ON",
        "subject": args.subject == "ON",
    }

    max_days = args.max_days if args.max_days > 0 else inf

    emails = []
    for msg in mailbox.mbox(mbox_path):
        try:
            timestamp = mktime_tz(parsedate_tz(msg.get("date", ""))) or 0
        except Exception:
            timestamp = 0
        emails.append((timestamp, msg))

    emails.sort(key=lambda tup: tup[0])

    last_date = None
    file_index = 1
    row_written = 0
    f = None

    for timestamp, email in emails:
        email_date_str = parse_date(email.get("date"), date_format)
        if email_date_str:
            email_date = datetime.datetime.strptime(email_date_str, date_format)
        else:
            email_date = datetime.datetime.min

        if last_date is None or (email_date - last_date).days > max_days:
            if f:
                f.close()
            filename = output_template.format(file_index)
            f = open(
                filename,
                "w",
                encoding="utf-8",
                newline="" if file_extension == "csv" else None,
            )
            print(f"Writing new file: {filename}")
            file_index += 1
            last_date = email_date

            if file_extension == "csv":
                header = []
                if include_options["from"]:
                    header.append("From")
                if include_options["to"]:
                    header.append("To")
                if include_options["date"]:
                    header.append("Date")
                if include_options["subject"]:
                    header.append("Subject")
                header.append("Content")
                f.write(",".join(header) + "\n")

        if file_extension == "txt":
            output = build_txt_output(email, include_options, date_format)
            f.write(output)
        elif file_extension == "csv":
            fields = build_csv_output(email, email_date_str, include_options)
            f.write(",".join(fields) + "\n")

        row_written += 1

    if f:
        f.close()

    print(f"Generated output for {row_written} messages into {file_index - 1} file(s).")


if __name__ == "__main__":
    main()

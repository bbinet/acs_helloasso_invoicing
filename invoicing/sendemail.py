#!/usr/bin/env python3
"""Send an email with an attachment using smtplib.

Drop-in replacement for the sendemail Perl tool.
Usage: sendemail.py -f FROM -t TO -u SUBJECT -m MESSAGE -a ATTACHMENT -s SMTP:PORT -xu USER -xp PASS -l LOGFILE

Error handling contract (matches original sendemail behavior):
- On success: creates logfile, exits 0
- On failure: creates logfile with error details, exits 1
  (Makefile then renames logfile to error_<logfile>)
"""
import argparse
import email.message
import mimetypes
import os
import smtplib
import sys
import traceback
from datetime import datetime


def send_email(*, from_addr, to_addr, subject, message, attachment, smtp_server, username, password, logfile):
    """Send an email with a PDF attachment via SMTP with STARTTLS.

    Always writes the logfile:
    - On success: log contains send confirmation
    - On failure: log contains error details, then raises the exception
    This ensures the Makefile's `mv $@ error_$@` always has a file to rename.
    """
    # Parse SMTP host:port
    if ":" in smtp_server:
        host, port = smtp_server.rsplit(":", 1)
        port = int(port)
    else:
        host = smtp_server
        port = 587

    # Build email — convert literal \n to real newlines
    msg = email.message.EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(message.replace('\\n', '\n'))

    # Attach PDF
    if attachment and os.path.isfile(attachment):
        mime_type, _ = mimetypes.guess_type(attachment)
        if mime_type is None:
            mime_type = "application/octet-stream"
        maintype, subtype = mime_type.split("/", 1)
        with open(attachment, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(attachment),
            )

    # Send and log
    try:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)

        # Success: write log
        with open(logfile, "w") as f:
            f.write(f"{datetime.now().isoformat()} sent successfully to {to_addr}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Attachment: {attachment}\n")
            f.write(f"SMTP: {smtp_server}\n")

    except Exception as e:
        # Failure: write error log so Makefile can rename it to error_<logfile>
        try:
            with open(logfile, "w") as f:
                f.write(f"{datetime.now().isoformat()} ERROR sending to {to_addr}\n")
                f.write(f"Error: {e}\n")
                f.write(f"Traceback:\n{traceback.format_exc()}\n")
        except OSError:
            pass  # Can't write log — nothing we can do
        raise


def main():
    parser = argparse.ArgumentParser(description="Send email with attachment (sendemail replacement)")
    parser.add_argument("-f", dest="from_addr", required=True, help="From address")
    parser.add_argument("-t", dest="to_addr", required=True, help="To address")
    parser.add_argument("-u", dest="subject", required=True, help="Subject")
    parser.add_argument("-m", dest="message", required=True, help="Message body")
    parser.add_argument("-a", dest="attachment", help="Attachment file path")
    parser.add_argument("-s", dest="smtp", required=True, help="SMTP server (host:port)")
    parser.add_argument("-xu", dest="username", required=True, help="SMTP username")
    parser.add_argument("-xp", dest="password", required=True, help="SMTP password")
    parser.add_argument("-l", dest="logfile", required=True, help="Log file path")
    parser.add_argument("-o", dest="options", action="append", help="Extra options (ignored for compat)")
    args = parser.parse_args()

    try:
        send_email(
            from_addr=args.from_addr,
            to_addr=args.to_addr,
            subject=args.subject,
            message=args.message,
            attachment=args.attachment,
            smtp_server=args.smtp,
            username=args.username,
            password=args.password,
            logfile=args.logfile,
        )
        print(f"Email sent to {args.to_addr}")
    except Exception as e:
        print(f"Error sending email: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

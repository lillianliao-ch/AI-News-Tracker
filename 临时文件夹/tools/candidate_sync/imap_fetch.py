#!/usr/bin/env python3
import argparse
import email
import imaplib
import os
import re
import sys
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from pathlib import Path
from subprocess import CalledProcessError, run

from dotenv import load_dotenv


def decode_str(value: str) -> str:
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def connect_imap(host: str, port: int | None, user: str, password: str) -> imaplib.IMAP4_SSL:
    if port:
        M = imaplib.IMAP4_SSL(host, port)
    else:
        M = imaplib.IMAP4_SSL(host)
    M.login(user, password)
    return M


def search_since_days(M: imaplib.IMAP4_SSL, folder: str, since_days: int | None) -> list[bytes]:
    typ, _ = M.select(folder)
    if typ != 'OK':
        raise RuntimeError(f"Failed to select folder: {folder}")
    if since_days and since_days > 0:
        since_date = (datetime.utcnow() - timedelta(days=since_days)).strftime('%d-%b-%Y')
        criteria = f'(SINCE {since_date})'
    else:
        criteria = 'ALL'
    typ, data = M.search(None, criteria)
    if typ != 'OK':
        return []
    ids = data[0].split() if data and data[0] else []
    return ids


def safe_filename(name: str) -> str:
    name = name.replace('\r', '').replace('\n', '')
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def should_keep_attachment(filename: str, allowed_exts: set[str], filename_regex: re.Pattern | None) -> bool:
    if not filename:
        return False
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    if allowed_exts and ext not in allowed_exts:
        return False
    if filename_regex and not filename_regex.search(filename):
        return False
    return True


def save_attachments(M: imaplib.IMAP4_SSL, msg_ids: list[bytes], download_dir: Path,
                     allowed_exts: set[str], filename_regex: re.Pattern | None) -> list[Path]:
    saved: list[Path] = []
    for mid in msg_ids:
        typ, msg_data = M.fetch(mid, '(RFC822)')
        if typ != 'OK' or not msg_data:
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        for part in msg.walk():
            content_disposition = part.get('Content-Disposition', '')
            if 'attachment' not in content_disposition.lower():
                continue
            filename = part.get_filename()
            if filename:
                filename = decode_str(filename)
                filename = safe_filename(filename)
            if not should_keep_attachment(filename or '', allowed_exts, filename_regex):
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            download_dir.mkdir(parents=True, exist_ok=True)
            out_path = download_dir / filename
            with open(out_path, 'wb') as f:
                f.write(payload)
            saved.append(out_path)
    return saved


def maybe_normalize(paths: list[Path], normalize: bool, mapping: Path | None, schema: Path | None,
                    out_dir: Path | None) -> None:
    if not normalize or not paths:
        return
    if not mapping or not schema or not out_dir:
        print('Skipping normalization: mapping/schema/out_dir not provided')
        return
    script = Path(__file__).with_name('normalize_candidates.py')
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in paths:
        if p.suffix.lower() != '.csv':
            continue
        out_csv = out_dir / f"normalized_{p.stem}.csv"
        out_parquet = out_dir / f"normalized_{p.stem}.parquet"
        cmd = [
            sys.executable, str(script),
            '--input', str(p),
            '--mapping', str(mapping),
            '--schema', str(schema),
            '--out', str(out_csv),
            '--parquet', str(out_parquet),
        ]
        try:
            print('Normalizing', p)
            run(cmd, check=True)
        except CalledProcessError as e:
            print(f"Normalization failed for {p}: {e}")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description='Fetch CSV/XLSX attachments from IMAP and optionally normalize')
    parser.add_argument('--host', default=os.getenv('IMAP_HOST'), help='IMAP host')
    parser.add_argument('--port', type=int, default=int(os.getenv('IMAP_PORT') or 993), help='IMAP SSL port')
    parser.add_argument('--user', default=os.getenv('IMAP_USER'))
    parser.add_argument('--password', default=os.getenv('IMAP_PASS'))
    parser.add_argument('--folder', default=os.getenv('IMAP_FOLDER') or 'INBOX')
    parser.add_argument('--since-days', type=int, default=int(os.getenv('IMAP_SINCE_DAYS') or 7))
    parser.add_argument('--download-dir', default=os.getenv('DOWNLOAD_DIR') or './downloads')
    parser.add_argument('--allowed-ext', default=os.getenv('ALLOWED_EXT') or 'csv,xlsx')
    parser.add_argument('--filename-regex', default=os.getenv('FILENAME_REGEX') or '')

    parser.add_argument('--normalize', action='store_true', help='Run normalization for downloaded CSVs')
    parser.add_argument('--mapping', default=os.getenv('MAPPING_YAML'))
    parser.add_argument('--schema', default=os.getenv('SCHEMA_YAML'))
    parser.add_argument('--out-dir', default=os.getenv('OUT_DIR') or './out')

    args = parser.parse_args()

    if not all([args.host, args.user, args.password]):
        print('IMAP credentials missing. Provide --host/--user/--password or set env vars.')
        sys.exit(2)

    allowed_exts = set(x.strip().lower() for x in args.allowed_ext.split(',') if x.strip())
    filename_regex = re.compile(args.filename_regex) if args.filename_regex else None

    download_dir = Path(args.download_dir)
    out_dir = Path(args.out_dir)

    M = connect_imap(args.host, args.port, args.user, args.password)
    try:
        ids = search_since_days(M, args.folder, args.since_days)
        saved = save_attachments(M, ids, download_dir, allowed_exts, filename_regex)
        print(f"Downloaded {len(saved)} attachment(s) to {download_dir}")
    finally:
        try:
            M.close()
        except Exception:
            pass
        M.logout()

    if args.normalize:
        mapping = Path(args.mapping) if args.mapping else None
        schema = Path(args.schema) if args.schema else None
        maybe_normalize(saved, True, mapping, schema, out_dir)


if __name__ == '__main__':
    main()



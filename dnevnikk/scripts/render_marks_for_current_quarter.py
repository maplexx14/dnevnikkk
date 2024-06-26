#!/usr/bin/env python3
import argparse
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict

import pkg_resources
import  toml

from dnevnikk import Dnevnik2


def get_subject(item, subjects: Dict[str, str]) -> str:
    subject_id = str(item['subject_id'])
    return subjects.get(subject_id, item['subject_name'])


def to_date(text):
    return dt.datetime.strptime(text, '%d.%m.%Y').date()


def main(user_id):


    cookies_path =  Path(f'../cookies/{user_id}.json')
    config_path= Path(f'../app_config.toml')
    base_dir= Path (f'')

    with config_path.open('r', encoding='utf-8') as f1:
        config = toml.load(f1)

    dnevnik = Dnevnik2.make_from_cookies_file(cookies_path)

    data = dnevnik.fetch_marks_for_current_quarter()

    with (base_dir / 'last_res.txt').open('w', encoding='utf-8') as f1:
        print(json.dumps(data, ensure_ascii=False, indent=2), file=f1)

    out_lines = []
    grouped = defaultdict(list)
    for item in sorted(data['data']['items'], key=lambda x: (to_date(x['date']), x['estimate_value_name'])):
        s_name = item['subject_name'] = get_subject(item, config['subjects'])
        mark = item['estimate_value_name']
        if mark.isdigit():
            grouped[s_name].append(int(mark))
        comment = ('# ' + item['estimate_comment']) if item['estimate_comment'] else ''
        out_lines.append((
            to_date(item['date']),
            "{subject_name:25s} {estimate_value_code:5s} {estimate_value_name:9s} {estimate_type_name:20s}".format(
                **item),
            comment
        ))

    if not out_lines:
        exit(1)

    with (base_dir / f'marks.{dt.date.today()}.txt').open('w', encoding='utf-8') as f1:
        for date, mark, comment in sorted(out_lines):
            print(f'{date}  {mark} {comment}', file=f1)

        f1.write('\n\n')
        for s_name in sorted(grouped):
            avg = sum(grouped[s_name]) / len(grouped[s_name])
            s_marks = ' '.join(str(mark) for mark in grouped[s_name])
            print(f'{s_name:25s} : {avg:0.3f}    {s_marks}', file=f1)


from collections import defaultdict
from dnevnikk import Dnevnik2
from pathlib import Path
import datetime as dt
# Функция получения дат
def to_date(text):
    return dt.datetime.strptime(text, '%d.%m.%Y').date()
def showAvg(user_id):
    marks = Dnevnik2.make_from_cookies_file(Path(f'../cookies/{user_id}.json')).fetch_marks_for_current_quarter()

    out_lines = []
    grouped = defaultdict(list)
    for item in marks['data']['items']:
        s_name = item['subject_name']
        mark = item['estimate_value_name']
        if mark.isdigit():
            grouped[s_name].append(int(mark))
        comment = ('# ' + item['estimate_comment']) if item['estimate_comment'] else ''
        out_lines.append((
            to_date(item['date']),
            "{subject_name:25s} {estimate_value_code:5s} {estimate_value_name:9s} {estimate_type_name:20s}".format(**item),
            comment
        ))

    if not out_lines:
        exit(1)

    arr = []

    for s_name in sorted(grouped):
        avg = round(sum(grouped[s_name]) / len(grouped[s_name]), 1)
        arr.append("<strong>" + str(s_name) + "</strong>" + " - " + "<em>" + str(avg) + "</em>")
    result = ''
    for i in arr:
        if i not in result:
            result += i + "\n"
    return result

def showAvgRating(user_id):
    marks = Dnevnik2.make_from_cookies_file(Path(f'../cookies/{user_id}.json')).fetch_marks_for_current_quarter()

    out_lines = []
    grouped = []
    for item in marks['data']['items']:
        mark = item['estimate_value_name']
        if mark.isdigit():
            grouped.append(int(mark))
        comment = ('# ' + item['estimate_comment']) if item['estimate_comment'] else ''
        out_lines.append((
            to_date(item['date']),
            "{subject_name:25s} {estimate_value_code:5s} {estimate_value_name:9s} {estimate_type_name:20s}".format(
                **item),
            comment
        ))

    if not out_lines:
        exit(1)
    IPU = sum(grouped) / len(grouped)
    return IPU

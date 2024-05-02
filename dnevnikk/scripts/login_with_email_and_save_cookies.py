import argparse
import getpass
import sys
from pathlib import Path

import dnevnikk


def login(user_id,email, password):

    cookies_path = Path(f'.../cookies/{user_id}.json')

    dnevnik = dnevnikk.Dnevnik2.make_from_login_by_email(email, password)
    dnevnik.save_cookies(cookies_path)



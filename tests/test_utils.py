
import datetime
from unittest import TestCase

from ekring.utils import parse_date_info, parse_readable_date

class T_parse_readable_date(TestCase):
    def test_1(self):
        res = parse_readable_date("in 1 hour") 
        self.assertTrue(res > datetime.timedelta(hours=0.9))
        self.assertTrue(res < datetime.timedelta(hours=1.1))

    def test_2(self):
        res = parse_readable_date("in 1 day") 
        self.assertTrue(res > datetime.timedelta(hours=23))
        self.assertTrue(res < datetime.timedelta(hours=25))

    def test_3(self):
        res = parse_readable_date("in 1 minute")
        self.assertTrue(res > datetime.timedelta(minutes=0.9))
        self.assertTrue(res < datetime.timedelta(minutes=1.1))

    def test_4(self):
        res = parse_readable_date("in 1 second")
        self.assertTrue(res > datetime.timedelta(seconds=0.9))
        self.assertTrue(res < datetime.timedelta(seconds=1.1))

    def test_5(self):
        res = parse_readable_date("in 1 weeks")
        self.assertTrue(res > datetime.timedelta(days=6))
        self.assertTrue(res < datetime.timedelta(days=8))

    def test_6(self):
        res = parse_readable_date("in 1 month")
        self.assertTrue(res > datetime.timedelta(days=29))
        self.assertTrue(res < datetime.timedelta(days=31))

    def test_7(self):
        res = parse_readable_date("in 1 year")
        self.assertTrue(res > datetime.timedelta(days=364))
        self.assertTrue(res < datetime.timedelta(days=366))

class T_parse_date_info(TestCase):
    def test_1(self):
        res = parse_date_info("in 24 hour") 
        self.assertTrue(res > datetime.datetime.now())
        self.assertTrue(res < datetime.datetime.now() + datetime.timedelta(days=2))

    def test_2(self):
        res = parse_date_info(
            datetime.timedelta(days=1, hours=1, minutes=1, seconds=1)
        )
        self.assertTrue(res >= datetime.datetime.now() + datetime.timedelta(days=1))
        self.assertTrue(res < datetime.datetime.now() + datetime.timedelta(days=2))
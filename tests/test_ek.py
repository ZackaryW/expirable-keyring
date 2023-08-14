
from time import sleep
from unittest import TestCase

from ekring.ek import AlreadyExpiredKey, ExpirableKeyringFactory


class T_EK(TestCase):
    def setUp(self) -> None:
        self.factory = ExpirableKeyringFactory()
        self.factory.purge_all()

    def tearDown(self) -> None:
        self.factory.purge_all()


    def test_1(self):
        self.factory.set_secret(
            "test",
            "test12412415",
            expiration_date="in 3 seconds"
        )

        res = self.factory.get_secret(
            "test",
        )

        self.assertEqual(res, "test12412415")

        sleep(6)

        with self.assertRaises(AlreadyExpiredKey):
            self.factory.get_secret(
                "test",
            )
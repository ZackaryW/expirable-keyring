from unittest import TestCase

from ekring.password import password_decrypt, password_encrypt_with_gen

msg = """
\n\t
\n
rj390fh3890fh23908y1htfn iefn13rhf109fj0893fji1092ejqwokd109u2r-`jfd0c9wm0912jdr1209jd
kodqa;d';}{a;dA:WDW"A:DAFAWPFKLWKFoWKaFopm
^$RR%^&*)(*&^%%$^&*(&^%$E))
"""

class T_password(TestCase):
    def test_password_encrypt(self):
        content, password = password_encrypt_with_gen(msg)

        encoded_content = content.encode()
        decrypted = password_decrypt(encoded_content, password)
        self.assertEqual(decrypted, msg)


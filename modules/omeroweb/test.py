import os

os.environ['MODE'] = 'test'

# noinspection PyUnresolvedReferences
import config
import unittest
import modules.omeroweb as omero_web
from services.Cache import CacheService


class OmeroWebTest(unittest.TestCase):

    def setUp(self):
        CacheService.flush_all()

    def test_get_or_create(self):
        session = omero_web.get_or_create('root', 'omero')

        self.assertIsNotNone(session)
        self.assertIsInstance(session, omero_web.OmeroSession)


if __name__ == '__main__':
    unittest.main()

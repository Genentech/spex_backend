# noinspection PyUnresolvedReferences
import os
# import config
import unittest
import modules.omeroweb as omero_web
from services.Cache import CacheService
os.environ['MODE'] = 'test'


class OmeroWebTest(unittest.TestCase):

    def setUp(self):
        CacheService.flush_all()

    def test_get_or_create(self):
        session = omero_web.create('root', 'omero')

        self.assertIsNotNone(session)
        self.assertIsInstance(session, omero_web.OmeroSession)


if __name__ == '__main__':
    unittest.main()

import unittest
from ..Cache import CacheService


class ClassInstance:
    def __init__(self, value):
        self.value = value


class CacheServiceTestCase(unittest.TestCase):
    def tearDown(self):
        CacheService.delete('test1')
        CacheService.delete('test2')

    def test_set_get(self):
        CacheService.set('test1', 'a')
        value = CacheService.get('test1')
        self.assertIsNotNone(value)
        self.assertEqual(value, 'a')

    def test_set_get_instance(self):
        item = ClassInstance(5)
        CacheService.set('test2', item)
        item = CacheService.get('test2')
        self.assertIsNotNone(item)
        self.assertIsInstance(item, ClassInstance)
        self.assertIsNotNone(item.value)
        self.assertEqual(item.value, 5)


if __name__ == '__main__':
    unittest.main()

import unittest

if __name__ == '__main__':
    from os import getcwd

    this_dir = getcwd()

    suite = unittest.loader.defaultTestLoader.discover(this_dir)

    runner = unittest.TextTestRunner()
    runner.run(suite)

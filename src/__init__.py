"""프로젝트 전체용 코드"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

if __name__ == '__main__':
    from os import getcwd

    this_dir = getcwd()

    import unittest

    suite = unittest.loader.defaultTestLoader.discover(this_dir)

    runner = unittest.TextTestRunner()
    runner.run(suite)

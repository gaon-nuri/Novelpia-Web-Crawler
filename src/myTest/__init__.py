# from src.myTest import test_module
# from src.myTest import test_novel_info


# def load_tests(loader, tests, pattern):
#     from src.myTest.test_module import CntNovelWithPrologue
#     from src.myTest.test_novel_info import CntNovelInStatus, CntNoEpNovel
#
#     test_cases: tuple = (CntNovelWithPrologue, CntNovelInStatus, CntNoEpNovel)
#     suite = unittest.TestSuite()
#
#     for test_class in test_cases:
#         tests = loader.loadTestsFromTestCase(test_class)
#         suite.addTests(tests)
#
#     return suite


# def load_tests(loader, standard_tests, pattern):
#     cur_dir = getcwd()
#     package_tests = loader.discover(start_dir=cur_dir, pattern=pattern)
#     standard_tests.addTests(package_tests)
#
#     return standard_tests

import unittest
from pathlib import Path


class ScaffoldTests(unittest.TestCase):
    def test_package_exists(self):
        self.assertTrue((Path(__file__).resolve().parents[1] / "src" / "nonprofit_business_manager_api" / "__init__.py").is_file())


if __name__ == "__main__":
    unittest.main()

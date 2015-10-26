import os
import shutil
import tempfile
import unittest

import conda_build.config
from conda_build.metadata import MetaData

from obvci.conda_tools.build_directory import BakedDistribution
from obvci.tests.unit.conda.dummy_index import DummyIndex, DummyPackage


class Test_conditional_recipe(unittest.TestCase):
    # Tests cases where a recipe changes based on external
    # conditions, such as the definition of the PYTHON version.
    def setUp(self):
        self.recipe_dir = tempfile.mkdtemp(prefix='tmp_obvci_recipe_')

    def tearDown(self):
        shutil.rmtree(self.recipe_dir)

    def test_py_version_selector(self):
        recipe = """
            package:
                name: recipe_which_depends_on_py_version
                version: 3  # [py3k]
                version: 2  # [not py3k]
            """.replace('\n' + ' ' * 12, '\n').strip()
        with open(os.path.join(self.recipe_dir, 'meta.yaml'), 'w') as fh:
            fh.write(recipe)
        conda_build.config.config.CONDA_PY = 27
        meta = MetaData(self.recipe_dir)
        dist = BakedDistribution(meta, (('python', '27', ), ))
        self.assertEqual(dist.version(), u'2')

        dist = BakedDistribution(meta, (('python', '35', ), ))
        self.assertEqual(dist.version(), u'2')
        # When we trigger re-reading, ensure that the version is correctly
        # reflected.
        dist.parse_again()
        self.assertEqual(dist.version(), u'3')


class Test_baked_version(unittest.TestCase):
    def setUp(self):
        self.index = DummyIndex()
        self.recipe_dir = tempfile.mkdtemp(prefix='tmp_obvci_recipe_')

    def tearDown(self):
        shutil.rmtree(self.recipe_dir)

    def test_py_xx_version(self):
        recipe = """
            package:
                name: recipe_which_depends_on_py_version
                version: 2
            requirements:
                build:
                 - python
                 - numpy
                run:
                 - python x.x
                 - numpy x.x
            """
        with open(os.path.join(self.recipe_dir, 'meta.yaml'), 'w') as fh:
            fh.write(recipe)
        conda_build.config.config.CONDA_PY = 35
        conda_build.config.config.CONDA_NPY = 17

        meta = MetaData(self.recipe_dir)

        index = {'python-2.7-0.tar.bz2': {'name': 'python', 'version': '2.7', 'build_number': 0}}
        self.index.add_pkg('python', '2.7.2')
        self.index.add_pkg('python', '3.5.0')
        self.index.add_pkg('numpy', '1.8.0', depends=['python'])
        r = BakedDistribution.compute_matrix(meta, self.index)
        self.assertEqual(len(r), 2)
        self.assertEqual(r[0].build_id(), 'np18py27_0')
        self.assertEqual(r[1].build_id(), 'np18py35_0')


if __name__ == '__main__':
    unittest.main()

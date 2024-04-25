import os
import unittest

import yaml

from kubegraph.data.template import loads_all


def _load_file(filename: str) -> str:
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


class TestCases(unittest.TestCase):
    maxDiff = None

    def test_load(self) -> None:
        base_dir = f'{os.path.dirname(__file__)}/../templates/db'
        files = (
            file
            for file in (
                os.path.realpath(f'{template_dir}/graph.yaml')
                for template_dir in (
                    os.path.realpath(f'{base_dir}/{dir_name}')
                    for dir_name in os.listdir(base_dir)
                )
                if os.path.isdir(template_dir)
            )
            if os.path.isfile(file)
        )

        objs = [
            obj
            for file in files
            for obj in yaml.safe_load_all(_load_file(file))
        ]

        templates = loads_all(objs)
        objs_reconstructed = [
            template.model_dump()
            for template in templates
        ]

        self.assertEqual(
            first=objs,
            second=objs_reconstructed,
        )


if __name__ == '__main__':
    unittest.main()

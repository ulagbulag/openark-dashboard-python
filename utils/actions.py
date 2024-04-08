from datetime import datetime
from typing import List
import inflection
import yaml

import jinja2
import kubernetes as kube

from utils.types import Specs, Template


class Actions:
    def __init__(self, path: str) -> None:
        kube.config.load_config()

        self._env = jinja2.Environment()
        self._kube = kube.client.ApiClient()
        self._path = path

    def _load(self, name: str) -> str:
        return open(f'{self._path}/{name}.yaml.j2', 'r').read()

    def _render(
        self,
        namespace: str,
        name: str,
        spec: Specs,
    ) -> List[Template]:
        template = self._env.from_string(self._load(name))
        timestamp = int(datetime.now().timestamp())

        return [
            yaml.safe_load(template.render(
                metadata=dict(
                    name=f'{inflection.dasherize(name)}-{timestamp}-{index}',
                    namespace=namespace,
                ),
                spec=spec,
            ))
            for index, spec in enumerate(
                spec if isinstance(spec, list) else [spec]
            )
        ]

    def apply_kubernetes(
        self,
        namespace: str,
        name: str,
        spec: Specs,
    ) -> None:
        templates = self._render(
            name=name,
            namespace=namespace,
            spec=spec,
        )

        kube.utils.create_from_yaml(
            k8s_client=self._kube,
            yaml_objects=templates,
            namespace=namespace,
        )

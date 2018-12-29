import importlib.util
import os
import pathlib
from enum import Enum
from typing import Callable, List, Mapping

TypeMap = Mapping[str, str]
Loader = Callable[[pathlib.Path], None]


class Category(Enum):
    ASSET = "asset"
    TEXTURE = "texture"


class Plugin(object):
    def __init__(self, category: Category, supported_type_map: TypeMap,
                 loader: Loader):
        self.__category = category
        self.__supported_type_map = supported_type_map
        self.__loader = loader

    def category(self) -> Category:
        return self.__category

    def can_run(self, file_path: pathlib.Path) -> bool:
        return file_path.suffix.lower() in self.__supported_type_map

    def run(self, file_path: pathlib.Path):
        self.__loader(file_path)


class PluginManager(object):
    def __init__(self):
        self.__plugins: List[Plugin] = []
        self.__search_paths: List[pathlib.Path] = []

    def add_search_path(self, search_path: pathlib.Path):
        self.__search_paths.append(search_path)

    def register_plugins(self):
        category_map = {
            "asset": Category.ASSET,
            "texture": Category.TEXTURE,
        }

        for search_path in self.__search_paths:
            for module_path in search_path.glob("*.py"):
                name = module_path.stem
                spec = importlib.util.spec_from_file_location(name, module_path)
                plugin = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin)

                if not hasattr(plugin, "loader"):
                    continue
                if not hasattr(plugin, "category"):
                    continue
                if not hasattr(plugin, "supported_types"):
                    continue

                if plugin.category not in category_map:
                    raise RuntimeError("'{}' is not a valid category".format(plugin.category))

                self.__plugins.append(Plugin(category_map[plugin.category], plugin.supported_types, plugin.loader))

    @classmethod
    def register(cls):
        manager = cls()

        # Internal plugin path
        internal_plugin_path = pathlib.Path(__file__).parent / "Plugins"
        manager.add_search_path(internal_plugin_path)

        # Environment variable pugin path
        search_paths = os.environ.get("YAAM_PLUGIN_PATHS", "")

        if search_paths:
            for search_path in search_paths.split(os.pathsep):
                manager.add_search_path(pathlib.Path(search_path))

        manager.register_plugins()

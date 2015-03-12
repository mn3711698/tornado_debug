# coding: utf8
import functools

from tornado_debug.utils import resolve_path
from tornado_debug.import_hook import register_import_hook


def wrap_module_func(module, attribute, wrapper_factory):
    (parent, attribute, original) = resolve_path(module, attribute)
    wrapper = wrapper_factory(original)
    setattr(parent, attribute, wrapper)


def regist_wrap_module_func_hook(module_str, attribute, wrapper_factory):
    register_import_hook(module_str, functools.partial(wrap_module_func, attribute=attribute, wrapper_factory=wrapper_factory))

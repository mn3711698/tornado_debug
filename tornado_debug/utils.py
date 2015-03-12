# coding: utf8
import inspect
import six
import sys


def resolve_path(module, name):
    if isinstance(module, six.string_types):
        __import__(module)
        module = sys.modules[module]

    parent = module

    path = name.split('.')
    attribute = path[0]

    original = getattr(parent, attribute)
    for attribute in path[1:]:
        parent = original

        # We can't just always use getattr() because in doing
        # that on a class it will cause binding to occur which
        # will complicate things later and cause some things not
        # to work. For the case of a class we therefore access
        # the __dict__ directly. To cope though with the wrong
        # class being given to us, or a method being moved into
        # a base class, we need to walk the class heirarchy to
        # work out exactly which __dict__ the method was defined
        # in, as accessing it from __dict__ will fail if it was
        # not actually on the class given. Fallback to using
        # getattr() if we can't find it. If it truly doesn't
        # exist, then that will fail.

        if inspect.isclass(original):
            for cls in inspect.getmro(original):
                if attribute in vars(cls):
                    original = vars(cls)[attribute]
                    break
            else:
                original = getattr(original, attribute)

        else:
            original = getattr(original, attribute)

    return (parent, attribute, original)

from distutils.core import setup


setup(
    name="tornado-debug",
    version="0.0.1",
    description="debug tornado web application",
    author="shaolianbo",
    author_email="lianboshao@sohu-inc.com",
    packages=['tornado_debug', "tornado_debug.bootstrap", "tornado_debug.hook"],
    scripts=["tor-debug"],
    long_description="""debug tornado web application."""
)

from distutils.core import setup


setup(
    name="tornado-debug",
    version="${version}",
    description="debug tornado web application",
    author="shaolianbo",
    author_email="lianboshao@sohu-inc.com",
    packages=['tornado_debug', "tornado_debug.bootstrap", "tornado_debug.hook"],
    package_data={'tornado_debug': ['static/bootstrap/*', 'static/jquery/*', 'static/tnDebug/*', 'templates/*']},
    scripts=["tor-debug"],
    long_description="""debug tornado web application."""
)

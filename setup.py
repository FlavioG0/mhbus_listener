from distutils.core import setup

setup(name="mhbus_listener",
    version="1.7",
    description="Events manager for bticino MyHome System",
    author="Flavio Giovannangeli",
    author_email="flavio.giovannangeli@gmail.com",
    url="https://github.com/FlavioG0/mhbus_listener",
    license="GPLv3",
    scripts=["m_main.py"],
    py_modules=["m_eventsman","cl_btbus","cl_email","cl_gsmat","cl_log","cl_pdu","cl_twtapi"]
)
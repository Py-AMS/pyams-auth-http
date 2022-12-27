=================================
PyAMS HTTP authentication package
=================================

.. contents::


What is PyAMS?
==============

PyAMS (Pyramid Application Management Suite) is a small suite of packages written for applications
and content management with the Pyramid framework.

**PyAMS** is actually mainly used to manage web sites through content management applications (CMS,
see PyAMS_content package), but many features are generic and can be used inside any kind of web
application.

All PyAMS documentation is available on `ReadTheDocs <https://pyams.readthedocs.io>`_; source code
is available on `Gitlab <https://gitlab.com/pyams>`_ and pushed to `Github
<https://github.com/py-ams>`_. Complete doctests are available in the *doctests* folder.


What is PyAMS HTTP authentication?
==================================

This package is a plug-in for PyAMS security policy; it allows to extract credentials from HTTP
basic authorization header.

You have to include this package in your Pyramid configuration to activate this plug-in.

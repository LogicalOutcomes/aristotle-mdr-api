Aristotle-MDR API
=================

.. image:: https://travis-ci.org/aristotle-mdr/aristotle-mdr-api.svg?branch=master
    :target: https://travis-ci.org/aristotle-mdr/aristotle-mdr-api

.. image:: https://coveralls.io/repos/aristotle-mdr/aristotle-mdr-api/badge.svg
    :target: https://coveralls.io/r/aristotle-mdr/aristotle-mdr-api

The Aristotle-MDR API provides a self-documenting JSON API for retrieving content
from thean Aristotle-MeteData-Registry

Quick start
-----------

1. Add `aristotle_mdr_api` and `rest_framework`  to your INSTALLED_APPS setting::

        INSTALLED_APPS = (
            ...
            'aristotle_mdr',
            'aristotle_mdr_api',
            'rest_framework',
            ...
        )

#. Include the API URL definitions in your Django URLconf file ::

        url(r'^api/', include('aristotle_mdr_api.urls',app_name="aristotle_mdr_api",namespace="aristotle"))),

#. Run ``python manage.py migrate`` to update the database to include the models for the API.

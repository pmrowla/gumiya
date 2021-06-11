gumiya
======

Twitch + Bancho chat bot for handling osu! related functions.

.. image:: https://travis-ci.com/pmrowla/gumiya.svg?branch=master
    :target: https://travis-ci.com/pmrowla/gumiya
.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django


:License: MIT


Usage
-----

1. Sign in to https://gumiya.pmrowla.com/
2. Link and verify your osu! account
3. Configure and enable the bot


Help
----

* Check the `FAQ`_.
* Submit bug/feature requests via github issues (please check to see if your issue has already been posted first).
* For other generic help requests please try to refrain from cluttering up the github issues list and just ask in `discord`_.

.. _`FAQ`: https://github.com/pmrowla/gumiya/wiki/FAQ
.. _`discord`: https://discord.gg/JDZhNPG


Features
--------

This intent of this project is to eventually have feature parity with the Mikuia osu! plugin.
Currently working features include:

* Beatmap requests

  * PP info for requests via Tillerino
  * Optional request filtering based on star rating
  * Optional subscribers only mode for map requests

* osu! player `!stats` command for Twitch chat

Gumiya is not intended to be a general purpose Twitch bot, and as such will never include support for non-osu! related Mikuia features.

Screenshots
^^^^^^^^^^^

.. image:: http://i.imgur.com/DS9SD83.png

.. image:: http://i.imgur.com/EM1sCVh.png

.. image:: http://i.imgur.com/WoGIWXu.png

Notes
^^^^^

* Mods for map requests can be specified with or without the leading ``+`` and are not case sensitive.
  When mods are used, the bot output will always the display the modified AR, OD and BPM, but displaying modified star rating is dependent on Tillerino.
  If Tillerino is unavailable, or if Tillerino does not have a calculated PP or star rating for a certain map + mod combination, the nomod star rating will be used (see the HDDTHR example screenshot).
* When filtering map requests by star rating, the filtering is done based on nomod star rating, regardless of whether the request specifies mods.


Developing
----------

* Use docker-compose with ``dev.yml`` (see docs from cookiecutter-django below).
* Dev discord: https://discord.gg/JDZhNPG

Rolling your own bot instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* If you just want to run your own IRC bot for map requests on a single Twitch channel, a standalone version of the Gumiya bot is available as `gumiyabot`_.
* If for some reason you are interested in running your own instance of the entire Gumiya bot + webapp server package, the whole thing is deployable with docker-compose.
See detailed `cookiecutter-django Docker documentation`_ for details.

.. _`gumiyabot`: https://github.com/pmrowla/gumiyabot
.. _`cookiecutter-django Docker documentation`: http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html

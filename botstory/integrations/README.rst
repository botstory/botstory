interface.tracker
-----------------

Collects statistics of usage like path through stories.

Implementations
~~~~~~~~~~~~~~~

- `Google Analytics <https://github.com/botstory/botstory/blob/develop/botstory/integrations/ga/tracker.py>`_

*Usage:*
.. code-block:: python
    from botstory.integrations.ga import tracker

    story.use(tracker.GAStatistics(tracking_id='UA-XXXXX-Y'))

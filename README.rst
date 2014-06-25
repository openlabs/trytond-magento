Tryton Magento Integration
==========================

Integration of Magento e-commerce platform with Tryton ERP.

.. image:: https://travis-ci.org/openlabs/trytond-magento.png?branch=develop
  :target: https://travis-ci.org/openlabs/trytond-magento

.. image:: https://coveralls.io/repos/openlabs/trytond-magento/badge.png?branch=develop
  :target: https://coveralls.io/r/openlabs/trytond-magento


Documentation
-------------

Detailed documentation is available for the project at
`read the docs <http://tryton-magento-connector.readthedocs.org/en/latest/>`_.
The documentation is automatically generated and contributions to improve
the documentation, or translate them is welcome.

Please create an issue before you start working on anything to avoid
duplication of effort.

Features of Magento Tryton connector
------------------------------------

* Multiple Magento instance architecture: The existing structure has been
  retained with each instance having multiple websites with each website
  comprising of different stores leading to a group of store views. The 
  users can import these Magento instance parameters to Tryton with the
  assistance of this connector.
* Import and Export: Users can import catalogues, categories and products
  along with customers’ information and addresses. The Magento Tryton
  connector imports every order status including the cancelled orders.
  The other imported orders are pending, enqueued, started, done or
  failed. The connector also creates a contact if it did not exist earlier.
* Synchronization: The Magento Tryton connector processes the import of
  orders on the basis of the order status in Tryton, thus synchronising
  the information across the e-commerce and ERP platforms.
* Fully Tested: The connector and the integration is completely scrutinized
  by unit test cases which check the functionality with different order and
  product types and other combinations. The testing ensures that the
  connector behavior is predictable and active development does not hinder
  the working features. You can 
  `see it <https://travis-ci.org/openlabs/trytond-magento>`_ for yourself.


Contributions
-------------

Contributions are always welcome and must adhere to the license of this
module. Please report bugs and discuss them if you are not sure. We are
happy to discuss with you.

If you are planning on writing new features, please read the sections
below about extensions. If your feature is not generic enough, we may not
be willing to accept it in this core module. From our bitter experiences
in the past with modules (like this integration) we have intentionally
made the choice of keeping this module as a simple core to which
extensions (other tryton modules) can enahance functionality. If you are
not sure if your feature should be part of the core or a separate module,
feel free to ask.

Extensions
----------

This module is meant to be the basic foundation with minimal functionality
that is common to all magento stores. Each store is different and so is each
implementation is different. The design of this module tries to be as
modular as possible to make it simple to write downstream modules which
extend the functionality.

A known list of extensions are listed below:

================== ============================ ========================================================================
Module Name         Features                    Links
================== ============================ ========================================================================
magento_weight      * Exports product weights   * `Bitbucket <https://bitbucket.org/zikzakmedia/trytond-magento_weight>`_
                    * Respects UOM of weight    * Package: trytonzz_magento_weight
                                                * Author: `Zikzakmedia <www.zikzakmedia.com>`_
================== ============================ ========================================================================

If you have written an extension module for magento connector and would
like to have it listed here, please send a pull request updating this
README file.

Website
-------

Visit the `Openlabs website <http://www.openlabs.co.in>`_ for latest news
and downloads. You can also follow us on Twitter 
`@openlabsindia <http://twitter.com/openlabsindia>`_ to receive updates on
releases.

Support
-------

If you have any questions or problems, please report an
`issue <https://github.com/openlabs/trytond-magento/issues>`_.

You can also reach us at `support@openlabs.co.in <mailto:support@openlabs.co.in>`_
or talk to a human at +1 813 793 6736. Please do not email any of the Openlabs
developers directly with issues or questions as you're more likely to get an
answer if you create a github issue or email us at the above address.

You can also mail us your ideas and suggestions about any changes.

Professional Support
--------------------

This module is professionally supported by `Openlabs <http://www.openlabs.co.in>`_.
If you are looking for on-site teaching or consulting support, contact our
`sales <mailto:sales@openlabs.co.in>`_ team.


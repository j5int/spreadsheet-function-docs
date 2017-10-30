Spreadsheet Function Docs
=========================

spreadsheet-function-docs is a project that provides spreadsheet function documentation in a JSON structure.
This means that it is easily consumable by software to provide function reference information.

Currently the documentation included is generated from the Apache OpenOffice.org source code

The documentation is published in this project as `openoffice-function-docs.json`

Generating the docs
-------------------

Code to retrieve the source code and generate the function documentation repository is included in the source tree.

To re-run the generation, you will need to

* check out the source code from [the repository](https://github.com/j5int/spreadsheet-function-docs/)
* ensure that the [Python Requests library](http://www.python-requests.org/) is available. This can be done by:

  - Installing [Python](https://www.python.org/)
  - Creating a virtual environment with `virtualenv spreadsheet-function-docs`
  - Running `pip install ./requirements.txt`

* run `./generate_spreadsheet_functions.py`
* The file will be saved as `openoffice-function-docs.json`

Licensing
---------

The generation code is licensed under the [Apache 2.0 License](./LICENSE.md); see `LICENSE.md` for me details

The actual function documentation in the JSON structure produced is licensed under whatever license it was released in the original source code.
This license is indicated in the JSON structure as well.


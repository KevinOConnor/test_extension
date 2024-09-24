This is a temporary repository for Klipper extension system testing.

Steps to install and run this extension:

1. Create a Klipper extensions directory: `mkdir ~/kextensions/`

2. Modify Klipper host startup to include that directory:
   `klippy.py -e ~/kextensions/ ...`

3. Create a new Python virtual environment in the extensions directory:
   `virtualenv ~/kextensions/test_extension/`

4. Install this extension into that directory:
   `~/kextensions/bin/pip install /path/to/pyexttest/`

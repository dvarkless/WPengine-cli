#! /usr/bin/bash

pyinstaller --onefile wengine.py
echo ""
echo "Create binary in system folder /usr/bin:"
sudo mv dist/wengine /usr/bin/wengine

#!/usr/bin/env bash

#TODO: bump version

echo "------------------------------------------------------------------------"
echo ""
echo " remove previous build"
echo ""
echo "------------------------------------------------------------------------"
rm -r ./build ./dist
echo "------------------------------------------------------------------------"
echo ""
echo " create source distribution"
echo ""
echo "------------------------------------------------------------------------"
pyenv exec python setup.py sdist
echo "------------------------------------------------------------------------"
echo ""
echo " build wheels"
echo ""
echo "------------------------------------------------------------------------"
pyenv exec python setup.py bdist_wheel
echo "------------------------------------------------------------------------"
echo ""
echo "register"
echo ""
echo "------------------------------------------------------------------------"
pyenv exec twine register dist/*.whl
echo "------------------------------------------------------------------------"
echo ""
echo "upload"
echo ""
echo "------------------------------------------------------------------------"
pyenv exec twine upload dist/*
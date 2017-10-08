#!/usr/bin/env bash

# bump semver of module

set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo 'bump to new version'

version=`cat ${DIR}/../botstory/version.txt`
versions=`git tag --list`

echo 'current version' ${version}

#increase patch
next_version="${version%.*}.$((${version##*.}+1))"

#TODO: increase major and beta version based on arguments

echo 'new version' ${next_version}
echo ${next_version} > ${DIR}/../botstory/version.txt
echo 'updated version.txt'

if [[ ${versions} == *${next_version}* ]]; then
   echo 'already has this version'
   exit 1
fi

# update CHANGELOG
github_changelog_generator

${DIR}/deploy.sh

git commit -am "bump to ${next_version}"
git tag ${next_version}
git push
git push --tag

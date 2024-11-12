#!/bin/sh

tag=$1
echo "Input tag: '$tag'"

major=$(sed -rn 's/^SET\(CMAKE_PROJECT_VERSION_MAJOR[[:space:]]*"(.*)"\)/\1/p' CMakeLists.txt)
minor=$(sed -rn 's/^SET\(CMAKE_PROJECT_VERSION_MINOR[[:space:]]*"(.*)"\)/\1/p' CMakeLists.txt)
patch=$(sed -rn 's/^SET\(CMAKE_PROJECT_VERSION_PATCH[[:space:]]*"(.*)"\)/\1/p' CMakeLists.txt)
rc=$(sed -rn 's/^SET\(CMAKE_PROJECT_VERSION_RC[[:space:]]*"(.*)"\)/\1/p' CMakeLists.txt)

# Construct version string
version="${major}.${minor}.${patch}"
if [ ! -z "$rc" ]; then
    version="${version}-rc${rc}"
fi

echo "Version in 'CMakeLists.txt' file: '$version'"

if [ "$tag" != "" ]; then
    echo "Release mode: check version consistency..."
    if [ "$tag" != "$version" ]; then
        echo "ERROR: the tag '$tag' is different from the version '$version' in the 'CMakeLists.txt' file"
        exit 1
    fi
else
    echo "Snapshot mode: fetch existing tags..."
    git fetch --tags
    if [ $(git tag -l "$version") ]; then
        echo "ERROR: version '$version' has already been released"
        exit 1
    fi
fi
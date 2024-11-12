#!/bin/sh

echo "Compute the current API version..."
version=$1

if [ "$version" = "" ]; then
    # Extract version components
    major=$(sed -rn 's/.*MAJOR.*\"(.*)\".*/\1/p' CMakeLists.txt)
    minor=$(sed -rn 's/.*MINOR.*\"(.*)\".*/\1/p' CMakeLists.txt)
    patch=$(sed -rn 's/.*PATCH.*\"(.*)\".*/\1/p' CMakeLists.txt)
    rc=$(sed -rn 's/.*VERSION_RC.*\"(.*)\".*/\1/p' CMakeLists.txt)

    # Construct version string
    version="${major}.${minor}.${patch}"
    if [ ! -z "$rc" ]; then
        version="${version}-rc${rc}"
    else
        version="${version}-SNAPSHOT"
    fi
fi

echo "Computed current API version: $version"

sed -i "s/%PROJECT_VERSION%/$version/g" ./.github/doxygen/Doxyfile
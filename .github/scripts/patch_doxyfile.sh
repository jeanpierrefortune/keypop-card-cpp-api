#!/bin/sh

echo "Compute the current API version..."
version=$1

if [ "$version" = "" ]; then
    # Extract version components
    major=$(sed -rn 's/^SET\(CMAKE_PROJECT_VERSION_MAJOR[[:space:]]*"(.*)"\)/\1/p' CMakeLists.txt)
    minor=$(sed -rn 's/^SET\(CMAKE_PROJECT_VERSION_MINOR[[:space:]]*"(.*)"\)/\1/p' CMakeLists.txt)
    patch=$(sed -rn 's/^SET\(CMAKE_PROJECT_VERSION_PATCH[[:space:]]*"(.*)"\)/\1/p' CMakeLists.txt)
    rc=$(sed -rn 's/^SET\(CMAKE_PROJECT_VERSION_RC[[:space:]]*"(.*)"\)/\1/p' CMakeLists.txt)

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
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

repository_name=$(git rev-parse --show-toplevel | xargs basename)

echo "Clone $repository_name..."
git clone --branch gh-pages https://github.com/jeanpierrefortune/"$repository_name".git

cd "$repository_name" || exit

echo "Delete existing SNAPSHOT directory..."
rm -rf ./*-SNAPSHOT

echo "Create target directory $version..."
mkdir "$version"

echo "Copy Doxygen doc..."
cp -rf ../.github/doxygen/out/html/* "$version"/

# Update "latest" only for stable versions (non SNAPSHOT and non RC)
if ! echo "$version" | grep -q "SNAPSHOT" && ! echo "$version" | grep -q "rc"; then
    echo "Creating/Updating latest symlink..."
    rm -f latest
    ln -s "$version" latest

    # Update robots.txt to allow indexing of latest version only
    cat > robots.txt << EOF
User-agent: *
Allow: /
Allow: /latest/
Disallow: /*/[0-9]*/
EOF
fi

echo "Update versions list..."
echo "| Version | Documents |" >list_versions.md
echo "|:---:|---|" >>list_versions.md

# Add "latest" entry only for stable versions
if [ -L "latest" ]; then
    echo "| latest | [API documentation](latest) |" >>list_versions.md
fi

# Create a temporary file with versions in the desired order
for directory in $(ls -d [0-9]*/ | cut -f1 -d'/'); do
    # Convert version string to a sortable format
    # For non-RC versions: append "zz" to make them sort before RC versions
    # For RC versions: extract RC number and pad with zeros
    version_str=$(echo "$directory" | sed 's/-rc/./g')
    if echo "$directory" | grep -q "rc"; then
        # RC version: pad RC number with zeros
        echo "${version_str}a" >> temp_versions.txt
    else
        # Regular version: add "zz" to sort before RC
        echo "${version_str}z" >> temp_versions.txt
    fi
done

# Sort versions and convert back to original format
for version in $(sort -rV temp_versions.txt | sed 's/[az]$//g' | sed 's/\.rc/-rc/g'); do
    echo "| $version | [API documentation]($version) |" >>list_versions.md
done

rm -f temp_versions.txt

echo "Computed all versions:"
cat list_versions.md

cd ..

echo "Local docs update finished."
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

repository_name=$(git rev-parse --show-toplevel | xargs basename)

echo "Clone $repository_name..."
git clone --branch gh-pages https://github.com/eclipse-keypop/"$repository_name".git

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

# Add all version-specific entries
# Sort in reverse order, with RC versions appearing after their corresponding release version
for directory in $(ls -rd [0-9]*/ | cut -f1 -d'/' | sort -V -r); do
    echo "| $directory | [API documentation]($directory) |" >>list_versions.md
done

echo "Computed all versions:"
cat list_versions.md

cd ..

echo "Local docs update finished."
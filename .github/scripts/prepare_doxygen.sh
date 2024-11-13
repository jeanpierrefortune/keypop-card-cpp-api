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
# Add header to the markdown table
echo "| Version | Documents |" > list_versions.md
echo "|:---:|---|" >> list_versions.md

# Add "latest" entry only for stable versions
if [ -L "latest" ]; then
    echo "| latest | [API documentation](latest) |" >> list_versions.md
fi

# Create a temporary file with versions in the desired order
rm -f temp_versions.txt
for directory in $(ls -d [0-9]*/ | cut -f1 -d'/'); do
    # Clean the directory name from any trailing spaces or special characters
    clean_dir=$(echo "$directory" | tr -d '[:space:]')
    if echo "$clean_dir" | grep -q "rc"; then
        # RC version: use exact format "X.Y.Z-rcN"
        echo "${clean_dir}" >> temp_versions.txt
    else
        echo "${clean_dir}" >> temp_versions.txt
    fi
done

# Sort versions and generate markdown entries
sort -t. -k1,1nr -k2,2nr -k3,3nr -k4,4r temp_versions.txt | while read version; do
    echo "| ${version} | [API documentation](${version}) |" >> list_versions.md
done

rm -f temp_versions.txt

# Display result
echo "Computed all versions:"
cat list_versions.md

cd ..

echo "Local docs update finished."
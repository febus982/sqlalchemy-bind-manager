#!/usr/bin/env bash

VERSION=$(poetry version -s)
SEMVER=( ${VERSION//./ } )
echo "${SEMVER[0]}.${SEMVER[1]}"

#!/usr/bin/env bash

# uv doesn't yet support reading dynamic version: https://github.com/astral-sh/uv/issues/14137
#VERSION=$(uv version --short)
VERSION=$(uv run scripts/version_from_git.py)
SEMVER=( ${VERSION//./ } )
echo "${SEMVER[0]}.${SEMVER[1]}"

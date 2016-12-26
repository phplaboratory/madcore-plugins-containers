#!/usr/bin/env bash
pushd /opt/plugins/cuda/pycuda/examples
    python3 "$@"
popd

#!/bin/sh
options="$*"
if [ -z $options ] ; then options="-O";fi
../../bin/pyjsbuild $* KitchenSink.py

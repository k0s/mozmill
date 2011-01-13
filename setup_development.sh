#!/bin/bash
# in order dependencies
for i in mozinfo mozprocess mozprofile mozrunner jsbridge mozmill 
do 
    cd $i
    python setup.py develop
    cd ..
done


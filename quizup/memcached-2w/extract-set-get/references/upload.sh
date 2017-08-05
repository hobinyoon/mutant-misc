#!/bin/bash

path='/home/sveinnfannar/traces'

echo "$(date -u): Checking for files to upload" >> /home/sveinnfannar/upload.log
for file in $(ls -t $path | tail -n +2); do
  #lsof 2>/dev/null | grep --quiet $path/$file # Check if file is open
  #if [ $? -eq 0 ]; then
  #  echo "Not uploading $file because it's still being written to" >> /home/sveinnfannar/upload.log
  #else
  #  echo "Uploading $file to S3" >> /home/sveinnfannar/upload.log
  #  aws s3 mv $path/$file s3://quizup-cache-experiments-34k23df93lk/quizup/traces/$file >> /home/sveinnfannar/upload.log 2>&1
  #fi
  echo "Uploading $file to S3" >> /home/sveinnfannar/upload.log
  aws s3 mv $path/$file s3://quizup-cache-experiments-34k23df93lk/quizup/traces/$file >> /home/sveinnfannar/upload.log 2>&1
done
  

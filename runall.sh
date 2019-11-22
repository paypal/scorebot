#!/usr/bin/env bash

if [ $# -eq 0 ] 
then
   req1="status"
else
   req1=$1
fi

echo ">>>> SCORE Bot: ${req1}"

for script in scorebot.sh daemon*.sh
do 
   echo
   echo "=============================="
   echo
   cmd1="./$script ${req1}"
   echo $cmd1
   $cmd1
done

echo "=== END ==="
echo

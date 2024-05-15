# Path: ./formatter.sh

files=`ls ./grammarflow/*/*.py`
for eachfile in $files
do
   autopep8 --in-place --aggressive --aggressive --max-line-length=80 --experimental $eachfile
done


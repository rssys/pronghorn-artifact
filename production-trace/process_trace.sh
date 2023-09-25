#!/bin/bash

# Use this script as following:
# bash gen_trace.sh dXX <first-min> <last-min> <max-memory>
#
# dXX is the identifier of the day of observations
# first-min is the first minute to consider
# last-min is the last minute to consider
# max-memory is the desired anticipated max memory consumption in MB

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
GREEN='\033[0;32m'
NC='\033[0m' # No Color

cd "$DIR" || {
  echo "Redirection failed!"
  exit 1
}

JAR=$DIR/azure-dataset-1.0-all.jar
MAIN=org.graalvm.argo.dataset.DatasetProcessor

echo -e "${GREEN}Processing the Azure dataset...${NC}"
$JAVA_HOME/bin/java -cp $JAR $MAIN $@
echo -e "${GREEN}Processing the Azure dataset...done${NC}"

# python3 process_trace.py
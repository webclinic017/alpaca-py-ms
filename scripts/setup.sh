#!/bin/bash

# Colors
red=$(tput setaf 1)
green=$(tput setaf 2)
blue=$(tput setaf 4)
reset=$(tput sgr0)

# ========================================================================
# @brief createMarketstoreContainer
# Create and initialize marketstore Docker container
function createMarketstoreContainer()
{
  echo "Starting Marketstore container"
  local CONFIG_FILE=$ALPACA_MS_ROOT/alpaca/conf/mkts.yml
  sudo docker create --name mktsdb --restart always -p 5993:5993 alpacamarkets/marketstore:latest
  sudo docker cp $CONFIG_FILE mktsdb:/etc/mkts.yml
  sudo docker start -i mktsdb
}

# ========================================================================
# @brief runMarketstoreContainer
# Create and run marketstore container
function updateAlpacaPackages()
{
  echo "Updating Alpaca Trade API"
  python -m pip install --upgrade pip
  pip install git+https://github.com/alpacahq/alpaca-trade-api-python
  pip install git+https://github.com/alpacahq/pymarketstore
  pip install git+https://github.com/mariostoev/finviz
}

# ========================================================================
# @brief compileProtobuf
# Compile .proto file into Python and C++ bindings
function compileProtobuf()
{
   # Ensure proto compiler (protoc) is installed
   if [ -z "$(which protoc)" ]; then
      sudo snap install protobuf --classic
   fi

   # Create folder for compiled messages
   PROTO_OUTPUT=$ALPACA_MS_ROOT/alpaca/interface/generated
   mkdir -p "$PROTO_OUTPUT"
   touch $PROTO_OUTPUT/__init__.py
   rm -f $PROTO_OUTPUT/*pb* 2> /dev/null || true

   # Location of .proto files
   PROTO_INPUT=$ALPACA_MS_ROOT/alpaca/interface

   # Compile protoc
   printf "Generating $PROTO_OUTPUT/interface_pb2.py..."
   protoc -I=$PROTO_INPUT --python_out=$PROTO_OUTPUT $PROTO_INPUT/interface.proto
   protoc -I=$PROTO_INPUT --cpp_out=$PROTO_OUTPUT $PROTO_INPUT/interface.proto

   if [ -f $PROTO_OUTPUT/interface_pb2.py ]; then
      printf "${green}SUCCESS\n${reset}"
   else
      printf "${red}FAILED\n${reset}"
   fi
}

# ========================================================================
# @brief buildInterfaceJson
# Generate interface JSON file
function buildInterfaceJson()
{
   $ALPACA_MS_ROOT/scripts/buildInterfaceJson.py
}

# ========================================================================
# @brief buildDocumentation
# Build pdoc html documentation
function buildDocumentation()
{
   cd $ALPACA_MS_ROOT/..
   pdoc --html --force --skip-errors --output-dir $ALPACA_MS_ROOT/documents Autotrader
   cd $ALPACA_MS_ROOT
}

# ========================================================================
# @brief runAutotrader
# Run all Autotrader services at market open.
function runAutotrader()
{
   echo "Sleeping until the market opens..."
   python ./scripts/sleep_until_open.py
   ret=$?

   if [ $ret -ne 0 ]; then
     echo "Exiting"
     exit
   fi

   echo "Starting Alpaca Service."
   ./scripts/start_alpaca_service.sh > ./LOGS/alpaca_service.log &

   echo "Starting Portfolio Manager."
   ./services/portfolio_scv.py > ./LOGS/portfolio_service.log &

   echo "Starting Test Subscribers."
   ./scripts/runTestSubscribers.py > ./LOGS/TestSubscribers.log &

   echo "Tasks Completed."
}

# ========================================================================
# @brief killAutotrader
# Kills Autotrader processes
function killAutotrader()
{
  echo "Stopping Autotrader services"

  ports=(5001 5002 5003 5004 5005 5006 5007) 

  echo "  Cleaning up ports"
  for p in "${ports[@]}"; do
      pidList=$(lsof -t -i:"$p")
      if [ ! -z "$pidList" ]
      then
          echo "    Killing processes $pidList on port $p"
          kill -9 $pidList
      fi
  done

  echo "  Killing Alpaca Monitor"
  pkill -f start_alpaca_service

  echo "  Killing Alpaca"
  pkill -f alpaca_svc

  echo "  Portfolio Service"
  pkill -f portfolio_scv

  echo "  Killing Test Subscribers"
  pkill -f runTestSubscribers

  echo "Tasks complete."
}

# ========================================================================
# @brief installProtobuf
# Clone and install Google protocol buffers
function installProtobuf()
{
    sudo apt-get install autoconf automake libtool curl make g++ unzip
    pushd /home/$USER/git || exit
    git clone https://github.com/protocolbuffers/protobuf.git
    pushd protobuf || exit
    git submodule update --init --recursive
    ./autogen.sh
    ./configure
    make
    make check
    sudo make install
    sudo ldconfig # refresh shared library cache.
}

# ========================================================================
# @brief installPackages
# Install required packages
function installPackages()
{
    pip install protobuf
    pip install git+https://github.com/alpacahq/alpaca-trade-api-python
    pip install git+https://github.com/mariostoev/finviz
}

# ========================================================================
# @brief testAutotrader
# Run Autotrader test suite
function testAutotrader()
{
  pytest --disable-warnings
}


function helpAutotrader()
{
    local script=$ALPACA_MS_ROOT/scripts/setup.sh

    # shellcheck disable=SC2059
    printf "${blue}========================= Autotrader =========================\n${reset}"
    printf "Welcome to Autotrader, ${green}%s\n${reset}" $USER


    printf "${blue}\n------------------------ Environment -------------------------\n${reset}"
    printf "ALPACA_MS_ROOT : %s\n" $ALPACA_MS_ROOT

    printf "${blue}\n----------------------- Function Help ------------------------\n${reset}"
    sed -n "/@brief/,/function/p" $script | \
        grep -v sed | \
        sed 's/function.*//g' | \
        sed 's|#\s*||g' | \
        sed -z 's|\(.*\)\n$|\1|'

    printf "${blue}==============================================================\n${reset}"
}


# Configure Autotrader root
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ALPACA_MS_ROOT="$(dirname "$SCRIPTS_DIR")"

# Configure PYTHONPATH
if [ -z "${PYTHONPATH}" ]; then
  export PYTHONPATH=$ALPACA_MS_ROOT
else
  export PYTHONPATH=$ALPACA_MS_ROOT:$PYTHONPATH
  PYTHONPATH="$(perl -e 'print join(":", grep { not $seen{$_}++ } split(/:/, $ENV{PYTHONPATH}))')"
fi

helpAutotrader

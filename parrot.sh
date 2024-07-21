#!/bin/bash

# Check if an argument is provided
if [ $# -lt 2 ]; then
    echo "Please provide the number of iterations and config file as arguments."
    exit 1
fi

# Get the number of iterations from the first argument
iterations=$1
config=$2
log_dir="parrot_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$log_dir"

# Loop for the specified number of iterations
for (( i=1; i<=$iterations; i++ ))
do
    # Generate a unique log file name using current timestamp
    log_file="parrot_$(date +%Y%m%d_%H%M%S_%N).log"
    
    echo "Running iteration $i, output will be saved to $log_file"
    
    # Run parrot.py and redirect stdout to the log file
    python parrot.py "$config" | tee "$log_dir/$log_file"
done
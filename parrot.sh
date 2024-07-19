#!/bin/bash

# Check if an argument is provided
if [ $# -eq 0 ]; then
    echo "Please provide the number of iterations as an argument."
    exit 1
fi

# Get the number of iterations from the first argument
iterations=$1

# Loop for the specified number of iterations
for (( i=1; i<=$iterations; i++ ))
do
    # Generate a unique log file name using current timestamp
    log_file="parrot_$(date +%Y%m%d_%H%M%S_%N).log"
    
    echo "Running iteration $i, output will be saved to $log_file"
    
    # Run parrot.py and redirect stdout to the log file
    python parrot.py | tee "$log_file"
done
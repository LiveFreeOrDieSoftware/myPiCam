#!/bin/bash 
# this script is way over-engineered for what it is.
# it is meant to send a message on motion when used with the 
# RPi_Cam_Web_Interface
# That just sends motions starts. Stops are separate.
# Instead I am using the start_video macro which passes
# the mp4 filename as an arguement when calling the script
# all it was ever supposed to do is what is in the last line
# everything else is an exercise in programming
#
# Default vaues are hard coded, but the Broker and Message
# can be passed from as arguemments.
#
# 'motion' events in Cam-Web-Interface only pass a 0 (start)
# or 1 (end). Img and Vid events pass file names
############################################################
# Help                                                     #
############################################################
Help()
{
   # Display Help
   echo "Send a 'motion' alert via MQTT when called."
   echo
   echo "Syntax: scriptTemplate [-g|h|v|V]"
   echo "options:"
   echo "g     Print the GPL license notification."
   echo "h     Print this Help."
   echo "b     Broker DNS name or IP address"
   echo "m     Enter the message to be sent"
   echo "v     Verbose mode."
   echo "V     Print software version and exit."
   echo
}

############################################################
############################################################
# Main program                                             #
############################################################
############################################################
# set variables
Message="default message"
Broker=10.0.0.5
TIMESTAMP=$(date +"%T") 
HOSTNAME=$(hostname)

############################################################
# Process the input options. Add options as needed.        #
############################################################
# Get the options
while getopts ":h:b:m:" option; do
   case $option in
      h) # display Help
         Help
         exit;;
      b) # Enter broker name or address
         Broker=$OPTARG;;
      m) # Enter a message
         Message=$OPTARG;;
     \?) # Invalid option
         echo "Error: Invalid option"
         exit;;
   esac
done

# uncomment for testing
# echo "Message is $Message"
# echo "Broker is $Broker"
# echo "mosquitto_pub -h $Broker -t motion -m "timestamp:$TIMESTAMP, host:$HOSTNAME, message: $Message" "

mosquitto_pub -h $Broker -t motion -m "timestamp:$TIMESTAMP, host:$HOSTNAME, message: $Message" 

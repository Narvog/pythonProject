"""
##################################################
## The purpose of this script is to sync video and sensor readings.
##################################################
## Project: Wireless Sensor Node (WSN) Project - MICS Group @ VT
## Data: 09/19/2020
## Status: {Prototype}
## Python 3.8.8
## Tested on Windows 10
##################################################

"""


import cv2
import time
import os
from datetime import datetime

src = 1       # Change
folder_name = "C:/Users/brand/OneDrive/Desktop/Video"  # Change
recording_length = 60  #900  #in seconds

def get_current_time( time_option ) :
    if time_option == 1 :
        time_now = str( datetime.now() ).split()
    else :
        time_now = time.time()
    return time_now

fps = 30
width = 864
height = 640
video_codec = cv2.VideoWriter_fourcc( "m" , "p" , "4" , "v" )

print( "Data and Videos will be saved in the following directory:" , folder_name )
print("Recording length is ", recording_length, "Seconds")
cap = cv2.VideoCapture( src )
ret = cap.set( 3 , 480 )

start = time.time()
video_counter = 0
video_file = os.path.join( folder_name , str( video_counter ) + ".mp4" )
# print( "Capture video saved location : {}".format( video_file ) )

# print("Creating Video Writer...")
# Create a video write before entering the loop
video_writer = cv2.VideoWriter( video_file , video_codec ,
                                fps , (int( cap.get( 3 ) ) ,
                                       int( cap.get( 4 ) )) )


exp_start_time = get_current_time(1)
print('\033[1m' + "Press Q to terminate" + '\033[0m')
print("Start time of the experiment:" + str(exp_start_time[0]) + " " +str(exp_start_time[1]) )

while cap.isOpened() :
    start_time = time.time()
    ret , frame = cap.read()
    if ret :
        cv2.imshow( "frame" , frame )
        # print(time.time() - start)
        if time.time() - start > recording_length :
            print( "Uploading data, batch number:" , str( video_counter + 1 ) )
            start = time.time()
            video_counter += 1
            video_file = os.path.join( folder_name , str( video_counter ) + ".mp4" )
            data_file = os.path.join( folder_name , str( video_counter - 1 ) + ".csv" )
            video_writer = cv2.VideoWriter(
                video_file , video_codec , fps , (int( cap.get( 3 ) ) , int( cap.get( 4 ) ))
            )
            #export data and reset

        # Write the frame to the current video writer
        current_time = get_current_time( 0 )
        video_writer.write( frame )

        if cv2.waitKey( 1 ) & 0xFF == ord("q") :
            exp_end_time = get_current_time(1)
            print( "End time of the experiment:" + str( exp_end_time[ 0 ] ) + " " + str( exp_end_time[ 1 ] ) )
            print( "Program Terminated" )
            break
    else :
        break
cap.release()
cv2.destroyAllWindows()
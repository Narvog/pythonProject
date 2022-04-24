from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
import cv2
import csv
import time
import os
from datetime import datetime
from tqdm import tqdm


header = ['Index', 'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z', 'time segment']
src = 0       # Change
folder_name = "C:/Users/brand/OneDrive/Desktop/Data/SN3"  # Change
recording_length = 900  # in seconds
timestamp = 0
start = time.time()

def get_current_time(time_option):
    if time_option == 1:
        time_now = str(datetime.now()).split()
    else:
        time_now = time.time()
    return time_now


fps = 30
width = 864
height = 640
video_codec = cv2.VideoWriter_fourcc("m", "p", "4", "v")

print("Data and Videos will be saved in the following directory:", folder_name)
print("Recording length is ", recording_length, "Seconds")
cap = cv2.VideoCapture(src)
ret = cap.set(3, 480)


video_counter = 0
video_file = os.path.join(folder_name, str(video_counter) + ".mp4")
# print( "Capture video saved location : {}".format( video_file ) )

# print("Creating Video Writer...")
# Create a video write before entering the loop
video_writer = cv2.VideoWriter(video_file, video_codec, fps, (int(cap.get(3)), int(cap.get(4))))




exp_start_time = get_current_time(1)
print('\033[1m' + "Press Q to terminate" + '\033[0m')
print("Start time of the experiment:" + str(exp_start_time[0]) + " " + str(exp_start_time[1]))


class State:
    # init state
    def __init__(self, device):
        self.device = device
        self.samples = 0
        self.accSamples = 0
        self.gyroSamples = 0

        self.acc_data = []
        self.gyro_data = []
        self.time_segments = []

        self.accCallback = FnVoid_VoidP_DataP(self.acc_data_handler)
        self.gyroCallback = FnVoid_VoidP_DataP(self.gyro_data_handler)

    # acc callback function
    def acc_data_handler(self, ctx, data):
        # print("ACC: %s -> %s" % (self.device.address, parse_value(data)))
        self.samples += 1
        self.accSamples += 1
        sdata = parse_value(data)
        pdata = [sdata.x * 9.8, sdata.y * 9.8, sdata.z * 9.8]
        self.acc_data.append(pdata)
        timesegment = time.time() - start
        self.time_segments.append(timesegment)

    # gyro callback function
    def gyro_data_handler(self, ctx, data):
        # print("GYRO: %s -> %s" % (self.device.address, parse_value(data)))
        self.samples += 1
        self.gyroSamples += 1
        sdata = parse_value(data)
        # print("%s -> %s" % (self.device.address, parse_value(data)))
        pdata = [sdata.x, sdata.y, sdata.z]
        self.gyro_data.append(pdata)


# init
states = []
# connect to all mac addresses in arg
d = MetaWear("DD:67:4C:10:D8:A4")  # SN1: "C2:08:77:A0:48:FE" SN2:
d.connect()
print("Connected to " + d.address + " over " + ("USB" if d.usb.is_connected else "BLE"))
states.append(State(d))

# configure all metawears
for s in states:
    print("Configuring device")
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
    sleep(1.5)

    # config acc
    # libmetawear.mbl_mw_acc_set_odr(s.device.board, 50.0) # Generic call
    libmetawear.mbl_mw_acc_bmi160_set_odr(s.device.board, AccBmi160Odr._50Hz)  # BMI 160 specific call
    libmetawear.mbl_mw_acc_bosch_set_range(s.device.board, AccBoschRange._4G)
    libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)

    # config gyro
    libmetawear.mbl_mw_gyro_bmi160_set_range(s.device.board, GyroBoschRange._1000dps)
    libmetawear.mbl_mw_gyro_bmi160_set_odr(s.device.board, GyroBoschOdr._50Hz)
    libmetawear.mbl_mw_gyro_bmi160_write_config(s.device.board)

    # get acc signal and subscribe
    acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_subscribe(acc, None, s.accCallback)

    # get gyro signal and subscribe
    gyro = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_subscribe(gyro, None, s.gyroCallback)

    # start accS
    libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board)
    libmetawear.mbl_mw_acc_start(s.device.board)

    # start gyro
    libmetawear.mbl_mw_gyro_bmi160_enable_rotation_sampling(s.device.board)
    libmetawear.mbl_mw_gyro_bmi160_start(s.device.board)

# sleep 10 s
# sleep(60.0)

pbar = tqdm(total=100)
start = time.time()
s2 = time.time()
timestamp = 0

while cap.isOpened():
    start_time = time.time()
    ret, frame = cap.read()
    if ret:
        cv2.imshow("frame", frame)
        # print(time.time() - start)
        if time.time() - s2 > (recording_length/100):
            s2 = time.time()
            pbar.update(1)
        if time.time() - start > recording_length:
            print("Uploading data, batch number:", str(video_counter + 1))
            pbar.clear()
            pbar.close()
            video_counter += 1
            video_file = os.path.join(folder_name, str(video_counter) + ".mp4")
            data_file = os.path.join(folder_name, str(video_counter - 1) + ".csv")
            video_writer = cv2.VideoWriter(
                video_file, video_codec, fps, (int(cap.get(3)), int(cap.get(4)))
            )
            # export data and reset
            f = open(data_file, 'w', newline='')
            data = []
            if s.accSamples < s.gyroSamples:
                length = s.accSamples
            else:
                length = s.gyroSamples
            for i in range(length):
                data.append([i, s.acc_data[i][0], s.acc_data[i][1], s.acc_data[i][2], s.gyro_data[i][0],
                             s.gyro_data[i][1], s.gyro_data[i][2], s.time_segments[i]])
            writer = csv.writer(f)
            writer.writerow(header)
            # for (i = 0; i < self.expected_samples -1; i++):
            # writer.writerow(acc_data[i])
            writer.writerows(data)
            s.acc_data = []
            s.gyro_data = []
            s.accSamples = 0
            s.gyroSamples = 0
            s.time_segments = []
            data = []
            f.close()


            pbar = tqdm(total=100)
            pbar.update(0)
            start = time.time()
            s2 = time.time()

        # Write the frame to the current video writer
        current_time = get_current_time(0)
        video_writer.write(frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            exp_end_time = get_current_time(1)
            print("End time of the experiment:" + str(exp_end_time[0]) + " " + str(exp_end_time[1]))
            print("Program Terminated")
            break
    else:
        break
cap.release()
cv2.destroyAllWindows()
pbar.close()
# breakdown meta wears
for s in states:
    # stop acc
    libmetawear.mbl_mw_acc_stop(s.device.board)
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)

    # stop gyro
    libmetawear.mbl_mw_gyro_bmi160_stop(s.device.board)
    libmetawear.mbl_mw_gyro_bmi160_disable_rotation_sampling(s.device.board)

    # unsubscribe acc
    acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(acc)

    # unsubscribe gyro
    gyro = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(gyro)

    # disconnect
    libmetawear.mbl_mw_debug_disconnect(s.device.board)

# download recap
print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))
    print("Exported Segments: " + str(video_counter))

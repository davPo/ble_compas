import struct
import numpy as np

ACCELEROMETER = 0x40  # b7-b6 = 1
MAGNETOMETER = 0x80  # b7-b6 = 2
GYROSCOPE = 0xC0  # b7-b6 = 3


class DATA_TYPE:
    ACCELEROMETER_RAW = 1
    MAGNETOMETER_RAW = 2
    GYROSCOPE_RAW = 3
    HEADING = 4

class Vector():
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def from_bytes(self, bytes_array):
        self.x = float(struct.unpack('f', bytes_array[0:4])[0])
        self.y = float(struct.unpack('f', bytes_array[4:8])[0])
        self.z = float(struct.unpack('f', bytes_array[8:12])[0])

    def __repr__(self):
        s = ("X={0} Y={1} Z={2}".format(self.x, self.y, self.z))
        return s

    def as_tsv(self):
        s = ("{0}\t{1}\t{2}".format(self.x, self.y, self.z))
        return s

    def as_nparray(self):
        arr = np.array([self.x, self.y, self.z])
        return arr

    def scale(self, factor):
        self.x = self.x * factor
        self.y = self.y * factor
        self.z = self.z * factor


class DataDecoder:
    ACCEL_MG_LSB_2G = 0.000244  # used by defaur
    ACCEL_MG_LSB_4G = 0.000488
    ACCEL_MG_LSB_8G = 0.000976
    SENSORS_GRAVITY_STANDARD = 9.80665  # Earth's gravity in m/s^2
    MAG_UT_LSB = 0.1  # sensor sensitivity (uT/LSB)

    def signedbyte(self, byte):
        if byte > 127:
            return (256 - byte) * (-1)
        else:
            return byte

    def battery_level_decoder(self, data):
        return "{0}".format(int(data[0]))

    def sensor_raw_decoder(self, sender, data):
        raw_val = Vector()
        raw_val.from_bytes(data)
        return raw_val

    def sensor_heading_decoder(self, sender, data):
        heading = int(data[0]) + int(data[1]) * 256  # unsigned
        msb = self.signedbyte(data[3])
        roll = int(data[2]) + msb * 256  # signed
        msb = self.signedbyte(data[5])
        pitch = int(data[4]) + msb * 256  # signed
        polar = chr(data[6])  # dec to ASCII
        hold = chr(data[7])  # dec to ASCII
        # heading = int.from_bytes(data[0:1], byteorder='big')
        # print ("{0}:{1}:{2}".format(heading,polar,hold))
        return heading, roll, pitch, polar, hold


def matrix2bytes(bias_array, scaling_matrix, header):
    """ return list of 4 bytes array from correction matrix
    U8_Header, U8_x_b0, U8_x_b1, U8_x_b2, U8_x_b3, U8_y_b0 ... U8_z_b3"""
    words = []
    corr = np.append(bias_array, scaling_matrix)  # build a single array
    idx = 0
    for n in np.split(corr, 4):  # divide in 4 parts
        # print(n) # debug
        tmp = np.asarray(n, dtype=np.float32).tobytes()  # convert to bytes with IEEE format for floats
        tmp = bytearray(tmp)  # bytes to bytes array
        tmp[0:0] = bytes([header + idx])  # insert header - data type and word index
        words.append(tmp)  # insert in list
        idx += 1
    return words


def from_bytes(uint8_lsb, uint8_msb):
    """Return an int from 2 bytes"""
    n = uint8_lsb + uint8_msb * 256
    if n > (32767):
        return (65536 - n) * (-1)
    else:
        return n


if __name__ == "__main__":
    pass

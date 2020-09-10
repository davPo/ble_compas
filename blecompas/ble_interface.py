# Version compatible with Jupyter Notebook
# working  !!!

import asyncio
import logging
import queue
from time import sleep, strftime, time

from bleak import BleakClient, discover
from bleak.uuids import uuid16_dict

from blecompas.helper import *

uuid16_dict = {v: k for k, v in uuid16_dict.items()}

MODEL_NBR_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Model Number String")
)

BATTERY_LEVEL_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Battery Level")
)


SENSOR_HEADING_UUID =   "1f7fbeea-8c8b-11e9-bc42-526af7764f64"
SENSOR_CORRECTION_UUID = "1f7fbf0b-8c8b-11e9-bc42-526af7764f64"
SENSOR_RAW_UUID =   "1f7fbda0-8c8b-11e9-bc42-526af7764f64"
RAWDATA_MAG_CHARACTERISTIC_UUID =  "1f7fbdc1-8c8b-11e9-bc42-526af7764f64"
RAWDATA_GYRO_CHARACTERISTIC_UUID =  "1f7fbda2-8c8b-11e9-bc42-526af7764f64"
RAWDATA_ACC_CHARACTERISTIC_UUID =  "1f7fbdf3-8c8b-11e9-bc42-526af7764f64"
SENSOR_RSSI_UUID = "1f7fa12b-8c8b-11e9-bc42-526af7764f64"

class BleInterface():
    timeout = 5
    client = None
    loop = None
    bound = False

    def __init__(self, address):
        self.address = address
        self.result_queue = queue.Queue()

    async def connect(self):
        await self._connect_run(self.address)

    async def getBatteryValue(self):
        battery_level= await self.client.read_gatt_char(BATTERY_LEVEL_UUID)
        level="{0}%".format(int(battery_level[0]))
        return level

    async def getHeadingRollPitch(self):
        bytes_data = await self.client.read_gatt_char(SENSOR_HEADING_UUID)
        heading, roll, pitch, polar,hold = DataDecoder().sensor_heading_decoder(None, bytes_data)
        return heading, roll, pitch, hold

    async def isHold(self):
        bytes_data = await self.client.read_gatt_char(SENSOR_HEADING_UUID)
        heading, roll, pitch, polar,hold = DataDecoder().sensor_heading_decoder(None, bytes_data)
        if hold == 'H':
            return True
        else:
            return False

    async def getSensorRawValues(self, type):
        if type == DATA_TYPE.MAGNETOMETER_RAW:
            values= await self.client.read_gatt_char(RAWDATA_MAG_CHARACTERISTIC_UUID)
        elif type == DATA_TYPE.ACCELEROMETER_RAW:
            values= await self.client.read_gatt_char(RAWDATA_ACC_CHARACTERISTIC_UUID) 
        elif type == DATA_TYPE.GYROSCOPE_RAW:
            values= await self.client.read_gatt_char(RAWDATA_GYRO_CHARACTERISTIC_UUID) 
        else:
            return None
        vector = DataDecoder().sensor_raw_decoder("", values)
        return vector

    async def _read_characteristics(self, uuid):
        rep = await self.client.read_gatt_char(uuid)
        return rep

    async def getBLEcharacteristics(self,uuid):
        return await self.client.read_gatt_char(uuid)

    async def _connect_run(self, address):
        self.client = BleakClient(address, loop=self.get_loop())
        await self.client.connect()

    async def disconnect(self):
        expiration = time() + self.timeout
        while self.loop.is_running() and time() <= expiration:
            sleep(0.1)
        sleep(1)
        try:
            await self._close_run()
        except RuntimeError as e:
            if "loop is already running" not in str(e):
                raise e
        self.bound = False

    async def _close_run(self):
        self.result_queue.put(None)
        # stop notification
        try:
            await self.client.stop_notify(RAWDATA_MAG_CHARACTERISTIC_UUID)
            await self.client.stop_notify(RAWDATA_ACC_CHARACTERISTIC_UUID)
            await self.client.stop_notify(RAWDATA_GYRO_CHARACTERISTIC_UUID)
            await self.client.stop_notify(SENSOR_HEADING_UUID)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass
         # disconnect        
        try:
            await self.client.disconnect()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass

    async def read(self):
        await self._read_run_()

    async def _read_run_(self):
        if not self.bound:
            self.bound = True
            await self.client.start_notify(RAWDATA_MAG_CHARACTERISTIC_UUID, self.callback) 
            await self.client.start_notify(RAWDATA_ACC_CHARACTERISTIC_UUID, self.callback) 
            await self.client.start_notify(SENSOR_HEADING_UUID, self.callback) 
        #return 0

    def callback(self,sender,data):
        #print("{0}: {1}".format(sender, data))
        if str(sender) in RAWDATA_MAG_CHARACTERISTIC_UUID:
            mag = DataDecoder().sensor_raw_decoder(sender, data)
            logging.debug("Pushing raw data to queue")
            self.result_queue.put({DATA_TYPE.MAGNETOMETER_RAW:mag})
        elif str(sender) in RAWDATA_ACC_CHARACTERISTIC_UUID:
            accel = DataDecoder().sensor_raw_decoder(sender, data)
            logging.debug("Pushing raw data to queue")
            self.result_queue.put({DATA_TYPE.ACCELEROMETER_RAW:accel})
        elif str(sender) in RAWDATA_GYRO_CHARACTERISTIC_UUID:
            gyro = DataDecoder().sensor_raw_decoder(sender, data)
            logging.debug("Pushing raw data to queue")
            self.result_queue.put({DATA_TYPE.GYROSCOPE_RAW:gyro})
        elif str(sender) in SENSOR_HEADING_UUID:
            heading, roll, pitch, polar,hold = DataDecoder().sensor_heading_decoder(sender, data)
            logging.debug("Pushing heading data to queue")
            self.result_queue.put({DATA_TYPE.HEADING:heading})
            
    async def uploadCalibration(self, correctionbytes):
        """upload calibration - to accomadate ble packet length it is 4 words 
            1 word is header byte + 12 bytes of data
            """
        for rawb in correctionbytes:
            print (rawb.hex())
            await self.client.write_gatt_char(SENSOR_CORRECTION_UUID,  rawb)

    async def uploadCalibrationTest(self, bytes):
        """upload calibration 13 bytes 
            header byte + 12 bytes of data
            """
        rawb = bytearray(bytes)
        print (rawb.hex())
        await self.client.write_gatt_char(SENSOR_CORRECTION_UUID,  rawb)

    def encode_command(self, command):
        return (command + "\r\n").encode("ascii")

    def get_loop(self):
        if not self.loop:
            self.loop = asyncio.get_event_loop()
        return self.loop

class NoResponseException(Exception):
    pass

async def scan_ble_device(targetdevice):
    """Return a BLE device which Model name match target device"""
    foundDevice = None
    devices = await discover()
    formatted = []
    for device in devices:
        formatted.append({
            "address": device.address,
            "name": device.name,
        })
        if targetdevice in device.name:
            foundDevice = device
            logging.info("Found BLE device : "+ foundDevice.name) 
    return foundDevice


from enum import IntEnum


class Mode(IntEnum):
    TX = 0
    RX = 1
    TX_F = 2
    RX_F = 3
    SERVICE_F = 4
    OTA_F = 5  # firmware upgrade for NooLite-F


class Request(IntEnum):
    CMD = 0
    BROADCAST_CMD = 1
    READ = 2
    BIND_START = 3
    BIND_STOP = 4
    CLEAR = 5
    CLEAR_ALL = 6
    UNBIND = 7
    CMD_F_ADDR = 8


class Response(IntEnum):
    SUCCESS = 0
    NO_RESPONSE = 1
    ERROR = 2
    BIND_SUCCESS = 3


class Command(IntEnum):
    OFF = 0
    BRIGHT_DOWN = 1
    ON = 2
    BRIGHT_UP = 3
    TOGGLE = 4
    BRIGHT_BACK = 5
    BRIGHT_SET = 6
    LOAD_PRESET = 7
    SAVE_PRESET = 8
    UNBIND = 9
    BRIGHT_STOP = 10  # Stop_Reg
    BRIGHT_STEP_DOWN = 11
    BRIGHT_STEP_UP = 12
    BRIGHT_START = 13  # Bright_Reg
    BIND = 15
    ROLL_COLOR = 16
    RGB_COLOR = 17
    RGB_MODE = 18
    RGB_MODE_BACK = 19
    BATTERY_LOW = 20
    SENSOR_TEMP_HUM = 21
    TEMPORARY_ON = 25
    SET_MODES = 26
    READ_STATE = 128
    WRITE_STATE = 129
    SEND_STATE = 130
    SERVICE = 131
    CLEAR_MEMORY = 132

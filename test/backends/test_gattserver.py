"""
Example for a BLE 4.0 Server using a GATT dictionary of services and
characteristics
"""
import sys
import logging
import asyncio
import threading

import signal # python doesn't keyboard interrupt an asyncio.Event.wait() so...
signal.signal(signal.SIGINT, signal.SIG_DFL)

from typing import Any, Dict, Union

from bless import (  # type: ignore
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
    GATTDescriptorProperties,
)

class BlessServer(BlessServer):
    """A BLE server that uses a GATT dictionary to define services and characteristics."""
    def add_new_descriptor(self, service_uuid, char_uuid, desc_uuid, properties, value, permissions):
        print("Adding new descriptor")
        print(f"Service UUID: {service_uuid}")
        return super().add_new_descriptor(service_uuid, char_uuid, desc_uuid, properties, value, permissions)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(name=__name__)

trigger: Union[asyncio.Event, threading.Event]
if sys.platform in ["darwin", "win32"]:
    trigger = threading.Event()
else:
    trigger = asyncio.Event()


def read_request(characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
    logger.debug(f"Reading {characteristic.value}")
    return characteristic.value


def write_request(characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
    characteristic.value = value
    logger.debug(f"Char value set to {characteristic.value}")
    if characteristic.value == b"\x0f":
        logger.debug("Nice")
        trigger.set()

ADVERTISED_SERVICE = "A07498CA-AD5B-474E-940D-16F1FBE7E8CD"
ADVERTISED_CHARACTERISTIC = "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"

async def run(loop):
    trigger.clear()

    # Instantiate the server
    gatt: Dict = {
        ADVERTISED_SERVICE: {
            ADVERTISED_CHARACTERISTIC: {
                "Properties": (
                    GATTCharacteristicProperties.read
                    | GATTCharacteristicProperties.write
                    | GATTCharacteristicProperties.indicate
                ),
                "Permissions": (
                    GATTAttributePermissions.readable
                    | GATTAttributePermissions.writeable
                ),
                "Value": None,
                'Descriptors': {
                    '2901': { # Bluetooth descriptor guid, or your custom 128bit guid
                        'Properties': (
                            GATTDescriptorProperties.read
                            | GATTDescriptorProperties.write
                        ),
                        'Permissions': (
                            GATTAttributePermissions.readable
                            | GATTAttributePermissions.writeable
                        ),
                        'Value': b'AMAZINGNAME', # Static value for descriptor.
                    }
                },
            }
        },
        "5c339364-c7be-4f23-b666-a8ff73a6a86a": {
            "bfc0c92f-317d-4ba9-976b-cc11ce77b4ca": {
                "Properties": GATTCharacteristicProperties.read,
                "Permissions": GATTAttributePermissions.readable,
                "Value": bytearray(b"\x69"),
            }
        },
    }
    my_service_name = "Test Service"
    server = BlessServer(name=my_service_name, loop=loop)
    server.read_request_func = read_request
    server.write_request_func = write_request

    await server.add_gatt(gatt)
    await server.start()
    logger.debug(server.get_characteristic(ADVERTISED_CHARACTERISTIC))
    logger.debug("Advertising")
    logger.info(
        "Write '0xF' to the advertised characteristic: "
        + ADVERTISED_CHARACTERISTIC
    )
    if trigger.__module__ == "threading":
        trigger.wait()
    else:
        await trigger.wait()
    await asyncio.sleep(2)
    logger.debug("Updating")
    server.get_characteristic(ADVERTISED_CHARACTERISTIC).value = bytearray(
        b"i"
    )
    server.update_value(
        ADVERTISED_SERVICE, ADVERTISED_CHARACTERISTIC
    )
    await asyncio.sleep(5)
    await server.stop()
    print("Stopped...")


loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))
import sys
from uuid import UUID
if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal
from typing import Union, Optional, List, Dict, cast, TYPE_CHECKING
from bleak.backends.winrt.descriptor import (  # type: ignore
    BleakGATTDescriptorWinRT,
)

if sys.version_info >= (3, 12):
    from winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattProtectionLevel,
        GattLocalDescriptorParameters,
        GattLocalDescriptor,
        GattLocalDescriptorResult,
    )
else:
    from bleak_winrt.windows.devices.bluetooth.genericattributeprofile import (  # type: ignore # noqa: E501
        GattProtectionLevel,
        GattLocalDescriptorParameters,
        GattLocalDescriptor,
        GattLocalDescriptorResult,
    )

if TYPE_CHECKING:
    from bless.backends.winrt.characteristic import BlessGATTCharacteristicWinRT
    from bless.backends.characteristic import BlessGATTCharacteristic
from bless.backends.attribute import (  # noqa: E402
    GATTAttributePermissions,
)
from bless.backends.descriptor import (  # noqa: E402
    BlessGATTDescriptor,
    GATTDescriptorProperties,
)

class BlessGATTDescriptorWinRT(
    BlessGATTDescriptor, BleakGATTDescriptorWinRT
):
    """
    BlueZ implementation of the BlessGATTDescriptor
    """
    def __init__(
        self,
        uuid: Union[str, UUID],
        properties: GATTDescriptorProperties,
        permissions: GATTAttributePermissions,
        value: Optional[bytearray],
    ):
        """
        Instantiates a new GATT Characteristic but is not yet assigned to any
        service or application
        Parameters
        ----------
        uuid : Union[str, UUID]
            The string representation of the universal unique identifier for
            the characteristic or the actual UUID object
        properties : GATTDescriptorProperties
            The properties that define the characteristics behavior
        permissions : GATTAttributePermissions
            Permissions that define the protection levels of the properties
        value : Optional[bytearray]
            The binary value of the characteristic
        """
        value = value if value is not None else bytearray(b"")
        super().__init__(uuid, properties, permissions, value)
        self.value = value

    async def init(self, characteristic: "BlessGATTCharacteristic"):
        """
        Initialize the BlueZGattDescriptor object
        Parameters
        ----------
        characteristic : BlessGATTCharacteristic
            The characteristic to assign the descriptor to
        """
        desc_params: GattLocalDescriptorParameters = (
            GattLocalDescriptorParameters()
        )
        
        # desc_params.read_protection_level = (
        #     GattProtectionLevel.PLAIN
        #     # BlessGATTDescriptorWinRT.permissions_to_protection_level(
        #     #     self._permissions, True
        #     # )
        # )
        
        # desc_params.write_protection_level = (
        #     GattProtectionLevel.PLAIN
        #     # BlessGATTDescriptorWinRT.permissions_to_protection_level(
        #     #     self._permissions, False
        #     # )
        # )
        
        descriptor_result: GattLocalDescriptorResult = (
            await characteristic.obj.create_descriptor_async(
                UUID(self._uuid), desc_params
            )
        )
        
        gatt_desc: GattLocalDescriptor = descriptor_result.descriptor
        super(BlessGATTDescriptor, self).__init__(
            obj=gatt_desc, characteristic_uuid=characteristic.uuid, characteristic_handle=characteristic.handle
        )

    @staticmethod
    def permissions_to_protection_level(
        permissions: GATTAttributePermissions, read: bool
    ) -> GattProtectionLevel:
        """
        Convert the GATTAttributePermissions into a GattProtectionLevel
        GATTAttributePermissions currently only consider Encryption or Plain

        Parameters
        ----------
        permissions : GATTAttributePermissions
            The permission flags for the characteristic
        read : bool
            If True, processes the permissions for Reading, else process for Writing

        Returns
        -------
        GattProtectionLevel
            The protection level equivalent
        """
        result: GattProtectionLevel = GattProtectionLevel.PLAIN
        shift_value: int = 3 if read else 4
        permission_value: int = permissions.value >> shift_value
        if permission_value & 1:
            result |= GattProtectionLevel.ENCRYPTION_REQURIED
        return result

    @property
    def value(self) -> bytearray:
        """Get the value of the characteristic"""
        return bytearray(self._value)

    @value.setter
    def value(self, val: bytearray):
        """Set the value of the characteristic"""
        self._value = val
    
    @property
    def uuid(self) -> str:
        """The uuid of this characteristic"""
        return self.obj.get("UUID").value

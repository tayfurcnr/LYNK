"""
ROS MAVLink Message Converter
Converts between ROS mavros_msgs.msg.Mavlink and binary MAVLink frames.
"""
import struct

def ros_mavlink_to_binary(ros_msg) -> bytes:
    """
    Reconstructs a binary MAVLink frame from a ROS Mavlink message.
    
    Args:
        ros_msg: mavros_msgs.msg.Mavlink message object
        
    Returns:
        bytes: Raw MAVLink binary frame ready for transmission
        
    Raises:
        ValueError: If message reconstruction fails
        
    Example:
        >>> from mavros_msgs.msg import Mavlink
        >>> ros_msg = Mavlink()
        >>> binary_frame = ros_mavlink_to_binary(ros_msg)
        >>> lynk.mavlink.send_mavlink(interface, binary_frame, dst=0)
    """
    try:
        # Helper to safely get ROS msg attributes with MAVLink defaults
        def _get(attr, default=0):
            return getattr(ros_msg, attr, default)

        # 1. Magic byte (version indicator)
        magic = _get("magic", 253)
        frame = struct.pack("B", magic)
        
        # 2. Header (depends on MAVLink version)
        if magic == 253:  # MAVLink v2
            # Message ID is 24-bit in v2
            msgid_bytes = struct.pack("<I", _get("msgid"))[:3]
            header = struct.pack("BBBBBB", 
                _get("len"), 
                _get("incompat_flags"), 
                _get("compat_flags"), 
                _get("seq"), 
                _get("sysid"), 
                _get("compid")
            ) + msgid_bytes
        else:  # MAVLink v1 (magic == 254)
            header = struct.pack("BBBBB", 
                _get("len"), 
                _get("seq"), 
                _get("sysid"), 
                _get("compid"), 
                _get("msgid") & 0xFF
            )
        
        frame += header

        # 3. Payload (stored as 64-bit chunks in ROS)
        payload64 = _get("payload64", [])
        payload_bytes = b""
        for u64 in payload64:
            payload_bytes += struct.pack("<Q", u64)
        frame += payload_bytes[:_get("len")]

        # 4. Checksum (16-bit CRC)
        frame += struct.pack("<H", _get("checksum"))

        # 5. Signature (MAVLink v2 only, optional)
        signature = _get("signature")
        if magic == 253 and signature:
            frame += bytes(signature)

        return frame
        
    except Exception as e:
        raise ValueError(f"Failed to reconstruct MAVLink frame: {e}")


def binary_to_ros_mavlink(payload: bytes):
    """
    Parses a binary MAVLink frame into a ROS Mavlink message structure.
    
    Args:
        payload: Raw MAVLink binary frame
        
    Returns:
        dict: Dictionary with ROS Mavlink message fields
        
    Raises:
        ValueError: If payload is too short or malformed
        
    Example:
        >>> binary_frame = b"\\xFD\\x09..."
        >>> msg_dict = binary_to_ros_mavlink(binary_frame)
        >>> ros_msg = Mavlink(**msg_dict)
    """
    if len(payload) < 6:
        raise ValueError("Payload too short for MAVLink frame")
    
    try:
        msg_data = {}
        magic = payload[0]
        msg_data['magic'] = magic
        msg_data['framing_status'] = 1  # FRAMING_OK
        
        if magic == 253:  # MAVLink v2
            msg_data['len'] = payload[1]
            msg_data['incompat_flags'] = payload[2]
            msg_data['compat_flags'] = payload[3]
            msg_data['seq'] = payload[4]
            msg_data['sysid'] = payload[5]
            msg_data['compid'] = payload[6]
            # 24-bit message ID
            msg_data['msgid'] = struct.unpack("<I", payload[7:10] + b"\x00")[0]
            p_start = 10
            p_end = 10 + msg_data['len']
            msg_data['checksum'] = struct.unpack("<H", payload[p_end:p_end+2])[0]
        else:  # MAVLink v1 (magic == 254)
            msg_data['len'] = payload[1]
            msg_data['seq'] = payload[2]
            msg_data['sysid'] = payload[3]
            msg_data['compid'] = payload[4]
            msg_data['msgid'] = payload[5]
            p_start = 6
            p_end = 6 + msg_data['len']
            msg_data['checksum'] = struct.unpack("<H", payload[p_end:p_end+2])[0]

        # Extract payload and convert to 64-bit chunks (using list for ROS compatibility)
        p_data = payload[p_start:p_end]
        padded = p_data + b"\x00" * ((8 - len(p_data) % 8) % 8)
        msg_data['payload64'] = list(struct.unpack("<" + "Q" * (len(padded) // 8), padded))
        
        # Add signature as list of uint8 if exists (MAVLink v2)
        if magic == 253 and len(payload) > p_end + 2:
            sig_data = payload[p_end+2:]
            if sig_data:
                msg_data['signature'] = list(sig_data)
        
        return msg_data
        
    except Exception as e:
        raise ValueError(f"Failed to parse MAVLink frame: {e}")

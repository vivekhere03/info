import binascii
from google.protobuf.message import Message
from google.protobuf import text_format
from google.protobuf.json_format import MessageToJson, Parse


class ProtobufUtils:
    def __init__(self):
        pass
    
    def decode_protobuf(self, hex_data: str, proto_class) -> Message:
        """Decode hex-encoded protobuf data to a protobuf message object"""
        try:
            # Convert hex string to bytes
            binary_data = bytes.fromhex(hex_data)
            
            # Create an instance of the protobuf class
            message = proto_class()
            
            # Parse the binary data
            message.ParseFromString(binary_data)
            
            return message
        except Exception as e:
            print(f"Protobuf decode error: {e}")
            # Return empty message if decoding fails
            return proto_class()
    
    def encode_protobuf(self, message: Message) -> str:
        """Encode a protobuf message to hex string"""
        try:
            # Serialize the message to binary
            binary_data = message.SerializeToString()
            
            # Convert to hex string
            hex_data = binary_data.hex()
            
            return hex_data
        except Exception as e:
            print(f"Protobuf encode error: {e}")
            return ""
    
    def protobuf_to_json(self, message: Message) -> str:
        """Convert protobuf message to JSON string"""
        try:
            return MessageToJson(message, preserving_proto_field_name=True)
        except Exception as e:
            print(f"Protobuf to JSON error: {e}")
            return "{}"
    
    def json_to_protobuf(self, json_str: str, proto_class) -> Message:
        """Convert JSON string to protobuf message"""
        try:
            message = proto_class()
            Parse(json_str, message)
            return message
        except Exception as e:
            print(f"JSON to protobuf error: {e}")
            return proto_class()
    
    def protobuf_to_text(self, message: Message) -> str:
        """Convert protobuf message to text format"""
        try:
            return text_format.MessageToString(message)
        except Exception as e:
            print(f"Protobuf to text error: {e}")
            return ""
    
    def text_to_protobuf(self, text_str: str, proto_class) -> Message:
        """Convert text format to protobuf message"""
        try:
            message = proto_class()
            text_format.Parse(text_str, message)
            return message
        except Exception as e:
            print(f"Text to protobuf error: {e}")
            return proto_class()
    
    def validate_protobuf(self, hex_data: str, proto_class) -> bool:
        """Validate if hex data can be decoded as the specified protobuf class"""
        try:
            binary_data = bytes.fromhex(hex_data)
            message = proto_class()
            message.ParseFromString(binary_data)
            return True
        except Exception:
            return False
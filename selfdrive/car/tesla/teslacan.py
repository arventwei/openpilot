import copy
import crcmod
from opendbc.can.can_define import CANDefine
from selfdrive.car.tesla.values import CANBUS

class TeslaCAN:
  def __init__(self, dbc_name, packer):
    self.can_define = CANDefine(dbc_name)
    self.packer = packer
    self.crc = crcmod.mkCrcFun(0x11d, initCrc=0x00, rev=False, xorOut=0xff)

  @staticmethod
  def checksum(msg_id, dat):
    # TODO: get message ID from name instead
    ret = (msg_id & 0xFF) + ((msg_id >> 8) & 0xFF)
    ret += sum(dat)
    return ret & 0xFF

  def create_steering_control(self, angle, enabled, frame):
    can_definitions = self.can_define.dv["DAS_steeringControl"]

    values = {
      "DAS_steeringAngleRequest": angle,
      "DAS_steeringHapticRequest": can_definitions["DAS_steeringHapticRequest"].get("IDLE"),
      "DAS_steeringControlType": can_definitions["DAS_steeringControlType"].get("ANGLE_CONTROL" if enabled else "NONE"),
      "DAS_steeringControlCounter": (frame % 16),
    }

    data = self.packer.make_can_msg("DAS_steeringControl", CANBUS.chassis, values)[2]
    values["DAS_steeringControlChecksum"] = self.checksum(0x488, data[:3])
    return self.packer.make_can_msg("DAS_steeringControl", CANBUS.chassis, values)

  def create_action_request(self, msg_stw_actn_req, cancel):
    values = copy.copy(msg_stw_actn_req)

    if cancel:
      values["SpdCtrlLvr_Stat"] = self.can_define.dv["STW_ACTN_RQ"]["SpdCtrlLvr_Stat"].get("FWD")

    data = self.packer.make_can_msg("STW_ACTN_RQ", CANBUS.autopilot, values)[2]
    values["CRC_STW_ACTN_RQ"] = self.crc(data[:7])
    return self.packer.make_can_msg("STW_ACTN_RQ", CANBUS.autopilot, values)
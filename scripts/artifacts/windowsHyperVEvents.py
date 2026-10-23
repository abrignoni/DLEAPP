"""Windows Hyper-V events, for DLEAPP: virtual machine worker process events, Host Compute Service events and
virtual switch events, each with the message the provider's manifest gives the event.

Author: @AlexisBrignoni, Claude.
"""

import re

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_WORKER_PROVIDER = 'Microsoft-Windows-Hyper-V-Worker'
_NIC_PROVIDER = 'Microsoft-Windows-Hyper-V-SynthNic'
_COMPUTE_PROVIDER = 'Microsoft-Windows-Hyper-V-Compute'
_SWITCH_PROVIDER = 'Microsoft-Windows-Hyper-V-VmSwitch'

# (Event ID, version): (message, the template's field names up to the last one the message inserts), from the
# provider's manifest (WEVT_TEMPLATE) and message table (.mui) in Windows 11 build 26100.2033 (see notes).
_WORKER = {
    (18500, 0): ("'%1' started successfully. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18502, 0): ("'%1' was turned off. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18504, 0): ("'%1' was shut down using the Shutdown Integration Component with parameters: Force = %3, Reason = '%4' (Virtual machine ID %2)",
               ('VmName', 'VmId', 'Force', 'Reason')),
    (18506, 0): ("'%1' shut down was initiated using the Shutdown Integration Component (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18507, 0): ("'%1' shut down was initiated using the Shutdown Integration Component (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18508, 0): ("'%1' was shut down by the guest operating system. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18510, 0): ("'%1' saved successfully. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18512, 0): ("'%1' was reset. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18514, 0): ("'%1' was reset by the guest operating system. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18515, 0): ("'%1' was shut down for a reset initiated by the guest operating system. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18516, 0): ("'%1' was paused. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18518, 0): ("'%1' was resumed. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18524, 0): ("'%1' was paused for critical error. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18526, 0): ("'%1' was resumed from critical error. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18528, 0): ("'%1' was turned off as it could not recover from a critical error. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18539, 0): ("'%1' was reset because the guest operating system requested an operation that is not supported by Hyper-V or an unrecoverable error occurred. This caused a triple fault. If the problem persists, contact Product Support. Additional diagnostics are disabled for this virtual machine. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18540, 0): ("'%1' was reset because the guest operating system requested an operation that is not supported by Hyper-V. This request caused a triple fault. If the problem persists, contact Product Support. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18550, 0): ("'%1' was reset because an unrecoverable error occurred while accessing a virtual processor register which caused a triple fault. This error might have been caused by a problem in the hypervisor. If the problem persists, contact Product Support. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18560, 0): ("'%1' was reset because an unrecoverable error occurred on a virtual processor that caused a triple fault. If the problem persists, contact Product Support. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18570, 0): ("'%1' was faulted because the guest executed an intercepting instruction not supported by Hyper-V instruction emulation. If the problem persists, contact Product Support. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18571, 0): ("'%1' was faulted with general protection exception, due to insufficient memory on the host while emulating an instruction for this guest. Free up some memory on the host to resolve this issue. If the problem persists, contact Product Support. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18572, 0): ("'%1' was faulted with general protection exception, due to unexpected error occurred on the host while emulating an instruction for this guest. If the problem persists, contact Product Support. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18573, 0): ("'%1' was stopped because an intercept occurred while serving an interrupt request. If the problem persists, contact Product Support. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18580, 0): ("'%1' was powered off because a TLB page size mismatch error occurred on a virtual processor. If the problem persists, contact Product Support. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18590, 0): ("'%1' has encountered a fatal error.  The guest operating system reported that it failed with the following error codes: ErrorCode0: %3, ErrorCode1: %4, ErrorCode2: %5, ErrorCode3: %6, ErrorCode4: %7,  PreOSId: %9, VTL %11.  If the problem persists, contact Product Support for the guest operating system.  (Virtual machine ID %2)%n%nGuest message:%n%8",
               ('VmName', 'VmId', 'VmErrorCode0', 'VmErrorCode1', 'VmErrorCode2', 'VmErrorCode3', 'VmErrorCode4', 'VmErrorMessage', 'VmPreOSId', 'VmHvOSId', 'VmVtl')),
    (18592, 0): ("'%1' was fast-restored successfully. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18594, 0): ("'%1' fast-saved successfully. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18596, 0): ("'%1' was restored successfully. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18598, 0): ("'%1' has initiated a fast-save operation. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18600, 0): ("'%1' has initiated a fast-restore operation. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18602, 0): ("'%1' has encountered a fatal error and a memory dump has been generated.  The guest operating system reported that it failed with the following error code: %3.  If the problem persists, contact Product Support for the guest operating system.  (Virtual machine ID %2)",
               ('VmName', 'VmId', 'VmErrorCode')),
    (18604, 0): ("'%1' has encountered a fatal error but a memory dump could not be generated. Error %3.  If the problem persists, contact Product Support for the guest operating system.  (Virtual machine ID %2)",
               ('VmName', 'VmId', 'VmErrorCode')),
    (18606, 0): ("'%1' has encountered a fatal error and was saved to '%3' (Virtual machine ID %2)",
               ('VmName', 'VmId', 'Parameter0')),
    (18608, 0): ("'%1' was hibernated successfully. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18609, 0): ("'%1' properties were successfully initialized. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (18609, 1): ("'%1' properties were successfully initialized. (Virtual machine ID %2) %nGuest processor features: %3%nGuest xsave features: %4%nPartition creation flags: %5%nNon architectural core sharing: %6%nCache line flush size: %7%nAddress bit width: %8%nPhysical address width: %9",
               ('VmName', 'VmId', 'ProcessorFeatures', 'ProcessorXsaveFeatures', 'PartitionCreationFlags', 'NonArchitecturalCoreSharing', 'ProcessorCLFlushSize', 'ImplementedAddressBits', 'PhysicalAddressWidth')),
    (18610, 0): ("'%1' has encountered a fatal virtual firmware error.  The guest virtual firmware reported that it failed with the following error codes: ErrorCode0: %3, ErrorCode1: %4, ErrorCode2: %5, ErrorCode3: %6, ErrorCode4: %7.  If the problem persists, contact Product Support.  (Virtual machine ID %2)",
               ('VmName', 'VmId', 'VmErrorCode0', 'VmErrorCode1', 'VmErrorCode2', 'VmErrorCode3', 'VmErrorCode4')),
    (18617, 0): ("'%1' has encountered a watchdog timeout and was reset. If the problem persists, contact Product Support for the guest operating system. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (3210, 0): ("'%1' failed to save RAM contents during a checkpoint operation: %3 (%4). (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult')),
    (3211, 0): ("'%1' failed to save RAM contents during a checkpoint operation: %3 (%4).",
               ('VmName', 'VmId', 'ErrorCode', 'HResult')),
    (3212, 0): ("A checkpoint operation was cancelled for the virtual machine '%1'. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (3213, 0): ("A checkpoint operation was cancelled for the virtual machine '%1'.",
               ('VmName',)),
    (3216, 0): ("'%1' failed to switch using the new differencing disks during a checkpoint operation: %3 (%4). (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult')),
    (3217, 0): ("'%1' failed to switch using the new differencing disks during a checkpoint operation: %3 (%4).",
               ('VmName', 'VmId', 'ErrorCode', 'HResult')),
    (3280, 0): ("'%1' could not initiate a checkpoint operation: %3 (%4). (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult')),
    (3281, 0): ("'%1' could not initiate a checkpoint operation.",
               ('VmName',)),
    (3286, 0): ("'%1' was paused as a hr of a failure to resume execution during a checkpoint operation. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (3287, 0): ("'%1' was paused as a hr of a failure to resume execution during a checkpoint operation.",
               ('VmName',)),
    (3330, 0): ("'%1' could not access checkpoint repository: %3 (%4). (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult')),
    (3331, 0): ('Could not access checkpoint repository.',
               ()),
    (3332, 0): ("Cannot take checkpoint for '%1' because one or more pass-through disks are attached. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (3333, 0): ('Cannot take checkpoint.',
               ()),
    (3352, 0): ("Production Checkpoint for VM '%1' failed in the guest VSS Integration Component with error %3 (%4). If you continue to see this problem please use regular checkpoints instead (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult')),
    (3353, 0): ("Production Checkpoint for VM '%1' failed in the guest VSS Integration Component with error %3 (%4).",
               ('VmName', 'VmId', 'ErrorCode', 'HResult')),
    (3370, 0): ("'%1' is unable to reset the virtual hard disk path for %3 as a hr of failure to create a checkpoint. %4 (%5). (Virtual machine ID %2)",
               ('VmName', 'VmId', 'String', 'ErrorCodeString', 'ErrorCode')),
    (3371, 0): ('Unable to change the virtual hard disk path for %3 as a hr of failure to create a checkpoint. %4',
               ('VmName', 'VmId', 'String', 'ErrorCodeString')),
    (3372, 0): ("'%1' is unable to take a checkpoint due to incorrect file or path name '%3'. %4 (%5). (Virtual machine ID %2)",
               ('VmName', 'VmId', 'String', 'ErrorCodeString', 'ErrorCode')),
    (3373, 0): ('An attempt to take checkpoint failed due to incorrect file or path name %3. %4',
               ('VmName', 'VmId', 'String', 'ErrorCodeString')),
    (3438, 0): ("Cannot take checkpoint for '%1' because one or more synthetic fibre channel controllers are attached. (Virtual machine ID %2)",
               ('VmName', 'VmId')),
    (3439, 0): ('Cannot take checkpoint.',
               ()),
    (3465, 0): ('Failed to take a checkpoint.',
               ()),
    (26004, 0): ('Started guest memory saving for checkpoint.',
               ()),
    (26005, 0): ('Finished guest memory saving for checkpoint, time %2 s.',
               ('VmId', 'Time')),
    (33100, 0): ("'%1': Virtual machine successfully negotiated Virtual PCI protocol version %6 on '%5'. (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult', 'Parameter0', 'Parameter1')),
    (33101, 0): ("'%1': Virtual machine requested unsupported Virtual PCI protocol version %6 on '%5'. Error: '%3' (%4). (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult', 'Parameter0', 'Parameter1')),
    (33102, 0): ("'%1': An unexpected transport error occurred on the virtual PCI bus: %5. Error: '%3' (%4). (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult', 'Parameter0')),
    (33103, 0): ("'%1': A virtual PCI device was successfully offered to the virtual machine: '%5'. PnpID = '%6', FunctionType = %7. (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult', 'Parameter0', 'Parameter1', 'Parameter2')),
    (33104, 0): ("'%1': A virtual PCI device was successfully revoked from the virtual machine: '%5'. (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult', 'Parameter0')),
    (33105, 0): ("'%1': Hardware resources have been successfully assigned to a virtual PCI device: '%5'. Physical device LUID = %6, Virtual function LUID = %7. (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult', 'Parameter0', 'Parameter1', 'Parameter2')),
    (33106, 0): ("'%1': Hardware resources have been removed from a virtual PCI device: '%5'. Physical device LUID = %6, Virtual function LUID = %7. (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult', 'Parameter0', 'Parameter1', 'Parameter2')),
    (33107, 0): ("'%1': The guest operating system powered on a virtual PCI device: '%5'. (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult', 'Parameter0')),
    (33108, 0): ("'%1': The guest operating system powered off a virtual PCI device: '%5'. (Virtual machine ID %2)",
               ('VmName', 'VmId', 'ErrorCode', 'HResult', 'Parameter0')),
}
_NIC = {
    (12582, 0): ("'%1' %4 (%3) started successfully. (Virtual Machine ID %2)",
               ('VmName', 'VmId', 'NicGuid', 'NicName')),
    (12597, 0): ("'%1' %4 (%3) Connected to virtual network. (Virtual Machine ID %2)",
               ('VmName', 'VmId', 'NicGuid', 'NicName')),
}
_COMPUTE = {
    (1000, 0): ('The Host Compute Service is starting.',
               ()),
    (1001, 0): ('The Host Compute Service started successfully.',
               ()),
    (1002, 0): ('The Host Compute Service is shutting down.',
               ()),
    (1003, 0): ('The Host Compute Service shut down successfully.',
               ()),
    (2000, 0): ('[%1] Create compute system, result %2',
               ('SystemId', 'Result')),
    (2001, 0): ('[%1] Start compute system, result %2',
               ('SystemId', 'Result')),
    (2002, 0): ('[%1] Shut down compute system, result %2',
               ('SystemId', 'Result')),
    (2003, 0): ('[%1] Terminate compute system, result %2',
               ('SystemId', 'Result')),
    (2004, 0): ("[%1] Pause compute system, options '%3', result %2",
               ('SystemId', 'Result', 'Parameter0')),
    (2005, 0): ("[%1] Resume compute system, options '%3', result %2",
               ('SystemId', 'Result', 'Parameter0')),
    (2007, 0): ("[%1] Modify compute system, settings '%3', result %2",
               ('SystemId', 'Result', 'Parameter0')),
    (2010, 0): ("[%1] Create Container, type '%2', settings '%3'",
               ('SystemId', 'Parameter0', 'Parameter1')),
    (2011, 0): ('[%1] Create Container VM, VM ID %3, result %2',
               ('SystemId', 'Result', 'Parameter0')),
    (2012, 0): ("[%1] Create Container template VM, image path '%4', VP count %2, memory %3 MB",
               ('SystemId', 'Parameter0', 'Parameter1', 'Parameter2')),
    (2013, 0): ("[%1] Using template VM '%2'",
               ('SystemId', 'Parameter0')),
    (2014, 0): ('[%1] Create Virtual Machine',
               ('SystemId',)),
    (2015, 0): ("[%1] Add compute system resource, location '%3', resource '%4', result %2",
               ('SystemId', 'Result', 'Parameter0', 'Parameter1')),
    (2016, 0): ("[%1] Modify compute system resource, location '%3', resource '%4', result %2",
               ('SystemId', 'Result', 'Parameter0', 'Parameter1')),
    (2017, 0): ("[%1] Remove compute system, location '%3', result %2",
               ('SystemId', 'Result', 'Parameter0')),
    (2018, 0): ("[%1] Save compute system, options '%3', result %2",
               ('SystemId', 'Result', 'Parameter0')),
    (2019, 0): ("[%1] Crash compute system, options '%3', result %2",
               ('SystemId', 'Result', 'Parameter0')),
    (2500, 0): ("[%1] Create process, parameters '%4', result %2, process ID %3",
               ('SystemId', 'Result', 'Parameter0', 'Parameter1')),
    (2501, 0): ('[%1] Terminate process, process ID %3, result %2',
               ('SystemId', 'Result', 'Parameter0')),
    (10000, 0): ('The Host Compute Service failed to start:  %1 (%2)',
               ('ErrorMessage', 'ErrorCode')),
    (10004, 0): ("'%1' failed to start worker process: %3 (%4). (Virtual machine ID %2)",
               ('Parameter0', 'Parameter1', 'Parameter2', 'Parameter3')),
    (10005, 0): ('Failed to start worker process: %3 (%4). (Virtual machine ID %2)',
               ('Parameter0', 'Parameter1', 'Parameter2', 'Parameter3')),
    (10008, 0): ("The virtual machine '%1' with RAM size %3 MB failed to start due to insufficient memory. %4 MB of memory is currently available to Hyper-V to provide both memory and supporting services to starting virtual machines. (Virtual machine ID %2)",
               ('Parameter0', 'Parameter1', 'Parameter2', 'Parameter3')),
    (10009, 0): ("Failed to start the virtual machine '%1' (Virtual machine ID %2).",
               ('Parameter0', 'Parameter1')),
    (11008, 0): ("Cannot create system '%1' since Hyper-V is not installed on the host.",
               ('SystemId',)),
    (12000, 0): ("Failed to create the Virtual Machine for Hyper-V Container '%1': %2 (%3).",
               ('SystemId', 'ErrorMessage', 'ErrorCode')),
    (12001, 0): ("Cannot start Hyper-V Container '%1' since the hypervisor is not running in the host.",
               ('SystemId',)),
    (12002, 0): ("Failed to create the Virtual Machine for Hyper-V Container template '%1': %2 (%3).",
               ('SystemId', 'ErrorMessage', 'ErrorCode')),
    (12100, 0): ("Failed to create network endpoint for Container '%1': %2 (%3).",
               ('SystemId', 'ErrorMessage', 'ErrorCode')),
    (12101, 0): ("Failed to delete network endpoint for Container '%1', network endpoint ID '%4': %2 (%3).",
               ('SystemId', 'ErrorMessage', 'ErrorCode', 'Parameter0')),
    (12102, 0): ("Failed to attach network endpoint to Container '%1', network endpoint ID '%4': %2 (%3).",
               ('SystemId', 'ErrorMessage', 'ErrorCode', 'Parameter0')),
    (12103, 0): ("Failed to detach network endpoint from Container '%1', network endpoint ID '%4': %2 (%3).",
               ('SystemId', 'ErrorMessage', 'ErrorCode', 'Parameter0')),
    (12104, 0): ("Failed to query network endpoint properties for Container '%1', network endpoint ID '%4': %2 (%3).",
               ('SystemId', 'ErrorMessage', 'ErrorCode', 'Parameter0')),
    (12105, 0): ("Failed to create network adapter for Container '%1', network endpoint ID '%4': %2 (%3).",
               ('SystemId', 'ErrorMessage', 'ErrorCode', 'Parameter0')),
}
_SWITCH = {
    (9, 0): ('Switch %2 (Friendly Name: %4) successfully initialized.',
               ('SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName')),
    (21, 0): ('Media connected on NIC %2 (Friendly Name: %4).',
               ('NicNameLen', 'NicName', 'NicFNameLen', 'NicFName')),
    (23, 0): ('NIC %2 (Friendly Name: %4) is now operational.',
               ('NicNameLen', 'NicName', 'NicFNameLen', 'NicFName')),
    (24, 0): ('NIC %2 (Friendly Name: %4) is no longer operational.',
               ('NicNameLen', 'NicName', 'NicFNameLen', 'NicFName')),
    (32, 0): ('Failed to connect NIC %3 (Friendly Name: %5) to port %7 (Friendly Name: %9) on switch %11 (Friendly Name: %13), status = %1. UniqueEvent = %14.',
               ('Status', 'NicNameLen', 'NicName', 'NicFNameLen', 'NicFName', 'PortNameLen', 'PortName', 'PortFNameLen', 'PortFName', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName', 'UniqueEvent')),
    (34, 0): ('Failed to create port %3 (Friendly Name: %5) on switch %7 (Friendly Name: %9). The task was vetoed by a switch extension, or the switch extension stack is corrupted. Status = %1. UniqueEvent = %10.',
               ('Status', 'PortNameLen', 'PortName', 'PortFNameLen', 'PortFName', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName', 'UniqueEvent')),
    (35, 0): ('Failed to connect NIC %3 (Friendly Name: %5) to port %7 (Friendly Name: %9) on switch %11 (Friendly Name: %13). The task was vetoed by a switch extension, or the switch extension stack is corrupted. Status = %1.',
               ('Status', 'NicNameLen', 'NicName', 'NicFNameLen', 'NicFName', 'PortNameLen', 'PortName', 'PortFNameLen', 'PortFName', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName')),
    (62, 0): ('Switch %2 (Friendly Name: %4) successfully deleted.',
               ('SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName')),
    (63, 0): ('Failed to delete switch %3 (Friendly Name: %5), status = %1, UniqueEvent = %6.',
               ('Status', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName', 'UniqueEvent')),
    (64, 0): ('Switch %2 (Friendly Name: %4) info successfully set.',
               ('SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName')),
    (66, 0): ('Delete complete for Switch %2 (Friendly Name: %4).',
               ('SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName')),
    (67, 0): ('Port %2 (Friendly Name: %4) successfully created on switch %6 (Friendly Name: %8).',
               ('PortNameLen', 'PortName', 'PortFNameLen', 'PortFName', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName')),
    (68, 0): ('Failed to create port %3 (Friendly Name: %5) on switch %7 (Friendly Name: %9). Status = %1. UniqueEvent = %10.',
               ('Status', 'PortNameLen', 'PortName', 'PortFNameLen', 'PortFName', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName', 'UniqueEvent')),
    (69, 0): ('Port %2 (Friendly Name: %4) successfully deleted - switch %6 (Friendly Name: %8).',
               ('PortNameLen', 'PortName', 'PortFNameLen', 'PortFName', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName')),
    (70, 0): ('Failed to delete port %3 (Friendly Name: %5) on switch %7 (Friendly Name: %9). Status = %1.',
               ('Status', 'PortNameLen', 'PortName', 'PortFNameLen', 'PortFName', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName')),
    (71, 0): ('Delete complete for port %2 (Friendly Name: %4).',
               ('PortNameLen', 'PortName', 'PortFNameLen', 'PortFName')),
    (77, 0): ('Failed to disconnect NIC %3 (Friendly Name: %5), status = %1. UniqueEvent = %6.',
               ('Status', 'NicNameLen', 'NicName', 'NicFNameLen', 'NicFName', 'UniqueEvent')),
    (89, 0): ('Completed security policy operation on port %2 (Friendly Name: %4) on switch %6 (Friendly Name: %8) - AllowMacSpoofing: %9, EnableDhcpGuard: %10, EnableRouterGuard: %11, MonitorMode: %12, AllowIeeePriorityTag: %14, VirtualSubnetId: %15, AllowTeaming %16, StormLimit: %17, DynamicIPAddressLimit: %18, EnableFixSpeed10G: %19.',
               ('PortNameLen', 'PortName', 'PortFNameLen', 'PortFName', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName', 'AllowMacSpoofing', 'EnableDhcpGuard', 'EnableRouterGuard', 'MonitorMode', 'MonitorSession', 'AllowIeeePriorityTag', 'VirtualSubnetId', 'AllowTeaming', 'StormLimit', 'DynamicIPAddressLimit', 'EnableFixSpeed10G')),
    (124, 0): ('NIC %2 (Friendly Name: %4) restarted.',
               ('NicNameLen', 'NicName', 'NicFNameLen', 'NicFName')),
    (125, 0): ('Media connected on NIC %2 (Friendly Name: %4).',
               ('NicNameLen', 'NicName', 'NicFNameLen', 'NicFName')),
    (126, 0): ('Media disconnected on NIC %2 (Friendly Name: %4).',
               ('NicNameLen', 'NicName', 'NicFNameLen', 'NicFName')),
    (220, 0): ('Status change (%13) sent to Nic %2 (Friendly Name: %4) on port %6 (Friendly Name: %8) on switch %10 (Friendly Name: %12). NicStatus: %13, Status: %14',
               ('NicNameLen', 'NicName', 'NicFNameLen', 'NicFName', 'PortNameLen', 'PortName', 'PortFNameLen', 'PortFName', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName', 'NicStatus', 'Status')),
    (232, 0): ('NIC %2 (Friendly Name: %4) successfully connected to port %6 (Friendly Name: %8) on switch %10(Friendly Name: %12).',
               ('NicNameLen', 'NicName', 'NicFNameLen', 'NicFName', 'PortNameLen', 'PortName', 'PortFNameLen', 'PortFName', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName')),
    (234, 0): ('NIC %2 successfully disconnected from port %4.',
               ('NicNameLen', 'NicName', 'PortNameLen', 'PortName')),
    (235, 0): ('NIC %3 disconnect from port %5 failed. Status = %1, UniqueEvent = %6.',
               ('Status', 'NicNameLen', 'NicName', 'PortNameLen', 'PortName', 'UniqueEvent')),
    (264, 0): ('Internal or External Port %2 (Friendly Name: %4) successfully created on switch %6 (Friendly Name: %8).',
               ('PortNameLen', 'PortName', 'PortFNameLen', 'PortFName', 'SwitchNameLen', 'SwitchName', 'SwitchFNameLen', 'SwitchFName')),
}


__artifacts_v2__ = {
    "hyperVWorkerEvents": {
        "name": "Hyper-V Worker Events",
        "description": "Virtual machine events the Hyper-V worker process providers logged: a virtual machine "
                       "started, turned off, shut down, saved, reset, paused, resumed, restored or hibernated, its "
                       "faults and fatal errors, checkpoint events, virtual PCI devices added or offered, removed or "
                       "revoked, and powered on and off, and synthetic network adapters started and connected, with the virtual machine "
                       "name and ID each record holds.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-23",
        "last_update_date": "2026-10-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Hyper-V-Worker-Admin.evtx and "
                 "Microsoft-Windows-Hyper-V-Worker-Operational.evtx the paths match with python-evtx and reports, one "
                 "row per record, the records whose provider is Microsoft-Windows-Hyper-V-Worker and whose Event ID "
                 "is one of 18500, 18502, 18504, 18506 to 18508, 18510, 18512, 18514 to 18516, 18518, 18524, 18526, "
                 "18528, 18539, 18540, 18550, 18560, 18570 to 18573, 18580, 18590, 18592, 18594, 18596, 18598, 18600, "
                 "18602, 18604, 18606, 18608 to 18610 and 18617 (the virtual machine's state and its faults), 3210 to "
                 "3213, 3216, 3217, 3280, 3281, 3286, 3287, 3330 to 3333, 3352, 3353, 3370 to 3373, 3438, 3439, 3465, "
                 "26004 and 26005 (the events whose message names a checkpoint) and 33100 to 33108 (virtual PCI "
                 "devices), and the records whose provider is Microsoft-Windows-Hyper-V-SynthNic and whose Event ID "
                 "is 12582 or 12597 (a synthetic network adapter started, or connected to a virtual network). Event "
                 "messages and field names come from the provider's event manifest (its WEVT_TEMPLATE resource) and "
                 "English message table (its en-US .mui) in vmwpevents.dll for the Worker provider and VmSynthNic.dll "
                 "for SynthNic, the files the SOFTWARE hive's Microsoft\\Windows\\CurrentVersion\\WINEVT\\Publishers key "
                 "names for the provider, as read from the hexordia_mvs2025_win11 image (Windows 11 24H2 build "
                 "26100.2033; vmwpevents.dll 10.0.26100.1, VmSynthNic.dll 10.0.26100.1882) and compared with the "
                 "copies on the pc_mus_001_win11 image (Windows 11 22H2 build 22621; both 10.0.22621.1). The manifest "
                 "was read with the layout scripts/windows_messages.py follows (libyal's libfwevt description of the "
                 "format). No public copy of these manifests was found in nasbench's EVTX-ETW-Resources at commit "
                 "a3fa2bdbfd123907b8a10cfa87da9b3da0db2e74 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/tree/a3fa2bdbfd123907b8a10cfa87da9b3da0db2e74/ETWProvidersManifests): "
                 "it holds no manifest file named for Microsoft-Windows-Hyper-V-Worker, -SynthNic, -Compute or "
                 "-VmSwitch. It does hold Microsoft-Windows-Hyper-V-ComputeLib, a different provider. Other Windows "
                 "versions were not checked. The two builds give these events the same messages and fields except: "
                 "33103 reads 'offered to' in build 26100 and 'added to' in 22621, and 33104 'revoked from' and "
                 "'removed from'; version 1 of 18609 adds 'Physical address width: %9' in 26100; 18590 adds 'VTL %11' "
                 "and 18550 words its cause differently in 26100; 18617 is only in 26100. So a build 22621 record of "
                 "18609 version 1 has a Message ending 'Physical address width:' with nothing after it. Message is "
                 "the manifest's message for the record's Event ID and version, from the build 26100 copy, with each "
                 "insertion (%1, %2 and so on) replaced by the record's field that has the name the manifest's "
                 "template gives that position, read by name, and %n written as a space; a field the record does not "
                 "carry leaves its place blank, and a record whose Event ID and version are not in the table gets an "
                 "empty Message. Values are the text python-evtx renders for the field, with surrounding whitespace "
                 "removed; a UTF-16 string that does not decode is read with U+FFFD in place of what did not, and the "
                 "run log says so. VM Name and VM ID are the record's VmName and VmId; Provider is the record's "
                 "provider, which tells the SynthNic rows from the Worker ones. Not shown in a column: the ErrorCode "
                 "and HResult of 33100 to 33108 and the processor fields of 18609, except where the message inserts "
                 "them. Event Time (UTC) is the record's TimeCreated SystemTime, and Channel, Event Version, Record "
                 "ID and Computer are its Channel, Version, EventRecordID and Computer. Rows in the tested logs: on "
                 "hexordia_mvs2025_win11 40 (12582 2, 12597 2, 18500 2, 18508 2, 18609 2, and 6 each of 33100, 33103, "
                 "33104, 33107 and 33108); on pc_mus_001_win11 193 (12582 9, 12597 9, 18500 5, 18508 5, 18609 5, and "
                 "32 each of 33100, 33103, 33104, 33107 and 33108). On every tested row Channel held one value, "
                 "Microsoft-Windows-Hyper-V-Worker-Admin, and Computer one value per key; Event Version was 1 on "
                 "every 18609 row and 0 on the others. VM Name and VM ID are identical on all 40 rows of "
                 "hexordia_mvs2025_win11 and on 168 of the 193 of pc_mus_001_win11; on the other 25 VM Name holds a "
                 "name that is not a GUID. Which program created these virtual machines is not established here. For "
                 "every key whose logs were matched, the records per Event ID were also counted with a second reader, "
                 "the evtx crate's Python binding (pyevtx-rs, PyPI package evtx 0.13.1), and the rows match it record "
                 "for record by channel, Event ID, EventRecordID and time to the second, and field for field on VM "
                 "Name and VM ID. Not exercised on real data: every listed event other than 12582, 12597, 18500, "
                 "18508, 18609 version 1, 33100, 33103, 33104, 33107 and 33108; no tested Worker-Operational log "
                 "holds a record. A row shows what the provider logged; a start or shut down row does not show who "
                 "asked for it unless the message says so. Not read: the Worker provider's other events, among them "
                 "3086, a performance summary of a repository (8 records on hexordia_mvs2025_win11 and 20 on "
                 "pc_mus_001_win11), and Microsoft-Windows-Hyper-V-SynthStor 12148 in the same log (2 and 5 records), "
                 "whose manifest in vmsynthstor.dll gives no message text on either image, and no vmsynthstor.dll.mui "
                 "was found in Windows\\System32\\en-US on either. The Microsoft-Windows-Hyper-V-VMMS logs are not "
                 "read: none was found on the tested keys whose file lists were read, and no copy of that provider's "
                 "manifest was found (nasbench's EVTX-ETW-Resources at that commit holds none, and the file lists of "
                 "hexordia_mvs2025_win11 and pc_mus_001_win11 show no vmms.exe in Windows\\System32). The other "
                 "Microsoft-Windows-Hyper-V logs on the tested keys are not read either: Hypervisor-Admin and "
                 "-Operational, VID-Admin, Guest-Drivers%4Admin and Hierarchical-NIC-Switch%4Operational (VID-Admin "
                 "and Hierarchical-NIC-Switch held no records on the tested keys; the tested Hypervisor and "
                 "Guest-Drivers records carry fields such as LoadOptions, ProcessorFeatures, PartitionId and "
                 "MajorVersion and no VmName or VmId field); and StorageVSP-Admin, whose tested records are 300 and "
                 "301, which its manifest in storvsp.sys gives as an IO latency summary for the storage device its "
                 "DeviceName field names by file path (5 records on hexordia_mvs2025_win11 and 6 on "
                 "pc_mus_001_win11). For a log marked dirty, scripts/windows_evtx.py also reads the records of intact "
                 "chunks after the chunks its header counts, and the run log says how many records came from there; "
                 "on pc_mus_001_win11 the Worker-Admin log is marked dirty and 39 of its 193 rows come from a chunk "
                 "its header does not count. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-Hyper-V-Worker-Admin.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-Hyper-V-Worker-Operational.evtx'),
        "output_types": ["standard"],
        "artifact_icon": "monitor",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763.3046 | 0 rows (no member matches the declared paths)",
            "bitlocker_tpm_win11_states": "Windows 11 build 26200 (ARM64) | 0 rows (BitLocker volumes not unlocked, so not searched)",
            "bitlocker_win11_ntfs_xts128": "Windows 11 Pro build 26200 | 0 rows (BitLocker volumes not unlocked, so not searched)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "defender_evtx_attack_samples": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "defender_evtx_to_mitre": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "dhparser_detectionhistory_gpl": "Defender DetectionHistory samples | 0 rows (no member matches the declared paths)",
            "discord_win_ptb": "Synthetic Discord PTB layout (application folder only) | 0 rows (no member matches the declared paths)",
            "dleapp_slack_known": "Constructed Slack known-data fixture | 0 rows (no member matches the declared paths)",
            "evtx_attack_samples_sysmon_gpl": "193 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 (per the release asset name) | 0 rows (the matched logs hold no records)",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_mitre_attack_4688_cc0": "74 public Security logs | 0 rows (no member matches the declared paths)",
            "evtx_mitre_sysmon_cc0": "25 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100.2033 | 40 rows",
            "lonewolf_win10": "Windows 10 Education build 16299, version 1709 | 0 rows (no member matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348.1850 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 193 rows",
            "plaso_testdata_f951fc6": "12 plaso test files | 0 rows (no member matches the declared paths)",
            "roblox_windows": "Windows Roblox profile (application folder only) | 0 rows (no member matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "windows11_arm_4688_known": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_7zip_known_20261010": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_auditmap_20261010": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_cam_known_20261019": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no member matches the declared paths)",
            "windows11_arm_defender_eicar_known_20261018": "Windows 11 build 26200 (ARM64) | 0 rows (no member matches the declared paths)",
            "windows11_arm_eventtranscript_known_20261022": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_eventtranscript_known_20261023": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_parallels": "OS version not recorded | 0 rows (no member matches the declared paths)",
            "windows11_arm_pstranscript_known_20261022": "Windows 11 build 26200 (ARM64) | 0 rows (no member matches the declared paths)",
            "windows11_arm_smb_known_20261011": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "wire_win": "Wire desktop profile (application folder only) | 0 rows (no member matches the declared paths)",
        },
    },
    "hyperVComputeEvents": {
        "name": "Hyper-V Host Compute Service Events",
        "description": "Events of the Hyper-V Host Compute Service: the service starting and stopping, compute "
                       "systems (virtual machines and containers) created, started, shut down, terminated, paused, "
                       "resumed, modified, saved and removed with the result each logged, container and process "
                       "creation, and failures to start or create them, with the compute system ID each record holds.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-23",
        "last_update_date": "2026-10-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Hyper-V-Compute-Admin.evtx and "
                 "Microsoft-Windows-Hyper-V-Compute-Operational.evtx the paths match with python-evtx and reports, "
                 "one row per record, the records whose provider is Microsoft-Windows-Hyper-V-Compute and whose Event "
                 "ID is one of 1000 to 1003, 2000 to 2005, 2007, 2010 to 2019, 2500, 2501, 10000, 10004, 10005, "
                 "10008, 10009, 11008, 12000 to 12002 and 12100 to 12105. The manifest names the provider's service "
                 "the Host Compute Service and its objects compute systems; the words virtual machine and container "
                 "in the description come from its messages ('Create Virtual Machine', 'Create Container'). Event "
                 "messages and field names come from the provider's event manifest (its WEVT_TEMPLATE resource) and "
                 "English message table (its en-US .mui) in vmcomputeeventlog.dll, the file the SOFTWARE hive's "
                 "Microsoft\\Windows\\CurrentVersion\\WINEVT\\Publishers key names for the provider, as read from the "
                 "hexordia_mvs2025_win11 image (Windows 11 24H2 build 26100.2033; 10.0.26100.1) and compared with the "
                 "copies on the pc_mus_001_win11 image (Windows 11 22H2 build 22621; 10.0.22621.1). The manifest was "
                 "read with the layout scripts/windows_messages.py follows (libyal's libfwevt description of the "
                 "format). No public copy of these manifests was found in nasbench's EVTX-ETW-Resources at commit "
                 "a3fa2bdbfd123907b8a10cfa87da9b3da0db2e74 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/tree/a3fa2bdbfd123907b8a10cfa87da9b3da0db2e74/ETWProvidersManifests): "
                 "it holds no manifest file named for Microsoft-Windows-Hyper-V-Worker, -SynthNic, -Compute or "
                 "-VmSwitch. It does hold Microsoft-Windows-Hyper-V-ComputeLib, a different provider. Other Windows "
                 "versions were not checked. The two builds give these events the same messages and fields. Message "
                 "is the manifest's message for the record's Event ID and version, from the build 26100 copy, with "
                 "each insertion (%1, %2 and so on) replaced by the record's field that has the name the manifest's "
                 "template gives that position, read by name, and %n written as a space; a field the record does not "
                 "carry leaves its place blank, and a record whose Event ID and version are not in the table gets an "
                 "empty Message. Values are the text python-evtx renders for the field, with surrounding whitespace "
                 "removed; a UTF-16 string that does not decode is read with U+FFFD in place of what did not, and the "
                 "run log says so. Compute System ID is the record's SystemId, and Result its Result, as stored. "
                 "Microsoft's 'HCS Error Code' page "
                 "(https://learn.microsoft.com/en-us/virtualization/api/hcs/reference/hcshresult, ms.date 2021-06-09) "
                 "gives 0x80370102 as HCS_E_HYPERV_NOT_INSTALLED, 'The virtual machine could not be started because a "
                 "required feature is not installed'; 0xC0370103 is not in that table, and its meaning is not "
                 "established here, so a row holding it should not be read as a failure or a success. The settings of "
                 "2007 are a JSON document, inserted into Message as stored. Event Time (UTC) is the record's "
                 "TimeCreated SystemTime, and Channel, Event Version, Record ID and Computer are its Channel, "
                 "Version, EventRecordID and Computer. Rows in the tested logs: on hexordia_mvs2025_win11 28 (1000 1, "
                 "1001 1, 2000 2, 2001 2, 2007 20, 2014 2); on pc_mus_001_win11 59 (1000 2, 1001 2, 2000 5, 2001 5, "
                 "2007 40, 2014 5); on evtx_baseline_nextron_085_win11_client_2023 8 (1000 1, 1001 1, 2000 2, 2014 2, "
                 "11008 2). Result held 0xC0370103 on every 2000 and 2001 row of hexordia_mvs2025_win11 and "
                 "pc_mus_001_win11, 0x00000000 on every 2007 row, and 0x80370102 on the 2 rows of 2000 on "
                 "evtx_baseline_nextron_085_win11_client_2023; it is empty on 1000, 1001, 2014 and 11008, which carry "
                 "no Result. Compute System ID is empty on 1000 and 1001, which carry no SystemId. Event Version held "
                 "one value, 0, on every tested row, and Computer one value per key. For every key whose logs were "
                 "matched, the records per Event ID were also counted with a second reader, the evtx crate's Python "
                 "binding (pyevtx-rs, PyPI package evtx 0.13.1), and the rows match it record for record by channel, "
                 "Event ID, EventRecordID and time to the second, and field for field on Compute System ID and "
                 "Result. Not exercised on real data: 1002, 1003, 2002 to 2005, 2010 to 2013, 2015 to 2019, 2500, "
                 "2501 and the listed errors other than 11008. Not read: the provider's other events, among them 2008 "
                 "and 2009, a compute system notification queried and queued, whose notification numbers are not "
                 "sourced here (2008: 56 records on hexordia_mvs2025_win11 and 145 on pc_mus_001_win11; 2009: 30, 81, "
                 "and 2 on evtx_baseline_nextron_085_win11_client_2023), 2006 and 2021 (property queries), 2502 and "
                 "2503 (process notifications), and the dynamic memory, trace and settings validation events. For a "
                 "log marked dirty, scripts/windows_evtx.py also reads the records of intact chunks after the chunks "
                 "its header counts, and the run log says how many records came from there; on pc_mus_001_win11 the "
                 "Compute-Operational log is marked dirty and 11 of its 57 rows come from a chunk its header does not "
                 "count. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-Hyper-V-Compute-Admin.evtx',
                  '*/Windows/System32/winevt/Logs/Microsoft-Windows-Hyper-V-Compute-Operational.evtx'),
        "output_types": ["standard"],
        "artifact_icon": "box",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763.3046 | 0 rows (no member matches the declared paths)",
            "bitlocker_tpm_win11_states": "Windows 11 build 26200 (ARM64) | 0 rows (BitLocker volumes not unlocked, so not searched)",
            "bitlocker_win11_ntfs_xts128": "Windows 11 Pro build 26200 | 0 rows (BitLocker volumes not unlocked, so not searched)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "defender_evtx_attack_samples": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "defender_evtx_to_mitre": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "dhparser_detectionhistory_gpl": "Defender DetectionHistory samples | 0 rows (no member matches the declared paths)",
            "discord_win_ptb": "Synthetic Discord PTB layout (application folder only) | 0 rows (no member matches the declared paths)",
            "dleapp_slack_known": "Constructed Slack known-data fixture | 0 rows (no member matches the declared paths)",
            "evtx_attack_samples_sysmon_gpl": "193 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 (per the release asset name) | 8 rows",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_mitre_attack_4688_cc0": "74 public Security logs | 0 rows (no member matches the declared paths)",
            "evtx_mitre_sysmon_cc0": "25 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100.2033 | 28 rows",
            "lonewolf_win10": "Windows 10 Education build 16299, version 1709 | 0 rows (no member matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348.1850 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 59 rows",
            "plaso_testdata_f951fc6": "12 plaso test files | 0 rows (no member matches the declared paths)",
            "roblox_windows": "Windows Roblox profile (application folder only) | 0 rows (no member matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "windows11_arm_4688_known": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_7zip_known_20261010": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_auditmap_20261010": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_cam_known_20261019": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no member matches the declared paths)",
            "windows11_arm_defender_eicar_known_20261018": "Windows 11 build 26200 (ARM64) | 0 rows (no member matches the declared paths)",
            "windows11_arm_eventtranscript_known_20261022": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_eventtranscript_known_20261023": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_parallels": "OS version not recorded | 0 rows (no member matches the declared paths)",
            "windows11_arm_pstranscript_known_20261022": "Windows 11 build 26200 (ARM64) | 0 rows (no member matches the declared paths)",
            "windows11_arm_smb_known_20261011": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "wire_win": "Wire desktop profile (application folder only) | 0 rows (no member matches the declared paths)",
        },
    },
    "hyperVVmSwitchEvents": {
        "name": "Hyper-V Virtual Switch Events",
        "description": "Hyper-V virtual switch events: switches initialized, set and deleted, ports created and "
                       "deleted, network adapters connected to and disconnected from ports, media connected and "
                       "disconnected, adapters restarted and status changes sent to them, port security policy "
                       "operations, and the failures to create, delete, connect or disconnect them, with the switch, port and adapter "
                       "names each record holds.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-23",
        "last_update_date": "2026-10-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-Hyper-V-VmSwitch-Operational.evtx the paths match with python-evtx "
                 "and reports, one row per record, the records whose provider is Microsoft-Windows-Hyper-V-VmSwitch "
                 "and whose Event ID is one of 9, 21, 23, 24, 32, 34, 35, 62 to 64, 66 to 71, 77, 89, 124 to 126, "
                 "220, 232, 234, 235 and 264. Event messages and field names come from the provider's event manifest "
                 "(its WEVT_TEMPLATE resource) and English message table (its en-US .mui) in vmswitch.sys, the file "
                 "the SOFTWARE hive's Microsoft\\Windows\\CurrentVersion\\WINEVT\\Publishers key names for the provider, "
                 "as read from the hexordia_mvs2025_win11 image (Windows 11 24H2 build 26100.2033; 10.0.26100.2033) "
                 "and compared with the copies on the pc_mus_001_win11 image (Windows 11 22H2 build 22621; "
                 "10.0.22621.963). The manifest was read with the layout scripts/windows_messages.py follows "
                 "(libyal's libfwevt description of the format). No public copy of these manifests was found in "
                 "nasbench's EVTX-ETW-Resources at commit a3fa2bdbfd123907b8a10cfa87da9b3da0db2e74 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/tree/a3fa2bdbfd123907b8a10cfa87da9b3da0db2e74/ETWProvidersManifests): "
                 "it holds no manifest file named for Microsoft-Windows-Hyper-V-Worker, -SynthNic, -Compute or "
                 "-VmSwitch. It does hold Microsoft-Windows-Hyper-V-ComputeLib, a different provider. Other Windows "
                 "versions were not checked. The two builds give these events the same messages and fields except "
                 "264, which reads 'Internal or External Port' in build 26100 and 'Port' in 22621. Message is the "
                 "manifest's message for the record's Event ID and version, from the build 26100 copy, with each "
                 "insertion (%1, %2 and so on) replaced by the record's field that has the name the manifest's "
                 "template gives that position, read by name, and %n written as a space; a field the record does not "
                 "carry leaves its place blank, and a record whose Event ID and version are not in the table gets an "
                 "empty Message. Values are the text python-evtx renders for the field, with surrounding whitespace "
                 "removed; a UTF-16 string that does not decode is read with U+FFFD in place of what did not, and the "
                 "run log says so. Switch Friendly Name, Switch Name, Port Friendly Name, Port Name, NIC Friendly "
                 "Name and NIC Name are the record's SwitchFName, SwitchName, PortFName, PortName, NicFName and "
                 "NicName; a column whose field the event does not carry is blank. The length fields beside each name "
                 "are not shown, and the security policy values of 89 and the NicStatus and Status numbers of 220 "
                 "appear only in Message; what the numbers of 220 mean is not sourced here. Event Time (UTC) is the "
                 "record's TimeCreated SystemTime, and Channel, Event Version, Record ID and Computer are its "
                 "Channel, Version, EventRecordID and Computer. Rows in the tested logs: on hexordia_mvs2025_win11 "
                 "147 (66 1, 124 9, 125 5, 126 9, 220 123); on pc_mus_001_win11 250 (66 1, 67 17, 69 10, 71 10, 89 3, "
                 "124 5, 125 3, 126 1, 220 200). The Switch and Port columns were empty on 19 of the 123 rows of 220 "
                 "on hexordia_mvs2025_win11 and 12 of the 200 on pc_mus_001_win11, and the NIC columns on every row "
                 "of 66, 67, 69, 71 and 89. Channel and Event Version each held one value on every tested row, "
                 "Microsoft-Windows-Hyper-V-VmSwitch-Operational and 0, and Computer one value per key. For every key "
                 "whose logs were matched, the records per Event ID were also counted with a second reader, the evtx "
                 "crate's Python binding (pyevtx-rs, PyPI package evtx 0.13.1), and the rows match it record for "
                 "record by channel, Event ID, EventRecordID and time to the second, and field for field on the six "
                 "name columns. Not exercised on real data: 9, 21, 23, 24, 32, 34, 35, 62 to 64, 68, 70, 77, 232, "
                 "234, 235 and 264. Not read (counts from the evtx crate): Event ID 0, which the manifest in "
                 "vmswitch.sys defines on neither image (110 records on hexordia_mvs2025_win11, 500 on "
                 "pc_mus_001_win11, 42 on evtx_baseline_nextron_085_win11_client_2023 and 14 on "
                 "evtx_baseline_nextron_085_win2022_0_20348_azure), 285, an operation that took longer than expected "
                 "(183, 471 and 3), 143 and 148, the virtual RSS and Ndk Oid notices (22 and 392 on "
                 "hexordia_mvs2025_win11, 22 on pc_mus_001_win11), and the provider's other events. For a log marked "
                 "dirty, scripts/windows_evtx.py also reads the records of intact chunks after the chunks its header "
                 "counts, and the run log says how many records came from there; on pc_mus_001_win11 the log is "
                 "marked dirty and 105 of its 250 rows come from chunks its header does not count; one chunk after "
                 "them fails its checksums and is not read, and the evtx crate reads 35 records from it, 23 of 285 "
                 "and 12 of Event ID 0, none of them an event this artifact reports. Reading needs the python-evtx "
                 "package (pip install python-evtx).",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-Hyper-V-VmSwitch-Operational.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "share-2",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763.3046 | 0 rows (no member matches the declared paths)",
            "bitlocker_tpm_win11_states": "Windows 11 build 26200 (ARM64) | 0 rows (BitLocker volumes not unlocked, so not searched)",
            "bitlocker_win11_ntfs_xts128": "Windows 11 Pro build 26200 | 0 rows (BitLocker volumes not unlocked, so not searched)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "defender_evtx_attack_samples": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "defender_evtx_to_mitre": "One public Defender Operational log | 0 rows (no member matches the declared paths)",
            "dhparser_detectionhistory_gpl": "Defender DetectionHistory samples | 0 rows (no member matches the declared paths)",
            "discord_win_ptb": "Synthetic Discord PTB layout (application folder only) | 0 rows (no member matches the declared paths)",
            "dleapp_slack_known": "Constructed Slack known-data fixture | 0 rows (no member matches the declared paths)",
            "evtx_attack_samples_sysmon_gpl": "193 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win10_client": "Windows 10 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win11_client": "Windows 11 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win11_client_2023": "Windows 11 (per the release asset name) | 0 rows (the matched log holds no record of these events)",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "Windows Server 2022 build 20348 (per the release asset name) | 0 rows (the matched log holds no record of these events)",
            "evtx_baseline_nextron_085_win2022_ad": "Windows Server 2022 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win2022_evtx": "Windows Server 2022 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_baseline_nextron_085_win7_x86": "Windows 7 x86 (per the release asset name) | 0 rows (no member matches the declared paths)",
            "evtx_mitre_attack_4688_cc0": "74 public Security logs | 0 rows (no member matches the declared paths)",
            "evtx_mitre_sysmon_cc0": "25 public Sysmon logs | 0 rows (no member matches the declared paths)",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no member matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100.2033 | 147 rows",
            "lonewolf_win10": "Windows 10 Education build 16299, version 1709 | 0 rows (no member matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348.1850 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 250 rows",
            "plaso_testdata_f951fc6": "12 plaso test files | 0 rows (no member matches the declared paths)",
            "roblox_windows": "Windows Roblox profile (application folder only) | 0 rows (no member matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "windows11_arm_4688_known": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_7zip_known_20261010": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_auditmap_20261010": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_cam_known_20261019": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no member matches the declared paths)",
            "windows11_arm_defender_eicar_known_20261018": "Windows 11 build 26200 (ARM64) | 0 rows (no member matches the declared paths)",
            "windows11_arm_eventtranscript_known_20261022": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_eventtranscript_known_20261023": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_parallels": "OS version not recorded | 0 rows (no member matches the declared paths)",
            "windows11_arm_pstranscript_known_20261022": "Windows 11 build 26200 (ARM64) | 0 rows (no member matches the declared paths)",
            "windows11_arm_smb_known_20261011": "Windows 11 25H2 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 ARM64 (selected files) | 0 rows (no member matches the declared paths)",
            "wire_win": "Wire desktop profile (application folder only) | 0 rows (no member matches the declared paths)",
        },
    },
}

_INSERT = re.compile(r'%(\d+)|%[nrt]|%%')


def event_message(table, record):
    """The manifest message of the record's Event ID and version with each %n replaced by the record's field of that
    position's name in the template, read by name; '' when the table has no such event and version."""
    try:
        template, names = table[(int(record.event_id), int(record.version or 0))]
    except (KeyError, ValueError):
        return ''

    def insert(match):
        token = match.group(0)
        if token == '%%':
            return '%'
        if match.group(1) is None:
            return ' '
        index = int(match.group(1))
        return record.get(names[index - 1]) if index <= len(names) else ''

    return _INSERT.sub(insert, template).strip()


def _wanted(table):
    return {str(event_id) for event_id, _version in table}


def _read(context, label, logs, tables):
    """Rows' records of every log in `logs`, kept when (provider, Event ID) is in one of `tables`."""
    event_ids = set()
    for table in tables.values():
        event_ids |= _wanted(table)
    records = []
    sources = []
    for log in logs:
        found, read = read_event_records(context, log, label, event_ids=event_ids)
        for record in found:
            table = tables.get(record.provider)
            if table is not None and record.event_id in _wanted(table):
                records.append(record)
        sources.extend(read)
    return records, sources


_WORKER_TABLES = {_WORKER_PROVIDER: _WORKER, _NIC_PROVIDER: _NIC}


def worker_row(record):
    get = record.get
    return (record.time, record.event_id, event_message(_WORKER_TABLES[record.provider], record), get('VmName'),
            get('VmId'), record.provider, record.channel, record.version, record.record_id, record.computer)


def compute_row(record):
    get = record.get
    return (record.time, record.event_id, event_message(_COMPUTE, record), get('SystemId'), get('Result'),
            record.channel, record.version, record.record_id, record.computer)


def switch_row(record):
    get = record.get
    return (record.time, record.event_id, event_message(_SWITCH, record), get('SwitchFName'), get('SwitchName'),
            get('PortFName'), get('PortName'), get('NicFName'), get('NicName'), record.channel, record.version,
            record.record_id, record.computer)


@artifact_processor
def hyperVWorkerEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Message', 'VM Name', 'VM ID', 'Provider',
                    'Channel', 'Event Version', 'Record ID', 'Computer')
    records, sources = _read(context, 'Hyper-V Worker Events',
                             ('microsoft-windows-hyper-v-worker-admin.evtx',
                              'microsoft-windows-hyper-v-worker-operational.evtx'), _WORKER_TABLES)
    return data_headers, [worker_row(record) for record in records], '\n'.join(sources)


@artifact_processor
def hyperVComputeEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Message', 'Compute System ID', 'Result',
                    'Channel', 'Event Version', 'Record ID', 'Computer')
    records, sources = _read(context, 'Hyper-V Compute Events',
                             ('microsoft-windows-hyper-v-compute-admin.evtx',
                              'microsoft-windows-hyper-v-compute-operational.evtx'), {_COMPUTE_PROVIDER: _COMPUTE})
    return data_headers, [compute_row(record) for record in records], '\n'.join(sources)


@artifact_processor
def hyperVVmSwitchEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Message', 'Switch Friendly Name', 'Switch Name',
                    'Port Friendly Name', 'Port Name', 'NIC Friendly Name', 'NIC Name', 'Channel', 'Event Version',
                    'Record ID', 'Computer')
    records, sources = _read(context, 'Hyper-V Virtual Switch Events',
                             ('microsoft-windows-hyper-v-vmswitch-operational.evtx',), {_SWITCH_PROVIDER: _SWITCH})
    return data_headers, [switch_row(record) for record in records], '\n'.join(sources)

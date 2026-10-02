"""BitLocker event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads two sets of BitLocker records: every Microsoft-Windows-BitLocker-API record of the BitLocker Management event
log, and every Microsoft-Windows-BitLocker-Driver record of the System event log. The Event IDs, the message text
and the field names are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_MANAGEMENT_LABEL = 'BitLocker Management Events'
_DRIVER_LABEL = 'BitLocker Driver Events'
_MANAGEMENT_LOG = 'microsoft-windows-bitlocker%4bitlocker management.evtx'
_SYSTEM_LOG = 'system.evtx'
_API = 'Microsoft-Windows-BitLocker-API'
_DRIVER = 'Microsoft-Windows-BitLocker-Driver'

# The fields that have a column of their own, in column order; any other field goes to Other Fields.
_MANAGEMENT_SHOWN = ('VolumeMountPoint', 'VolumeName', 'IdentificationGUID', 'ProtectorGUID', 'ProtectorType',
                     'AlgorithmType', 'ErrorCode')
_DRIVER_SHOWN = ('Volume', 'ErrorCode', 'WritePhase', 'VolumeGUID', 'OptionalGUID', 'Flags')

# Event ID: the first sentence of the provider's message for it, placeholders as written (see notes).
_MANAGEMENT_EVENTS = {
    '768': 'BitLocker encryption was started for volume %3 using %4 algorithm.',
    '769': 'BitLocker encryption will occur for volume %3 when the computer is restarted using %4 algorithm.',
    '770': 'BitLocker decryption was started for volume %3.',
    '771': 'BitLocker encryption was stopped for volume %3.',
    '772': 'BitLocker encryption was restarted for volume %3 using %4 algorithm.',
    '773': 'BitLocker was suspended for volume %3.',
    '774': 'BitLocker was resumed for volume %3.',
    '775': 'A BitLocker key protector was created.',
    '776': 'A BitLocker key protector was removed.',
    '777': 'The PIN was updated for the operating system volume.',
    '778': 'The BitLocker volume %3 was reverted to an unprotected state.',
    '779': 'The BitLocker volume %3 was erased.',
    '780': 'The identification field was changed.',
    '781': 'The BitLocker protected volume %3 was locked.',
    '782': 'The BitLocker protected volume %3 was unlocked.',
    '783': ('BitLocker Drive Encryption recovery information for the specified protector is already present in '
            'Active Directory Domain Services.'),
    '784': ('BitLocker Drive Encryption recovery information was backed up successfully to Active Directory Domain '
            'Services.'),
    '785': 'Failed to backup BitLocker Drive Encryption recovery information to Active Directory Domain Services.',
    '786': 'BitLocker free space wiping was started for volume %3.',
    '787': 'BitLocker free space wiping was stopped for volume %3.',
    '788': 'BitLocker free space wiping was restarted for volume %3.',
    '789': 'The PIN was changed.',
    '790': 'A PIN change attempt failed.',
    '791': ('The BitLocker Service (BdeSvc) PIN and password change facility is locked out due to too many failed '
            'PIN or password change attempts.'),
    '792': 'BitLocker encountered a failure to commit metadata changes for volume %3.',
    '793': 'BitLocker resealed boot settings to the TPM for volume %3.',
    '794': 'BitLocker failed to reseal boot settings to the TPM.',
    '795': 'BitLocker failed to initialize hardware encryption for volume %3 due to group policy.',
    '796': 'BitLocker Drive Encryption is using software-based encryption to protect volume %3.',
    '797': ('Group Policy settings prevented BitLocker Drive Encryption from reverting to BitLocker software-based '
            'encryption.'),
    '798': 'BitLocker failed to initialize hardware encryption for volume %3.',
    '799': 'BitLocker failed to initialize hardware encryption for volume %3.',
    '800': 'BitLocker failed to initialize hardware encryption for volume %3.',
    '801': 'BitLocker failed to initialize hardware encryption for volume %3.',
    '802': 'BitLocker failed to initialize hardware encryption for volume %3.',
    '803': 'BitLocker failed to initialize hardware encryption for volume %3.',
    '804': ("The target drive (%3) cannot be managed by BitLocker because the drive's hardware encryption feature "
            'is already in use.'),
    '805': 'The BitLocker protected volume was unlocked in the Windows Recovery Environment.',
    '806': 'BitLocker resealed boot settings to the TPM in the Windows Recovery Environment.',
    '807': 'BitLocker free space wiping was canceled for volume %3.',
    '808': 'BitLocker failed to initialize hardware encryption for volume %3.',
    '809': 'BitLocker cannot use Secure Boot for integrity because it is disabled in Group Policy.',
    '810': 'BitLocker cannot use Secure Boot for integrity because it is disabled.',
    '811': "BitLocker cannot use Secure Boot for integrity because the required UEFI variable '%1' is not present.",
    '812': "BitLocker cannot use Secure Boot for integrity because the UEFI variable '%1' could not be read.",
    '813': ("BitLocker cannot use Secure Boot for integrity because the expected TCG Log entry for variable '%1' is "
            'missing or invalid.'),
    '814': ('BitLocker cannot use Secure Boot for integrity because the expected TCG Log entry for the OS Loader '
            'Authority is missing or invalid.'),
    '815': ('BitLocker cannot use Secure Boot for integrity because the expected TCG Log separator entry is missing '
            'or invalid.'),
    '816': 'BitLocker cannot use Secure Boot for integrity because the TCG Log for PCR [7] contains invalid entries.',
    '817': 'BitLocker successfully sealed a key to the TPM.',
    '818': 'BitLocker encountered a failure attempting to configure network unlock for volume %3.',
    '819': ('The BitLocker service could not resume protection on the OS volume %3, due to the following error: '
            'Bootable media in the drive.'),
    '820': ('The BitLocker service could not resume protection on the OS volume %3, due to the following error: TPM '
            'is locked out.'),
    '821': ('The BitLocker service could not resume protection on the OS volume %3, due to the following error: '
            'Group policy conflict.'),
    '822': ('The BitLocker service could not resume protection on the OS volume %3, due to the following error '
            'code: %4.'),
    '825': 'BitLocker failed to initialize hardware encryption for volume %3.',
    '826': 'The password was changed.',
    '827': 'A password change attempt failed.',
    '828': ('BitLocker Drive Encryption recovery information for volume %3 was backed up successfully to your '
            'Microsoft account.'),
    '829': ('Failed to backup BitLocker Drive Encryption recovery information for volume %3 to your Microsoft '
            'account.'),
    '830': 'The BitLocker Drive Encryption recovery information already exists in your Microsoft account.',
    '831': ('Failed to save BitLocker Drive Encryption recovery information to your Microsoft account due to an '
            'error.'),
    '832': 'TCG Log parsing failure.',
    '833': 'BitLocker detected that custom Secure Boot policy is installed, and will seal to this configuration.',
    '834': 'BitLocker determined that the TCG log is invalid for use of Secure Boot.',
    '835': ('BitLocker cannot use Secure Boot for integrity because the expected TCG Log entry for the OS Loader '
            'Authority has invalid structure.'),
    '836': ('BitLocker cannot use Secure Boot for integrity because the expected TCG Log entry for the OS Loader '
            'Authority is invalid.'),
    '837': ('BitLocker cannot use Secure Boot for integrity because the expected TCG Log entry for the OS Loader '
            'Authority is invalid.'),
    '838': ('BitLocker cannot use Secure Boot for integrity because the signature of the boot loader could not be '
            'validated as a Windows signature chained to a trusted Microsoft root certificate.'),
    '839': ('BitLocker cannot use Secure Boot for integrity because the TCG Log entry for the OS Loader Authority '
            'is invalid.'),
    '840': 'A trusted WIM file has been added for volume %3.',
    '841': 'BitLocker was unable to update a key for volume %3 due to the following error: %4',
    '842': 'BitLocker was unable to reseal boot settings to the TPM in the Windows Recovery Environment.',
    '843': 'BitLocker was suspended from within the Windows Recovery Environment.',
    '844': 'BitLocker was unable to recover from device lock in the Windows Recovery Environment.',
    '845': ('BitLocker Drive Encryption recovery information for volume %1 was backed up successfully to your Azure '
            'AD.'),
    '846': 'Failed to backup BitLocker Drive Encryption recovery information for volume %1 to your Azure AD.',
    '847': 'Failed to save BitLocker Drive Encryption recovery information to your Azure AD due to an error.',
    '848': 'Failed to update BCD store with the Recovery URL for OS volume.',
    '849': 'Failed to set the TPM dictionary attack parameters to the legacy behavior.',
    '850': 'Successfully set the TPM dictionary attack parameters to the legacy behavior.',
    '851': 'Failed to enable Silent Encryption.',
    '852': 'Failed to enable Silent Encryption.',
    '853': 'Failed to enable Silent Encryption.',
    '854': 'Failed to enable Silent Encryption.',
    '855': 'Recovery Password Rotation initiated.',
    '856': 'Failed to initiate the Recovery Password Rotation Error:%1.',
    '857': 'Recovery Passwords Rotation done successfully',
    '858': 'Recovery Password Rotation failed.',
    '863': 'Failed to initiate the Recovery Password Rotation and AAD Deletion requests processing Error:%1.',
    '864': 'Recovery Passwords Rotation and AAD Deletion requests processing initiated successfully',
    '865': ('BitLocker was unable to verify if TPM protector resealing is possible for volume %3 due to the '
            'following error: %4'),
    '866': 'A BitLocker key protector which uses PBKDF2 was created.',
    '867': 'Failed to delete BitLocker Drive Encryption recovery information for volume %1 from Azure AD.',
    '868': 'Failed while attempting to get BitLocker Drive Encryption recovery information from Azure AD.',
    '869': ('An operating system volume BitLocker recovery key password for the currently signed in user has not '
            'been backed up.'),
    '870': 'Failed to register information for reverted volume.',
    '871': 'Failed to register timer for recovery password cleanup.',
    '872': 'Failed to save request.',
    '873': 'Server reported a failure while attempting to backup a recovery password.',
    '874': 'Server reported a failure while attempting to delete recovery password(s) from AAD.',
    '875': 'Server reported a failure while attempting to retrieve recovery password information from AAD.',
    '876': 'Failed to delete BitLocker Drive Encryption recovery information from Azure AD.',
    '4096': 'Device Encryption could not be initialized.',
    '4099': 'Device Encryption failed to process user logon event.',
    '4102': 'BitLocker failed to recover after Device Lock.',
    '4103': 'Failed to automatically enable Device Encryption.',
    '4106': 'Failed to automatically back up recovery password to your Microsoft account.',
    '4111': 'Device Lock recovery event initiated for volume %3.',
    '4112': 'MaxPasswordRetry policy enforced with TPM-based hardening for volume %3.',
    '4113': 'MaxPasswordRetry policy enforced without hardware based hardening for volume %3.',
    '4114': 'Device Lock recovery event initiated due to protected state mismatch for volume %3.',
    '4122': ('The following DMA (Direct Memory Access) capable devices are not declared as protected from external '
             'access, which can block security features such as BitLocker automatic device encryption: %1'),
    '4123': ('BitLocker Drive Encryption recovery information for volume %1 was deleted successfully from your '
             'Azure AD.'),
    '4138': 'Successfully setup TPM API callback.',
    '4139': 'Failed to setup TPM API callback.',
    '4140': 'Successfully added predicted TPM protector.',
    '4141': 'Failed to add predicted TPM protector.',
    '4142': 'Predicted PCR4 value for TPM info based protector.',
    '4143': 'Failed to evaluate PCR4 predicted value from TPM info.',
    '4144': 'Predicted PCR7 value for TPM info based protector.',
    '4145': 'Failed to evaluate PCR7 predicted value from TPM info.',
}

_DRIVER_EVENTS = {
    '24577': 'Encryption of volume %2 started.',
    '24578': 'Encryption of volume %2 stopped.',
    '24579': 'Encryption of volume %2 completed.',
    '24580': 'Decryption of volume %2 started.',
    '24581': 'Decryption of volume %2 stopped.',
    '24582': 'Decryption of volume %2 completed.',
    '24583': 'Conversion worker thread for volume %2 was started.',
    '24584': 'Conversion worker thread for volume %2 was temporarily stopped.',
    '24585': 'Auto-unlock enabled for volume %2.',
    '24586': 'An error was encountered converting volume %2.',
    '24587': 'Auto-unlock disabled for volume %2.',
    '24588': 'The conversion operation on volume %2 encountered a bad sector error.',
    '24589': 'Failed to enable auto-unlock for volume %2.',
    '24590': 'Failed to disable auto-unlock for volume %2.',
    '24591': 'Auto-unlocking failed for volume %2.',
    '24592': 'An attempt to automatically restart conversion on volume %2 failed.',
    '24593': 'Metadata write: Volume %2 returning errors while trying to modify metadata.',
    '24594': ('Metadata rebuild: An attempt to write a copy of metadata on volume %2 failed and may appear as disk '
              'corruption.'),
    '24595': 'Volume %2 contains bad clusters.',
    '24596': 'No key file was found for Volume %2 during restart.',
    '24597': 'A corrupt key file was encountered for Volume %2 during restart.',
    '24598': 'No volume master key was retrieved in a key file during restart.',
    '24599': 'The TPM was not enabled during restart.',
    '24600': 'The SRK was found to be invalid during restart.',
    '24601': 'The PCRs did not match during restart.',
    '24602': 'No volume master key was retrieved from a key file during restart.',
    '24603': 'A boot application hash did not match expected value during restart.',
    '24604': 'The boot configuration options did not match expected values during restart.',
    '24605': 'No volume master key was retrieved from a PIN during restart.',
    '24606': 'No volume master key was retrieved from a recovery password during restart.',
    '24607': 'A valid key was found during the last restart.',
    '24608': 'An unexpected error was encountered attempting to retrieve the volume master key during restart.',
    '24609': 'A key was not available from required sources during restart.',
    '24610': 'Metadata commit: Not all copies of metadata on volume %2 could be written.',
    '24611': 'Metadata commit: No copies of metadata on volume %2 could be written.',
    '24612': 'Metadata commit: Metadata update could not be flushed.',
    '24613': 'Metadata commit: An attempt to verify metadata update on volume %2 failed at read.',
    '24614': 'Metadata commit: Update verification of metadata on volume %2 failed.',
    '24615': 'Metadata initial read: Primary metadata record on volume %2 could not be found.',
    '24616': 'Metadata initial read: Failover metadata record on volume %2 could not be found.',
    '24617': 'Metadata initial read: Failover metadata record on volume %2 used.',
    '24618': 'Metadata check: Metadata record on volume %2 could not be read and has been marked for rebuild.',
    '24619': ('Metadata rebuild: An attempt build a new set of metadata on %2 failed at commit and may appear as '
              'disk corruption.'),
    '24620': 'Encrypted volume check: Volume information on %2 cannot be read.',
    '24621': 'Initial state check: Rolling volume conversion transaction on %2.',
    '24622': 'BIOS/TCG Memory Overwrite Control: Error finding TPM driver.',
    '24623': 'BIOS/TCG Memory Overwrite Control: Error registering TPM device interface.',
    '24624': 'BIOS/TCG Memory Overwrite Control: Error changing value.',
    '24625': 'A valid BitLocker key was found during the last restart.',
    '24626': 'The auto-unlock master key was not available from the operating system volume.',
    '24627': 'Boot debugging is enabled on Bootmgr so TPM based keys cannot be obtained.',
    '24628': ('The partition size specified in the partition table is smaller than the size of the file system '
              'contained by that partition.'),
    '24629': 'The system firmware failed to enable overwriting of system memory on restart.',
    '24630': 'Bootmgr failed to find a BitLocker key file for Volume %2.',
    '24631': 'Bootmgr detected corruption in the BitLocker key file for Volume %2.',
    '24632': 'Bootmgr failed to obtain the BitLocker volume master key from the key file contents.',
    '24633': 'Bootmgr determined that the TPM is disabled.',
    '24634': 'Bootmgr determined that the authorization data for the SRK of the TPM is incompatible with BitLocker.',
    '24635': 'Bootmgr failed to obtain the BitLocker volume master key from the TPM because the PCRs did not match.',
    '24636': 'Bootmgr failed to obtain the BitLocker volume master key from the TPM.',
    '24637': 'A boot application hash did not match the expected value during restart.',
    '24638': 'Bootmgr failed to obtain the BitLocker volume master key from the TPM + PIN.',
    '24639': 'Bootmgr failed to obtain the BitLocker volume master key from the recovery password.',
    '24640': 'A valid BitLocker key was found during the last restart.',
    '24641': ('An unexpected error was encountered attempting to retrieve the BitLocker volume master key during '
              'restart.'),
    '24642': 'An internal BitLocker self-test failed for drive %2.',
    '24643': 'Bootmgr failed to obtain the BitLocker volume master key from the TPM + enhanced PIN.',
    '24644': 'An internal BitLocker self-test failed for drive %2 when switching from raw mode to filtering mode.',
    '24645': 'Bootmgr failed to obtain the BitLocker volume master key from the network key protector.',
    '24646': 'Encryption of the used space on volume %2 started.',
    '24647': 'Encryption of the used space on volume %2 stopped.',
    '24648': 'Encryption of the used space on volume %2 completed.',
    '24649': 'Wiping of free space on volume %2 started.',
    '24650': 'Wiping of free space on volume %2 stopped.',
    '24651': 'Wiping of free space on volume %2 completed.',
    '24652': 'A recovery password was used to start Windows.',
    '24653': 'Bootmgr failed to obtain the BitLocker volume master key from the password.',
    '24654': 'A recovery key was used to start Windows.',
    '24655': 'The BitLocker driver has started a self-healing operation on the metadata of volume %2.',
    '24656': 'The BitLocker driver has successfully completed a self-healing operation on the metadata of volume %2.',
    '24657': ('Bootmgr failed to obtain the BitLocker volume master key from the TPM because Secure Boot was '
              'disabled.'),
    '24658': ('Bootmgr failed to obtain the BitLocker volume master key from the TPM because Secure Boot '
              'configuration changed unexpectedly.'),
    '24659': 'Device Lock was triggered due to too many incorrect password attempts.',
    '24660': 'BitLocker encryption on write started for volume %2.',
    '24661': 'BitLocker free space sweep started for volume %2.',
    '24662': 'BitLocker free space sweep stopped for volume %2.',
    '24663': 'BitLocker free space sweep completed for volume %2.',
    '24664': 'BitLocker finalization sweep started for volume %2.',
    '24665': 'BitLocker finalization sweep paused for volume %2.',
    '24666': 'BitLocker finalization sweep resumed for volume %2.',
    '24667': 'BitLocker finalization sweep completed for volume %2.',
    '24668': 'BitLocker encryption on write failed for volume %2 due to disk I/O error.',
    '24669': 'BitLocker finalization sweep failed for volume %2 due to disk I/O error.',
    '24670': ('Disk containing volume %2 is employing non-volatile caching software which does not support control '
              'over its caching policies.'),
    '24671': 'Disk containing volume %2 is employing non-volatile caching software which is experiencing problems.',
    '24672': 'Device Lock was triggered due to Device Lockout state validation failure.',
    '24673': 'Drive %2 is no longer automatically managed by device encryption.',
    '24674': 'Drive %2 is now automatically managed by device encryption.',
    '24675': 'WIM hash generation paused for volume %2.',
    '24676': 'WIM hash generation resumed for volume %2.',
    '24677': 'WIM hash generation completed for volume %2.',
    '24678': 'WIM hash generation failed for volume %2.',
    '24679': 'WIM hashes will be deleted for volume %2.',
    '24680': 'Bootmgr failed to unseal VMK using the TPM',
    '24681': ('Bootmgr failed to obtain the BitLocker volume master key from the network key protector: failed to '
              'acquire protocol handle.'),
    '24682': ('Bootmgr failed to obtain the BitLocker volume master key from the network key protector: failed to '
              'get IP address.'),
    '24683': ('Bootmgr failed to obtain the BitLocker volume master key from the network key protector: failed to '
              'create request.'),
    '24684': ('Bootmgr failed to obtain the BitLocker volume master key from the network key protector: failed to '
              'send request.'),
    '24685': ('Bootmgr failed to obtain the BitLocker volume master key from the network key protector: invalid '
              'response.'),
    '24686': 'Bootmgr failed to obtain the BitLocker volume master key from the network boot protector.',
    '24687': ('BitLocker timed out attempting to enumerate bands during volume discovery on this hardware '
              'encrypting drive.'),
    '24688': 'Failed to read metadata from logical copy.',
    '24689': 'Attempted to read metadata from logical copy.',
    '24690': 'Attempted to fix metadata logical copies.',
    '24691': 'Failed to verify metadata logical copy against Primary.',
    '24692': 'Failed to verify metadata file against Primary copy.',
    '24693': 'Failed to register metadata check worker.',
    '24694': 'Metadata check worker started.',
    '24695': 'Metadata check worker completed.',
    '24696': 'Successfully created metadata file.',
    '24697': 'Failed to read a valid metadata copy.',
    '24698': 'Failed to fix metadata logical copy.',
    '24699': 'Attempted to check metadata logical copies.',
    '24700': 'Successfully fixed metadata logical copy.',
    '24701': 'Volume %2 has been excluded from device encryption by BitLocker Drive Encryption policy.',
    '24702': 'Read-only BitLocker Drive Encryption policy has been applied to volume %2.',
    '24703': ('Failed to determine whether volume %2 should be excluded from enforcement by BitLocker Drive '
              'Encryption policy.'),
}

__artifacts_v2__ = {
    "bitLockerManagementEvents": {
        "name": "BitLocker Management Events",
        "description": "Microsoft-Windows-BitLocker-API records of the BitLocker Management event log: what the "
                       "provider logged about BitLocker on the machine, such as encryption being started on a "
                       "volume, a key protector being created or a volume being unlocked, with the volume, the "
                       "protector and the user SID the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-BitLocker%4BitLocker Management.evtx the paths match with "
                 "python-evtx and reports, one row per record, every record whose provider is "
                 "Microsoft-Windows-BitLocker-API, whatever its Event ID. The provider's manifest gives that log's "
                 "channel the path Microsoft-Windows-BitLocker/BitLocker Management "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-API.xml#L19-L25) "
                 "and sends 122 events to it, among them 'BitLocker encryption was started for volume %3 using %4 "
                 "algorithm.' (768, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-API.xml#L370-L385), "
                 "'A BitLocker key protector was created. Protector GUID: %4 Identification GUID: %1' (775, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-API.xml#L478-L496), "
                 "'The identification field was changed. Identification GUID: %1' (780, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-API.xml#L564-L579), "
                 "'The BitLocker protected volume %3 was unlocked. Protector GUID: %4 Identification GUID: %1' (782, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-API.xml#L596-L614), "
                 "'BitLocker Drive Encryption is using software-based encryption to protect volume %3.' (796, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-API.xml#L811-L825), "
                 "'BitLocker cannot use Secure Boot for integrity because it is disabled.' (810, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-API.xml#L1038-L1047) "
                 "and 'The following DMA (Direct Memory Access) capable devices are not declared as protected from "
                 "external access, which can block security features such as BitLocker automatic device encryption: "
                 "%1' (4122, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-API.xml#L2390-L2405). "
                 "These are entries of the provider's manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository. Event is, for each of those 122 Event IDs, "
                 "the message's first sentence: the message with each run of white space made one space, cut after "
                 "the first period that a space or the end of the message follows, with its placeholders (such as %2 "
                 "or %3) as the manifest writes them. A placeholder is an insertion string for a data item of the "
                 "event's template by its position (Microsoft's Defining Events page: 'to include the third data "
                 "item in the template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in. Event is blank for an Event ID outside the 122, which no tested record had. "
                 "The manifests that repository publishes for Windows 10 builds 16299.15, 17763.107 and 19041.208 "
                 "send 90, 94 and 102 of the 122 events to the channel with the same first sentence, but for 768, "
                 "769 and 772 on build 16299.15, whose messages do not name an algorithm "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-BitLocker-API.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-BitLocker-API.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-BitLocker-API.xml). "
                 "Volume Mount Point, Volume Name, Identification GUID, Protector GUID, Protector Type (as stored), "
                 "Algorithm Type (as stored) and Error Code (as stored) are the fields VolumeMountPoint, VolumeName, "
                 "IdentificationGUID, ProtectorGUID, ProtectorType, AlgorithmType and ErrorCode, read by name. Each "
                 "value is as python-evtx renders it with any white space at either end removed, and a column whose "
                 "field the record does not carry is blank. Other Fields lists every other named field that holds "
                 "more than white space as 'name: value', in the record's order, joined with ' | '; a data item that "
                 "has no name is not shown, and no tested record had one. If a record named a field twice the last "
                 "would be read; no entry of the build 22621 manifest names a field twice. python-evtx renders a "
                 "GUID in braces "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1375-L1376), "
                 "a field the manifest types win:HexInt32, as it does ProtectorType, as 0x and eight hexadecimal "
                 "digits "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1481-L1486) "
                 "and a binary field as base64 "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1359-L1360; "
                 "no tested record held a binary field). 2 tested values had white space at an end, the "
                 "LocalizedText of the 2 rows of 4122. Protector Type (as stored) is a number whose meaning is not "
                 "established here: fveapi.dll, the provider's resource file, defines three value maps on the tested "
                 "images (AlgorithmTypeMap, TpmPcrBitmapMap and TpmPcrBitmapSourceMap; two on lonewolf_win10) and "
                 "none of them is for protector types. Microsoft's page for the GetKeyProtectorType method of "
                 "Win32_EncryptableVolume lists 3 as Numerical password and 8 as Passphrase "
                 "(https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/SecProv/getkeyprotectortype-win32-encryptablevolume.md?plain=1#L58-L68); "
                 "that the event field uses that method's numbers is not established by any source read. Algorithm "
                 "Type (as stored) is the number python-evtx renders in decimal. The manifest of build 18990 that "
                 "repnz's etw-providers-docs repository publishes defines a value map named AlgorithmTypeMap: 0x0 "
                 "default, 0x8000 AES-CBC 128 with Diffuser, 0x8001 AES-CBC 256 with Diffuser, 0x8002 AES-CBC 128, "
                 "0x8003 AES-CBC 256, 0x8004 XTS-AES 128, 0x8005 XTS-AES 256 and 0xffff unknown "
                 "(https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-18990/Microsoft-Windows-BitLocker-API.xml#L13-L22), "
                 "and binds it to the AlgorithmType field of the template of 768 "
                 "(https://github.com/repnz/etw-providers-docs/blob/d5f68e8acda5da154ab44e405b610dd8c2ba1164/Manifests-Win10-18990/Microsoft-Windows-BitLocker-API.xml#L227-L232). "
                 "The same eight entries were read from fveapi.dll and its en-US language file on af_case2_win10, "
                 "pc_mus_001_win11 and szechuan_win10; the fveapi.dll of lonewolf_win10 (build 16299) defines no "
                 "such map. 32772 is 0x8004. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "python-evtx renders from the FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. User SID "
                 "is the UserID of the record's Security element. Tested on the logs of three public images "
                 "(af_case2_win10, build 17763; pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which "
                 "gave 6, 25 and 2 rows in that order; lonewolf_win10 (build 16299) holds no such log. The rows are "
                 "1 each of 768, 780, 782 and 796 and 2 of 775 (af_case2_win10), 25 of 810 (pc_mus_001_win11) and 2 "
                 "of 4122 (szechuan_win10), each record version 0, and each tested record's field names were the "
                 "names the manifest lists for its event, in the manifest's order. The other 115 events are "
                 "unexercised: they are read by the field names the manifest lists, which no tested record confirms "
                 "for them. On af_case2_win10 the 6 rows are for one volume, Volume Mount Point E:, in this order: "
                 "796, then 775 twice, 108.9 and 111.0 seconds later (Protector Type (as stored) 0x00000008, then "
                 "0x00000003), then 780 and 768 at 125.2 seconds (Algorithm Type (as stored) 32772), then 782 at "
                 "320.9 seconds, whose Protector GUID is that of the 0x00000008 row. Identification GUID is all "
                 "zeros on the 796 row and one other value on the other 5. Volume Name held one value on those 6 "
                 "rows, \\\\?\\Volume{54aeb569-0000-0000-0000-010000000000}. The Mounted Devices artifact reports "
                 "\\DosDevices\\E: on that image as disk signature 54aeb569 offset 65536: the first eight hexadecimal "
                 "digits of the Volume Name are that signature, and its last sixteen, read as eight bytes least "
                 "significant first, are 65536. The BitLocker Driver Events artifact reports 10 rows for E: within "
                 "one second of the 768 row. User SID held one value on each tested log: one account SID (S-1-5-21 "
                 "and more) on the 6 rows of af_case2_win10 and S-1-5-18 on the 27 rows of the other two images. "
                 "Volume Mount Point, Volume Name, Identification GUID, Protector GUID, Protector Type (as stored) "
                 "and Algorithm Type (as stored) are blank on every row of pc_mus_001_win11 and szechuan_win10, "
                 "whose 810 and 4122 records carry none of those fields, and Event ID and Event held one value on "
                 "each of those two logs. Error Code (as stored) is blank on every tested row: no tested event "
                 "carries ErrorCode. Other Fields is blank on every row of af_case2_win10 and pc_mus_001_win11 and "
                 "held one value on szechuan_win10, the LocalizedText of 4122 (the %1 of its message). Computer held "
                 "one value on af_case2_win10 and on pc_mus_001_win11 and two on szechuan_win10. Rows are in the "
                 "order the log file holds its records, which was rising Record ID and time on every tested log. "
                 "Every record of the three tested logs rendered, and none was of another provider. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported. A log marked dirty is read past the chunks its header counts, and the run log says how "
                 "many records came from there. Reading needs the python-evtx package (pip install python-evtx). Not "
                 "read: the provider's events in other logs. Its manifest sends 21 events to the System channel, 8 "
                 "to Microsoft-Windows-BitLocker/BitLocker Operational and 27 to "
                 "Microsoft-Windows-BitLocker/Tracing; no System log of the four images, or of two captures of a "
                 "Windows 11 build 26200 machine, held a record of the provider. What makes the provider write an "
                 "810 or a 4122 record is not established here.",
        "paths": ('*/Windows/System32/winevt/Logs/Microsoft-Windows-BitLocker%4BitLocker Management.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "lock",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 6 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 25 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 2 rows",
        },
    },
    "bitLockerDriverEvents": {
        "name": "BitLocker Driver Events",
        "description": "Microsoft-Windows-BitLocker-Driver records of the System event log: what the BitLocker "
                       "driver logged for a volume, such as encryption on write being started or a finalization "
                       "sweep being started, paused or resumed, with the volume and the codes the record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every System.evtx the paths match with python-evtx and reports, one row per record, every "
                 "record whose provider is Microsoft-Windows-BitLocker-Driver, whatever its Event ID. The provider's "
                 "manifest sends all 127 of its events, 24577 to 24703, to the System channel "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-Driver.xml#L12-L18), "
                 "among them 'Decryption of volume %2 started.' (24580, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-Driver.xml#L90-L104), "
                 "'BitLocker encryption on write started for volume %2.' (24660, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-Driver.xml#L1400-L1414) "
                 "and 'BitLocker finalization sweep started for volume %2.' (24664), 'BitLocker finalization sweep "
                 "paused for volume %2.' (24665), 'BitLocker finalization sweep resumed for volume %2.' (24666) and "
                 "'BitLocker finalization sweep completed for volume %2.' (24667, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-BitLocker-Driver.xml#L1460-L1519). "
                 "These are entries of the provider's manifest as registered on Windows 11 build 22621.819, "
                 "published in nasbench's EVTX-ETW-Resources repository. Event is, for each of those 127 Event IDs, "
                 "the message's first sentence: the message with each run of white space made one space, cut after "
                 "the first period that a space or the end of the message follows, with its placeholders (such as %2 "
                 "or %3) as the manifest writes them. A placeholder is an insertion string for a data item of the "
                 "event's template by its position (Microsoft's Defining Events page: 'to include the third data "
                 "item in the template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in. Event is blank for an Event ID outside the 127, which no tested record had. "
                 "The manifests that repository publishes for Windows 10 builds 16299.15, 17763.107 and 19041.208 "
                 "hold 109, 109 and 110 of the 127 events, each with the same first sentence "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-BitLocker-Driver.xml, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-BitLocker-Driver.xml "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-BitLocker-Driver.xml). "
                 "Volume, Error Code (as stored), Write Phase (as stored), Volume GUID, Optional GUID and Flags (as "
                 "stored) are the fields Volume, ErrorCode, WritePhase, VolumeGUID, OptionalGUID and Flags, read by "
                 "name. Each value is as python-evtx renders it with any white space at either end removed, and a "
                 "column whose field the record does not carry is blank. Other Fields lists every other named field "
                 "that holds more than white space as 'name: value', in the record's order, joined with ' | '; a "
                 "data item that has no name is not shown, and no tested record had one. If a record named a field "
                 "twice the last would be read; no entry of the build 22621 manifest names a field twice. The "
                 "manifest types ErrorCode, WritePhase and Flags win:HexInt32, which python-evtx renders as 0x and "
                 "eight hexadecimal digits "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1481-L1486), "
                 "and VolumeGUID and OptionalGUID win:GUID, rendered in braces "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1375-L1376). "
                 "What a Write Phase (as stored) or Flags (as stored) number stands for is not sourced here. No "
                 "tested value had white space at either end. Event Time (UTC) is the record's TimeCreated "
                 "SystemTime, which python-evtx renders from the FILETIME the record stores, counted in UTC "
                 "(python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID and Computer the machine name the record stores. The "
                 "record's user is not reported; it was S-1-5-18 on every tested record. Tested on the System logs "
                 "of four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; pc_mus_001_win11, "
                 "build 22621; szechuan_win10, build 19041) and of two captures of a Windows 11 build 26200 machine, "
                 "which gave 10, 0, 0, 0, 130 and 130 rows in that order; every row of the first capture is a row of "
                 "the second. The 10 rows of af_case2_win10 are 1 of 24660, 2 of 24664, 4 of 24665, 2 of 24666 and 1 "
                 "of 24667; the 130 of each capture are 13 of 24660, 26 of 24664, 53 of 24665, 27 of 24666, 10 of "
                 "24667 and 1 of 24580. Each record is version 0 and carries the three fields the manifest lists for "
                 "its event, ErrorCode, Volume and WritePhase. The other 121 events are unexercised, every event "
                 "that carries VolumeGUID, OptionalGUID, Flags or a field without a column among them: Volume GUID, "
                 "Optional GUID, Flags (as stored) and Other Fields are blank on every tested row. Error Code (as "
                 "stored) held one value, 0x00000000, on every tested row, and so did Write Phase (as stored). "
                 "Volume held one value on each tested log, a drive letter and a colon (E: on af_case2_win10), and "
                 "Computer held one value on each. These records can come several at a time. On af_case2_win10 the "
                 "10 rows are for E: and lie within 0.2 seconds, in this order: 24664, 24665, 24666, 24665, 24660, "
                 "24666, 24664, 24665, 24665, 24667; all 10 are within one second of the one row the BitLocker "
                 "Management Events artifact reports for encryption being started on E: (768). What a finalization "
                 "sweep is, and how a 24667 row relates to the end of an encryption, is not sourced here. Rows are "
                 "in the order the log file holds its records, which was rising Record ID and time on every tested "
                 "log. Each capture's log held 72 records python-evtx could not render, which are not reported; "
                 "every record of the four images' logs rendered. A record python-evtx cannot render, or whose XML "
                 "does not parse, is counted in the run log and not reported. A log marked dirty is read past the "
                 "chunks its header counts, and the run log says how many records came from there. Reading needs the "
                 "python-evtx package (pip install python-evtx). Not read: Microsoft-Windows-BitLocker-API records, "
                 "which the BitLocker Management Events artifact reads from their own log; no tested System log held "
                 "one.",
        "paths": ('*/Windows/System32/winevt/Logs/System.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "lock",
        "sample_data": {
            "windows11_arm_4688_known": "Windows 11 build 26200 | 130 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 130 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 10 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
}


def other_fields(record, shown):
    """Every named field outside `shown` that holds a value, as 'name: value' joined with ' | '."""
    return ' | '.join(f'{name}: {record.get(name)}' for name in record.fields
                      if name not in shown and record.get(name))


def management_row(record):
    return (record.time, record.event_id, _MANAGEMENT_EVENTS.get(record.event_id, ''),
            *(record.get(name) for name in _MANAGEMENT_SHOWN), other_fields(record, _MANAGEMENT_SHOWN),
            record.user_sid, record.record_id, record.computer)


def driver_row(record):
    return (record.time, record.event_id, _DRIVER_EVENTS.get(record.event_id, ''),
            *(record.get(name) for name in _DRIVER_SHOWN), other_fields(record, _DRIVER_SHOWN),
            record.record_id, record.computer)


@artifact_processor
def bitLockerManagementEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Volume Mount Point', 'Volume Name',
                    'Identification GUID', 'Protector GUID', 'Protector Type (as stored)',
                    'Algorithm Type (as stored)', 'Error Code (as stored)', 'Other Fields', 'User SID', 'Record ID',
                    'Computer')
    records, sources = read_event_records(context, _MANAGEMENT_LOG, _MANAGEMENT_LABEL, provider=_API)
    data_list = [management_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def bitLockerDriverEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Volume', 'Error Code (as stored)',
                    'Write Phase (as stored)', 'Volume GUID', 'Optional GUID', 'Flags (as stored)', 'Other Fields',
                    'Record ID', 'Computer')
    records, sources = read_event_records(context, _SYSTEM_LOG, _DRIVER_LABEL, provider=_DRIVER)
    data_list = [driver_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)

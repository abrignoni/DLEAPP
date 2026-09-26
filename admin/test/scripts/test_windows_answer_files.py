"""Pin the setting rows of scripts/artifacts/windowsAnswerFiles.py."""
import pathlib
import sys
import unittest
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsAnswerFiles as answers  # pylint: disable=wrong-import-position

_XML = '''<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend" xmlns:cpi="urn:schemas-microsoft-com:cpi"
          xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
  <servicing></servicing>
  <settings pass="oobeSystem" wasPassProcessed="true">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64">
      <UserAccounts>
        <AdministratorPassword>*SENSITIVE*DATA*DELETED*</AdministratorPassword>
      </UserAccounts>
      <FirstLogonCommands>
        <SynchronousCommand wcm:action="add"><CommandLine>cmd /c one</CommandLine><Order>1</Order></SynchronousCommand>
        <SynchronousCommand wcm:action="add"><CommandLine>cmd /c two</CommandLine><Order>2</Order></SynchronousCommand>
      </FirstLogonCommands>
      <RegisteredOwner/>
    </component>
  </settings>
  <settings pass="specialize">
    <component name="Microsoft-Windows-Shell-Setup"><ComputerName>
        HOST01
      </ComputerName></component>
  </settings>
  <cpi:offlineImage cpi:source="wim:d:/sources/install.wim#Windows 10" />
</unattend>'''


class AnswerRowsTest(unittest.TestCase):
    def test_rows(self):
        rows = answers.answer_rows(ElementTree.fromstring(_XML.encode('utf-8')))
        self.assertEqual(rows, [
            ('oobeSystem', 'true', 'Microsoft-Windows-Shell-Setup', 'UserAccounts/AdministratorPassword',
             '*SENSITIVE*DATA*DELETED*'),
            ('oobeSystem', 'true', 'Microsoft-Windows-Shell-Setup',
             'FirstLogonCommands/SynchronousCommand[1]/CommandLine', 'cmd /c one'),
            ('oobeSystem', 'true', 'Microsoft-Windows-Shell-Setup',
             'FirstLogonCommands/SynchronousCommand[1]/Order', '1'),
            ('oobeSystem', 'true', 'Microsoft-Windows-Shell-Setup',
             'FirstLogonCommands/SynchronousCommand[2]/CommandLine', 'cmd /c two'),
            ('oobeSystem', 'true', 'Microsoft-Windows-Shell-Setup',
             'FirstLogonCommands/SynchronousCommand[2]/Order', '2'),
            ('oobeSystem', 'true', 'Microsoft-Windows-Shell-Setup', 'RegisteredOwner', ''),
            ('specialize', '', 'Microsoft-Windows-Shell-Setup', 'ComputerName', 'HOST01'),
            ('', '', '', 'offlineImage source', 'wim:d:/sources/install.wim#Windows 10'),
        ])


if __name__ == '__main__':
    unittest.main()

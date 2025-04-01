#!/usr/bin/env python3
"""
Create a test LBX file with multi-line text for testing the compact_multiline functionality.
"""

import os
import zipfile
import tempfile

# Sample XML with multi-line text
TEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<pt:document xmlns:pt="http://schemas.brother.info/ptouch/2007/lbx/main"
             xmlns:text="http://schemas.brother.info/ptouch/2007/lbx/text"
             xmlns:style="http://schemas.brother.info/ptouch/2007/lbx/style">
    <style:paper format="259" width="33.6pt" height="2834.4pt"
                 marginLeft="2.8pt" marginRight="2.8pt"
                 marginTop="0pt" marginBottom="0pt"
                 printerID="30256" printerName="Brother PT-P710BT" />
    <style:backGround x="5.6pt" y="2.8pt" width="56.2pt" height="28.0pt" />
    <text:text>
        <pt:objectStyle x="10pt" y="7.1pt" width="100pt" height="30pt" />
        <pt:data>First Line
Second Line
Third Line</pt:data>
        <text:textStyle orgPoint="8pt" spacing="0" spacingMagnification="100"/>
        <text:stringItem charLen="32">
            <text:ptFontInfo>
                <text:logFont name="Arial" width="0" italic="false" weight="400" charSet="0" pitchAndFamily="34" />
                <text:fontExt effect="NOEFFECT" underline="0" strikeout="0" size="8pt" orgSize="28.8pt"
                              textColor="#000000" textPrintColorNumber="1" />
            </text:ptFontInfo>
        </text:stringItem>
    </text:text>
</pt:document>
"""

def create_test_lbx(output_path="test_samples/test_multiline.lbx"):
    """Create a test LBX file with multi-line text."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the XML file
        xml_path = os.path.join(temp_dir, "label.xml")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(TEST_XML)

        # Create the LBX file (zip the XML)
        with zipfile.ZipFile(output_path, "w") as zipf:
            zipf.write(xml_path, arcname="label.xml")

    print(f"Created test LBX file with multi-line text at: {output_path}")
    return output_path

if __name__ == "__main__":
    lbx_path = create_test_lbx()
    print(f"Test both with and without compacting:")
    print(f"1. With compacting (default):")
    print(f"python change_lbx.py {lbx_path} test_samples/test_multiline_compact.lbx --text-tweaks --verbose")
    print(f"\n2. Without compacting:")
    print(f"python change_lbx.py {lbx_path} test_samples/test_multiline_nocompact.lbx --text-tweaks --no-compact --verbose")
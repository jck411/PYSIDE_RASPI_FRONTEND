#!/bin/bash
# Script to update PySide6 to the latest version and install required modules

echo "Updating PySide6 to the latest version (6.5+)..."

# Display current version
echo "Current PySide6 version:"
pip show PySide6 | grep Version

# Upgrade PySide6 to 6.5 or newer
pip install --upgrade "PySide6>=6.5.0"

# Install additional packages that might be needed for effects
pip install --upgrade PySide6-Addons PySide6-Essentials

# Check if QtQuick.Effects module is available
echo "Checking for QtQuick.Effects module..."
python3 -c "
import sys
try:
    import PySide6
    print(f'Upgraded to PySide6 version: {PySide6.__version__}')
    
    from PySide6.QtQml import QQmlApplicationEngine
    engine = QQmlApplicationEngine()
    
    print('QML import paths:')
    for path in engine.importPathList():
        print(f'  {path}')
    
    # Test specifically for MultiEffect
    print('Testing for MultiEffect...')
    from PySide6.QtCore import QUrl
    engine.load(QUrl.fromLocalFile('test_multieffect.qml'))
    
    if not engine.rootObjects():
        print('ERROR: MultiEffect not available in QtQuick.Effects')
    else:
        print('Success! MultiEffect is available')
        
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"

# Create a temporary QML file to test MultiEffect
cat > test_multieffect.qml << EOF
import QtQuick
import QtQuick.Controls
import QtQuick.Effects

Rectangle {
    width: 200
    height: 200
    
    MultiEffect {
        anchors.fill: parent
        source: parent
        blurEnabled: true
    }
}
EOF

echo ""
echo "Update complete. You may need to restart your application."
echo "If there were any errors, check that your PySide6 version is 6.5 or newer."
echo "For advanced blur effects, make sure QtQuick.Effects module is properly installed."
echo ""
echo "You can test blur with the following command:"
echo "  qt6-qml test_multieffect.qml" 
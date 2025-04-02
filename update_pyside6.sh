#!/bin/bash
# Script to verify PySide6 version and check for required modules

echo "Checking PySide6 version and QtQuick.Effects availability..."

# Display current version
echo "Current PySide6 version:"
pip show PySide6 | grep Version

# Check if PySide6 version is 6.5 or newer
python3 -c "
import sys
import PySide6

version = PySide6.__version__
print(f'Installed PySide6 version: {version}')
major, minor = map(int, version.split('.')[:2])

if major < 6 or (major == 6 and minor < 5):
    print('WARNING: Your PySide6 version is below 6.5.0')
    print('For blur effects, you need PySide6 6.5.0 or higher')
    print('To upgrade, run: pip install --upgrade \"PySide6>=6.5.0\"')
else:
    print('SUCCESS: Your PySide6 version supports QtQuick.Effects')
"

echo ""
echo "Checking for required PySide6 modules..."
python3 -c "
import sys
import os
try:
    # Check for required modules
    import PySide6.QtQml
    import PySide6.QtCore
    import PySide6.QtGui
    
    # Create application instance first
    from PySide6.QtGui import QGuiApplication
    app = QGuiApplication(sys.argv)
    
    # Get PySide6 location
    import PySide6
    pyside_path = os.path.dirname(PySide6.__file__)
    
    # Check for the Effects module directory
    effects_dir = os.path.join(pyside_path, 'Qt', 'qml', 'QtQuick', 'Effects')
    qmldir_file = os.path.join(effects_dir, 'qmldir')
    
    if os.path.exists(effects_dir) and os.path.exists(qmldir_file):
        print(f'FOUND: QtQuick.Effects module at {effects_dir}')
        
        # Check for MultiEffect in the qmldir file
        has_multieffect = False
        try:
            with open(qmldir_file, 'r') as f:
                content = f.read()
                if 'MultiEffect' in content:
                    has_multieffect = True
                    print('FOUND: MultiEffect is defined in the qmldir file')
        except:
            pass
            
        if not has_multieffect:
            print('WARNING: MultiEffect not found in qmldir file')
            print('This is strange since we confirmed the Effects module exists')
    else:
        print(f'WARNING: Could not find QtQuick.Effects module at {effects_dir}')
        print('You may need to install additional packages:')
        print('pip install --upgrade PySide6-Addons PySide6-Essentials')
        
    # Check for the plugin file
    plugin_file = os.path.join(effects_dir, 'libeffectsplugin.so')
    if os.path.exists(plugin_file):
        print(f'FOUND: Effects plugin at {plugin_file}')
    else:
        print(f'WARNING: Effects plugin not found at {plugin_file}')
        
    # Now let's create a test app using MultiEffect (this will validate if it actually works)
    print('\\nChecking if MultiEffect can be imported and used...')
    try:
        from PySide6.QtCore import QUrl, QByteArray
        from PySide6.QtQml import QQmlComponent, QQmlApplicationEngine
        
        engine = QQmlApplicationEngine()
        
        # Create a simple QML snippet that uses MultiEffect
        qml = b'''
        import QtQuick
        import QtQuick.Controls
        import QtQuick.Effects
        
        Rectangle {
            width: 100
            height: 100
            color: "#ff0000"
            
            MultiEffect {
                anchors.fill: parent
                source: parent
                blurEnabled: true
            }
        }
        '''
        
        # Create component with the QML
        component = QQmlComponent(engine)
        component.setData(QByteArray(qml), QUrl())
        
        # Try to create an object
        obj = component.create()
        if obj:
            print('SUCCESS: MultiEffect component was created successfully!')
        else:
            print('ERROR: Failed to create MultiEffect component')
            print('Error:', component.errorString())
            
    except Exception as e:
        print(f'ERROR testing MultiEffect: {e}')
        
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"

echo ""
echo "Diagnostic complete."
echo "If you need to upgrade PySide6, run: pip install --upgrade \"PySide6>=6.5.0\" PySide6-Addons PySide6-Essentials"
echo "For advanced blur effects, make sure QtQuick.Effects module is properly installed." 
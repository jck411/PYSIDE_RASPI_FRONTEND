#!/usr/bin/env python3
from frontend.settings_model import SettingsModel
from PySide6.QtCore import Qt

def main():
    model = SettingsModel()
    print('Categories:', len(model._categories))
    
    for i, cat in enumerate(model._categories):
        print(f'{i}. {cat._display_name} - Settings: {len(cat._settings)}')
        for j, s in enumerate(cat._settings):
            print(f'  {j}. {s._display_name} ({s._name})')
    
    # Print role names
    print("\nRole Names:")
    role_names = model.roleNames()
    for role_id, role_name in role_names.items():
        print(f"  {role_id}: {role_name.decode()}")
    
    # Print data for first item
    print("\nData for first category:")
    for role_id, role_name in role_names.items():
        data = model.data(model.index(0, 0), role_id)
        print(f"  {role_name.decode()}: {data}")

if __name__ == "__main__":
    main() 
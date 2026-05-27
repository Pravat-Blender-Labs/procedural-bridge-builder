"""
Procedural Bridge Builder Add-on for Blender.
This module initializes the add-on, handles the metadata, and registers 
the custom operators and keymaps with Blender's core system.
"""

bl_info = {
    "name": "Procedural Bridge Builder",
    "author": "Pravat-Blender-Labs",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D Viewport > Press Ctrl + Shift + M",
    "description": "Generates a mathematically precise, multi-material suspension bridge.",
    "warning": "",
    "doc_url": "https://github.com/Pravat-Blender-Labs/procedural-bridge-builder#readme",
    "tracker_url": "https://github.com/Pravat-Blender-Labs/procedural-bridge-builder/issues",
    "category": "Add Mesh",
}

import bpy
from .operator import MESH_OT_add_bridge

classes = [
    MESH_OT_add_bridge,
]

addon_keymaps = []

def register():
    """Registers classes and sets up the custom hotkey when the add-on is enabled."""
    for cls in classes:
        bpy.utils.register_class(cls)
        
    # Set up the Ctrl + Shift + M hotkey for the 3D Viewport
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(MESH_OT_add_bridge.bl_idname, type='M', value='PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))


def unregister():
    """Unregisters classes and removes the hotkey when the add-on is disabled."""
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    # Clean up the keymap to prevent memory leaks
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
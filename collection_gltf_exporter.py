bl_info = {
    "name": "GLTF Collection Exporter",
    "author": "Mythica",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "View3D > N-Panel > GLTF Export",
    "description": "Export collections as separate GLTF files with UI controls",
    "category": "Import-Export",
}

import bpy
import os
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, PointerProperty

# ===== PROPERTIES =====

class GLTF_Properties(PropertyGroup):
    export_path: StringProperty(
        name="Export Path",
        description="Custom export location (leave empty for default)",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
    )
    use_collection_structure: bpy.props.BoolProperty(
        name="Use Collection Structure",
        description="Create subfolders based on collection hierarchy",
        default=False
    )

# ===== UI PANEL =====

class GLTF_PT_collection_exporter(Panel):
    """Panel in the N-panel for GLTF Collection Export"""
    bl_label = "GLTF Collection Exporter"
    bl_idname = "GLTF_PT_collection_exporter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "GLTF Export"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        gltf_props = scene.gltf_export_props
        
        # Export path setting
        box = layout.box()
        box.label(text="Export Settings:", icon='FILEBROWSER')
        
        box.prop(gltf_props, "export_path", text="Export Path")
        box.prop(gltf_props, "use_collection_structure", text="Use Collection Folders")
        
        if gltf_props.export_path:
            box.label(text=f"Will export to: {gltf_props.export_path}", icon='CHECKMARK')
        else:
            box.label(text="Will use default location", icon='INFO')
        
        layout.separator()
        
        # Header with export button
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("gltf.export_collections", text="Export Enabled Collections", icon='EXPORT')
        
        layout.separator()
        
        # Quick actions
        row = layout.row(align=True)
        row.operator("gltf.enable_all_collections", text="Enable All", icon='CHECKMARK')
        row.operator("gltf.disable_all_collections", text="Disable All", icon='X')
        
        layout.separator()
        
        # Collection list
        box = layout.box()
        box.label(text="Collections:", icon='OUTLINER_COLLECTION')
        
        if len(bpy.data.collections) == 0:
            box.label(text="No collections found", icon='INFO')
        else:
            for collection in bpy.data.collections:
                row = box.row(align=True)
                
                # Toggle checkbox
                export_enabled = collection.get("export_gltf", False)
                
                # Create a custom operator for each collection
                props = row.operator("gltf.toggle_collection", 
                                   text="", 
                                   icon='CHECKBOX_HLT' if export_enabled else 'CHECKBOX_DEHLT')
                props.collection_name = collection.name
                
                # Collection name and object count
                row.label(text=f"{collection.name} ({len(collection.objects)} objects)")

# ===== OPERATORS =====

class GLTF_OT_export_collections(Operator):
    """Export all enabled collections as GLTF files"""
    bl_idname = "gltf.export_collections"
    bl_label = "Export Collections"
    bl_options = {'REGISTER'}

    def execute(self, context):
        # Get custom export path if set
        gltf_props = context.scene.gltf_export_props
        custom_path = gltf_props.export_path.strip() if gltf_props.export_path else None
        
        # Use custom path or default
        export_path = custom_path if custom_path else None
        
        export_collections_to_gltf(export_path)
        self.report({'INFO'}, "Collection export completed! Check console for details.")
        return {'FINISHED'}

class GLTF_OT_toggle_collection(Operator):
    """Toggle collection export status"""
    bl_idname = "gltf.toggle_collection"
    bl_label = "Toggle Collection Export"
    bl_options = {'REGISTER'}
    
    collection_name: StringProperty()

    def execute(self, context):
        if self.collection_name in bpy.data.collections:
            collection = bpy.data.collections[self.collection_name]
            current_status = collection.get("export_gltf", False)
            collection["export_gltf"] = not current_status
            
            status = "enabled" if not current_status else "disabled"
            self.report({'INFO'}, f"Collection '{self.collection_name}' export {status}")
        else:
            self.report({'ERROR'}, f"Collection '{self.collection_name}' not found")
        
        return {'FINISHED'}

class GLTF_OT_enable_all_collections(Operator):
    """Enable all collections for export"""
    bl_idname = "gltf.enable_all_collections"
    bl_label = "Enable All Collections"
    bl_options = {'REGISTER'}

    def execute(self, context):
        enable_all_collections_for_export()
        self.report({'INFO'}, f"Enabled {len(bpy.data.collections)} collections for export")
        return {'FINISHED'}

class GLTF_OT_disable_all_collections(Operator):
    """Disable all collections for export"""
    bl_idname = "gltf.disable_all_collections"
    bl_label = "Disable All Collections"
    bl_options = {'REGISTER'}

    def execute(self, context):
        disable_all_collections_for_export()
        self.report({'INFO'}, f"Disabled {len(bpy.data.collections)} collections for export")
        return {'FINISHED'}

# ===== ADDON LIFECYCLE =====

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register the property group
    bpy.types.Scene.gltf_export_props = PointerProperty(type=GLTF_Properties)
    
    print("GLTF Collection Exporter: Addon registered successfully!")

def unregister():
    # Unregister the property group
    del bpy.types.Scene.gltf_export_props
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("GLTF Collection Exporter: Addon unregistered")

# Only auto-register if running as script (not as addon)
if __name__ == "__main__":
    # First unregister in case script was run before
    try:
        unregister()
    except:
        pass
    
    # Register the UI classes
    register()
    print("Running as script - UI registered. Check the N-panel under 'GLTF Export' tab.")

def toggle_collection_export(collection_name, enabled=True):
    """
    Enable or disable a collection for GLTF export.
    
    Args:
        collection_name (str): Name of the collection
        enabled (bool): True to enable export, False to disable
    """
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        collection["export_gltf"] = enabled
        status = "enabled" if enabled else "disabled"
        print(f"Collection '{collection_name}' export {status}")
    else:
        print(f"Collection '{collection_name}' not found")

def enable_all_collections_for_export():
    """Enable all collections for export."""
    for collection in bpy.data.collections:
        collection["export_gltf"] = True
    print(f"Enabled {len(bpy.data.collections)} collections for export")

def disable_all_collections_for_export():
    """Disable all collections for export."""
    for collection in bpy.data.collections:
        collection["export_gltf"] = False
    print(f"Disabled {len(bpy.data.collections)} collections for export")

def get_collection_hierarchy_path(collection):
    """
    Get the folder path based on collection hierarchy.
    Returns a list of parent collection names from root to the collection's parent.
    """
    hierarchy = []
    
    # Find all parent collections by checking which collections contain this one
    def find_parents(target_collection, current_path=[]):
        for parent_collection in bpy.data.collections:
            if target_collection.name in [child.name for child in parent_collection.children]:
                new_path = current_path + [parent_collection.name]
                # Check if this parent has its own parent
                parent_found = False
                for grandparent in bpy.data.collections:
                    if parent_collection.name in [child.name for child in grandparent.children]:
                        parent_found = True
                        break
                
                if parent_found:
                    return find_parents(parent_collection, new_path)
                else:
                    return new_path
        return current_path
    
    return find_parents(collection)
    """Print the export status of all collections."""
    print("\n=== Collection Export Status ===")
    for collection in bpy.data.collections:
        status = "✓" if collection.get("export_gltf", False) else "✗"
        print(f"{status} {collection.name}")
    print("================================\n")

def export_collections_to_gltf(export_path=None):
    """
    Export each collection as a separate GLTF file.
    Only exports collections that have the 'export_gltf' custom property set to True.
    """
    
    # Get the use_collection_structure setting
    use_structure = bpy.context.scene.gltf_export_props.use_collection_structure
    
    # Set export path - defaults to blend file directory or desktop
    if export_path is None:
        if bpy.data.filepath:
            export_path = os.path.dirname(bpy.data.filepath)
        else:
            export_path = os.path.expanduser("~/Desktop")
    
    # Store original selection, active object, and mode
    original_selection = bpy.context.selected_objects.copy()
    original_active = bpy.context.active_object
    original_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'
    
    # Switch to object mode if not already there
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        print(f"Switched from {original_mode} mode to OBJECT mode for export")
    
    # Clear current selection
    bpy.ops.object.select_all(action='DESELECT')
    
    exported_count = 0
    
    # Loop through all collections in the scene
    for collection in bpy.data.collections:
        # Check if this collection is marked for export
        export_enabled = collection.get("export_gltf", False)
        
        if not export_enabled:
            print(f"Skipping collection (export disabled): {collection.name}")
            continue
            
        # Skip empty collections
        if not collection.objects:
            print(f"Skipping empty collection: {collection.name}")
            continue
            
        # Clear selection
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select all objects in this collection
        objects_in_collection = []
        for obj in collection.objects:
            # Only select if object is in the current scene
            if obj.name in bpy.context.scene.objects:
                obj.select_set(True)
                objects_in_collection.append(obj)
        
        # Skip if no valid objects found
        if not objects_in_collection:
            print(f"No valid objects in collection: {collection.name}")
            continue
            
        # Set one of the objects as active (required for export)
        bpy.context.view_layer.objects.active = objects_in_collection[0]
        
        # Determine the export directory
        final_export_path = export_path
        
        if use_structure:
            # Get the collection hierarchy
            hierarchy = get_collection_hierarchy_path(collection)
            if hierarchy:
                # Reverse the hierarchy so it goes from root to parent
                hierarchy.reverse()
                # Create subfolder path
                subfolder_path = os.path.join(*hierarchy)
                final_export_path = os.path.join(export_path, subfolder_path)
                
                # Create the directory if it doesn't exist
                os.makedirs(final_export_path, exist_ok=True)
                print(f"Created/using folder structure: {subfolder_path}")
        
        # Create filename using only the collection name
        safe_collection_name = "".join(c for c in collection.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        filename = f"{safe_collection_name}.gltf"
        filepath = os.path.join(final_export_path, filename)
        
        # Export selected objects as GLTF
        try:
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                use_selection=True,  # Only export selected objects
                export_apply=True    # Apply modifiers before export
            )
            print(f"Exported collection '{collection.name}' to: {filepath}")
            exported_count += 1
            
        except Exception as e:
            print(f"Failed to export collection '{collection.name}': {str(e)}")
    
    # Restore original selection, active object, and mode
    bpy.ops.object.select_all(action='DESELECT')
    for obj in original_selection:
        if obj.name in bpy.context.scene.objects:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = original_active
    
    # Restore original mode if we changed it
    if original_active and original_mode != 'OBJECT':
        try:
            bpy.ops.object.mode_set(mode=original_mode)
            print(f"Restored to {original_mode} mode")
        except:
            print(f"Could not restore to {original_mode} mode, staying in OBJECT mode")
    
    structure_note = " (with folder structure)" if use_structure else ""
    print(f"\nExport complete! {exported_count} collections exported to: {export_path}{structure_note}")

# ===== REGISTRATION =====

classes = [
    GLTF_Properties,
    GLTF_PT_collection_exporter,
    GLTF_OT_export_collections,
    GLTF_OT_toggle_collection,
    GLTF_OT_enable_all_collections,
    GLTF_OT_disable_all_collections,
]

# ===== HELPER FUNCTIONS =====
bl_info = {
    "name" : "Voxelizer",
    "author": "Santiago Alvarez de Araya",
    "version": (1,0,0),
    "blender" : (4, 2, 0),
    "location" : "3D Viewport > Sidebar > Voxelizer Category",
    "description" : "Turns voxelization of both animated and static meshes into the click of a single button",
    "category" : "Development",
}

#Give python access to blender's functionality
import bpy

from bpy.utils import resource_path
from pathlib import Path

USER = Path(resource_path("USER"))
src = USER / "scripts" / "addons" / "Voxelizer"

file_path = src / "VoxelizationNodes.blend"
inner_path = "NodeTree"

def voxelizeStaticAsset():
        '''
        For static meshes
        -----------------------------
        Create one collection, static
        Add prefix to selected object of static_
        Place object in collection
        
        Add geometry node modifier to object and give it the voxelize asset
        Make duplicate of Voxelize asset and name it Voxelize_ObjectName
        Within Voxelize_ObjectName asset
            provide the static mesh node with a value
            provide the UVmap node with the name of the UVMap variable
            provide the material node with the material
        '''
        
        active_object = bpy.context.active_object
        active_object.name = "Static_" + active_object.name
        
        static_collection_name = active_object.name + "_Collection"
        static_collection = bpy.data.collections.get(static_collection_name)
        if not static_collection:
            static_collection = bpy.data.collections.new(static_collection_name)
            bpy.context.scene.collection.children.link(static_collection)
        
        for collection in list(active_object.users_collection):
            collection.objects.unlink(active_object)
            
        static_collection.objects.link(active_object)
        
        geometry_node = active_object.modifiers.new(name = "Voxelize", type = "NODES")
        node_group = geometry_node.node_group
        node_group = bpy.data.node_groups.get("Voxelize_Static")
        
        node_group = node_group.copy()
        node_group.name = "Voxelize_" + active_object.name
        geometry_node.node_group = node_group
        
        identifier = geometry_node.node_group.interface.items_tree["UVMap"].identifier
        geometry_node[identifier] = active_object.data.uv_layers.active.name
        
        identifier = geometry_node.node_group.interface.items_tree["Material"].identifier
        geometry_node[identifier] = active_object.active_material
        
def voxelizeAnimatedAsset():
    '''
    For animated meshes
    -----------------------------
    Create two collections, static and animated
    Grab the entire heirarchy and apply transformations
    Duplicate selected object and add prefixes to each, static_ and animated_
    Place each object in their corresponding collections
    Add geometry node modifier to animated object and give it the voxelize asset
    Make duplicate of Voxelize asset and name it Voxelize_ObjectName
    Within Voxelize_ObjectName asset
        provide the static mesh node with a value
        provide the UVmap node with the name of the UVMap variable
        provide the material node with the material
        provide the animated bool with a value
    '''
    pass

    static_collection_name = "Static_" + bpy.context.active_object.name + "_Collection"
    animated_collection_name = "Animated_" + bpy.context.active_object.name + "_Collection"
    
    static_collection = bpy.data.collections.get(static_collection_name)
    if not static_collection:
        static_collection = bpy.data.collections.new(static_collection_name)
        bpy.context.scene.collection.children.link(static_collection)
    
    animated_collection = bpy.data.collections.get(animated_collection_name)
    if not animated_collection:
        animated_collection = bpy.data.collections.new(animated_collection_name)
        bpy.context.scene.collection.children.link(animated_collection)
        
    animated_object = bpy.context.active_object
    bpy.ops.object.select_grouped(type = "PARENT")
    bpy.ops.object.transform_apply(location = False, rotation = True, scale = False)
    bpy.ops.object.select_all(action = "DESELECT")
    animated_object.select_set(True)
    bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)

    static_object = animated_object.copy()
    static_object.data = animated_object.data.copy()
    bpy.context.collection.objects.link(static_object)
    static_object.modifiers.remove(static_object.modifiers["Armature"])
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = static_object
    static_object.select_set(True)
    bpy.ops.object.parent_clear(type = "CLEAR_KEEP_TRANSFORM")
    
    animated_object.name = "Animated_" + animated_object.name
    static_object.name = "Static_" + static_object.name
    
    for collection in list(animated_object.users_collection):
        collection.objects.unlink(animated_object)
        
    animated_collection.objects.link(animated_object)
    
    for collection in list(static_object.users_collection):
        collection.objects.unlink(static_object)
        
    static_collection.objects.link(static_object)
    
    geometry_node = animated_object.modifiers.new(name = "Voxelize", type = "NODES")
    node_group = geometry_node.node_group
    node_group = bpy.data.node_groups.get("Voxelize")

    node_group = node_group.copy()
    node_group.name = "Voxelize_" + animated_object.name
    geometry_node.node_group = node_group

    identifier = geometry_node.node_group.interface.items_tree["Static Mesh"].identifier
    geometry_node[identifier] = static_object
    identifier = geometry_node.node_group.interface.items_tree["UVMap"].identifier
    geometry_node[identifier] = animated_object.data.uv_layers.active.name
    identifier = geometry_node.node_group.interface.items_tree["Material"].identifier
    geometry_node[identifier] = animated_object.active_material
    identifier = geometry_node.node_group.interface.items_tree["Animated"].identifier
    geometry_node[identifier] = True
    
class VoxelizerProperties(bpy.types.PropertyGroup):
    is_animated: bpy.props.BoolProperty(
        name = "Skinned?",
        description = "Does your model have a skeleton or armature?",
        default = False
    )

class OBJECT_OT_voxelize(bpy.types.Operator):
    """Creates a duplicate copy of the selected asset, adds the 
    geometry node modifier to it, and provides the modifier with
    the voxelizer asset"""
    
    bl_idname = "object.voxelize"
    bl_label = "Voxelize Selected Object"
    bl_options = {"REGISTER", "UNDO"}
    
    def execute(self, context):

         # First Object
        if "Voxelize" not in bpy.data.node_groups:
            object_name = "Voxelize"
            filepath = str(file_path / inner_path / object_name)
            directory = str(file_path / inner_path)

            bpy.ops.wm.append(
                filepath=filepath,
                directory=directory,
                filename=object_name
            )

        # Second Object
        if "Voxelize_Static" not in bpy.data.node_groups:
            object_name = "Voxelize_Static"
            filepath = str(file_path / inner_path / object_name)
            directory = str(file_path / inner_path)

            bpy.ops.wm.append(
                filepath=filepath,
                directory=directory,
                filename=object_name
            )
        
        if bpy.context.scene.voxelizer_properties.is_animated:
            voxelizeAnimatedAsset()
        else:
            voxelizeStaticAsset()
        
        return {"FINISHED"}

class VIEW3D_PT_voxelizer_panel(bpy.types.Panel):

    #Where to add panel in the UI
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    #Add Labels
    bl_category = "Voxelizer"
    bl_label = "Voxelizer"

    #Define the layout of the panel
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("object.voxelize", text = "Voxelize")
        row.enabled = context.active_object is not None
        
        props = context.scene.voxelizer_properties
        layout.prop(props,"is_animated")
        
#Register the panel with blender
def register():
    bpy.utils.register_class(VoxelizerProperties)
    bpy.types.Scene.voxelizer_properties = bpy.props.PointerProperty(type = VoxelizerProperties)
    bpy.utils.register_class(VIEW3D_PT_voxelizer_panel)
    bpy.utils.register_class(OBJECT_OT_voxelize)
    
def unregister():
    bpy.utils.unregister_class(VoxelizerProperties)
    del bpy.types.Scene.voxelizer_properties
    bpy.utils.unregister_class(VIEW3D_PT_voxelizer_panel)
    bpy.utils.unregister_class(OBJECT_OT_voxelize)
        
if __name__ == "__main__":
    register()
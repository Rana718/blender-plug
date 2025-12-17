bl_info = {
    "name": "Mosaic Effect",
    "author": "Custom",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "Render Properties",
    "description": "Apply mosaic/pixelation effect to renders",
    "category": "Render",
}

import bpy
from bpy.props import IntProperty, BoolProperty
from bpy.types import Panel, PropertyGroup, Operator

class MosaicProperties(PropertyGroup):
    enabled: BoolProperty(
        name="Enable Mosaic Effect",
        description="Apply mosaic effect to renders",
        default=False
    )
    pixel_size: IntProperty(
        name="Pixel Size",
        description="Downscale factor (higher = bigger pixels)",
        default=8,
        min=2,
        max=50
    )

def update_compositor(context):
    scene = context.scene
    props = scene.mosaic_props
    
    # Enable compositing
    scene.render.use_compositing = True
    
    # Create or get compositor node group
    if not scene.compositing_node_group:
        tree = bpy.data.node_groups.new(name="MosaicCompositor", type='CompositorNodeTree')
        scene.compositing_node_group = tree
    else:
        tree = scene.compositing_node_group
    
    # Clear existing nodes and interface
    tree.nodes.clear()
    tree.interface.clear()
    
    # Add Render Layers input
    render_layers = tree.nodes.new('CompositorNodeRLayers')
    render_layers.location = (0, 0)
    
    # Add Group Output
    output = tree.nodes.new('NodeGroupOutput')
    
    # Create output socket
    tree.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    
    if not props.enabled:
        output.location = (200, 0)
        tree.links.new(render_layers.outputs['Image'], output.inputs[0])
        return
    
    # Add Pixelate node
    pixelate = tree.nodes.new('CompositorNodePixelate')
    pixelate.location = (200, 0)
    pixelate.inputs['Size'].default_value = props.pixel_size
    
    output.location = (400, 0)
    
    # Link nodes
    tree.links.new(render_layers.outputs['Image'], pixelate.inputs['Color'])
    tree.links.new(pixelate.outputs['Color'], output.inputs[0])
    
    # Switch UI to show compositor
    for area in context.screen.areas:
        if area.type == 'NODE_EDITOR':
            area.spaces.active.tree_type = 'CompositorNodeTree'
            area.spaces.active.node_tree = tree
            break

class MOSAIC_OT_apply(Operator):
    bl_idname = "mosaic.apply"
    bl_label = "Apply Mosaic"
    bl_description = "Apply mosaic effect to compositor"
    
    def execute(self, context):
        update_compositor(context)
        props = context.scene.mosaic_props
        if props.enabled:
            self.report({'INFO'}, f"Mosaic applied: {props.pixel_size}x downscale")
        else:
            self.report({'INFO'}, "Mosaic disabled")
        return {'FINISHED'}

class MOSAIC_PT_render_panel(Panel):
    bl_label = "Mosaic Effect"
    bl_idname = "MOSAIC_PT_render_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    def draw_header(self, context):
        self.layout.prop(context.scene.mosaic_props, "enabled", text="")
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.mosaic_props
        scene = context.scene
        
        layout.enabled = props.enabled
        layout.prop(props, "pixel_size")
        layout.operator("mosaic.apply", icon='FILE_REFRESH')
        
        # Show status
        box = layout.box()
        box.label(text=f"Compositing: {'ON' if scene.render.use_compositing else 'OFF'}")
        if props.enabled:
            res_x = scene.render.resolution_x // props.pixel_size
            res_y = scene.render.resolution_y // props.pixel_size
            box.label(text=f"Reduced: {res_x}x{res_y} px")

def register():
    bpy.utils.register_class(MosaicProperties)
    bpy.utils.register_class(MOSAIC_OT_apply)
    bpy.utils.register_class(MOSAIC_PT_render_panel)
    bpy.types.Scene.mosaic_props = bpy.props.PointerProperty(type=MosaicProperties)

def unregister():
    del bpy.types.Scene.mosaic_props
    bpy.utils.unregister_class(MOSAIC_PT_render_panel)
    bpy.utils.unregister_class(MOSAIC_OT_apply)
    bpy.utils.unregister_class(MosaicProperties)

if __name__ == "__main__":
    register()

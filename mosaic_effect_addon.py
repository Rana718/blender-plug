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
from bpy.types import Panel, PropertyGroup
from bpy.app.handlers import persistent

class MosaicProperties(PropertyGroup):
    enabled: BoolProperty(
        name="Enable Mosaic Effect",
        description="Apply mosaic effect to renders",
        default=False,
        update=lambda self, context: update_compositor(context)
    )
    pixel_size: IntProperty(
        name="Pixel Size",
        description="Size of mosaic blocks (lower = bigger pixels)",
        default=20,
        min=2,
        max=200,
        update=lambda self, context: update_compositor(context)
    )

def update_compositor(context):
    scene = context.scene
    props = scene.mosaic_props
    
    # Enable compositing
    scene.use_nodes = True
    scene.render.use_compositing = True
    
    # Wait for node tree to be created
    if not hasattr(scene, 'node_tree') or scene.node_tree is None:
        # Force creation by toggling
        scene.use_nodes = False
        scene.use_nodes = True
    
    if not hasattr(scene, 'node_tree') or scene.node_tree is None:
        print("ERROR: Cannot access compositor node tree")
        return
    
    tree = scene.node_tree
    
    if not props.enabled:
        # Remove mosaic nodes
        tree.nodes.clear()
        render_layers = tree.nodes.new('CompositorNodeRLayers')
        composite = tree.nodes.new('CompositorNodeComposite')
        tree.links.new(render_layers.outputs['Image'], composite.inputs['Image'])
        return
    
    # Clear and rebuild
    tree.nodes.clear()
    
    render_layers = tree.nodes.new('CompositorNodeRLayers')
    render_layers.location = (0, 0)
    
    # Get render resolution
    render_x = scene.render.resolution_x
    render_y = scene.render.resolution_y
    
    # Calculate reduced dimensions (fewer pixels = bigger blocks)
    new_x = max(1, render_x // props.pixel_size)
    new_y = max(1, render_y // props.pixel_size)
    
    # Scale down to reduced resolution
    scale_down = tree.nodes.new('CompositorNodeScale')
    scale_down.location = (200, 0)
    scale_down.space = 'ABSOLUTE'
    scale_down.inputs['X'].default_value = new_x
    scale_down.inputs['Y'].default_value = new_y
    
    # Scale back up to original size (creates blocky pixels)
    scale_up = tree.nodes.new('CompositorNodeScale')
    scale_up.location = (400, 0)
    scale_up.space = 'ABSOLUTE'
    scale_up.inputs['X'].default_value = render_x
    scale_up.inputs['Y'].default_value = render_y
    
    composite = tree.nodes.new('CompositorNodeComposite')
    composite.location = (600, 0)
    
    tree.links.new(render_layers.outputs['Image'], scale_down.inputs[0])
    tree.links.new(scale_down.outputs[0], scale_up.inputs[0])
    tree.links.new(scale_up.outputs[0], composite.inputs[0])

@persistent
def setup_on_render(scene):
    if scene.mosaic_props.enabled:
        update_compositor(bpy.context)

class MOSAIC_OT_apply(bpy.types.Operator):
    bl_idname = "mosaic.apply"
    bl_label = "Apply Now"
    bl_description = "Manually apply mosaic effect to compositor"
    
    def execute(self, context):
        update_compositor(context)
        self.report({'INFO'}, "Mosaic effect applied to compositor")
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
        
        layout.enabled = props.enabled
        layout.prop(props, "pixel_size")
        layout.operator("mosaic.apply", icon='CHECKMARK')

classes = (
    MosaicProperties,
    MOSAIC_OT_apply,
    MOSAIC_PT_render_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mosaic_props = bpy.props.PointerProperty(type=MosaicProperties)
    bpy.app.handlers.render_pre.append(setup_on_render)

def unregister():
    if setup_on_render in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.remove(setup_on_render)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.mosaic_props

if __name__ == "__main__":
    register()

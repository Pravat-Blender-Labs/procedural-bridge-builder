"""
Core operator logic for the Procedural Bridge Builder.
Utilizes Blender's BMesh API to dynamically generate vertices, edges, and faces
based on user-defined properties in the Redo Panel.
"""

import bpy
import bmesh
import mathutils
from math import sqrt, atan2 
from bpy.props import IntProperty, FloatProperty, FloatVectorProperty 

class MESH_OT_add_bridge(bpy.types.Operator):
    """
    Operator that generates a multi-component procedural suspension bridge.
    Includes real-time UI updates via the 'REGISTER' and 'UNDO' bl_options.
    """
    bl_idname = "mesh.add_procedural_bridge"
    bl_label = "Add Procedural Bridge"
    bl_options = {'REGISTER', 'UNDO'} 
    
    # -------------------------------------------------------------------------
    # USER INTERFACE PROPERTIES
    # These automatically draw in the bottom-left Redo Panel
    # -------------------------------------------------------------------------
    bridge_length: FloatProperty(name="Length", default=40.0, min=10.0, max=200.0)
    bridge_width: FloatProperty(name="Width", default=4.0, min=1.0, max=20.0)
    pillar_count: IntProperty(name="Deck Pillars", default=6, min=2, max=20)
    rail_post_count: IntProperty(name="Rail Posts", default=25, min=3, max=100)
    rail_height: FloatProperty(name="Rail Height", default=1.2, min=0.5, max=3.0)
    tower_height: FloatProperty(name="Tower Height", default=15.0, min=5.0, max=50.0)
    
    custom_paint_color: FloatVectorProperty(
        name="Paint Color",
        subtype='COLOR',
        size=4,
        default=(0.7, 0.15, 0.05, 1.0), 
        min=0.0, max=1.0
    )
    
    def execute(self, context):
        """Main execution function that builds the mesh and applies materials."""
        # Cache properties for cleaner math later
        length, width, pillars = self.bridge_length, self.bridge_width, self.pillar_count
        posts, r_height, t_height = self.rail_post_count, self.rail_height, self.tower_height
        
        # Initialize Mesh Data and Object Container
        mesh = bpy.data.meshes.new("Golden_Gate_Mesh")
        obj = bpy.data.objects.new("ProceduralGoldenGate", mesh)
        context.collection.objects.link(obj)
        
        bm = bmesh.new()
        
        def paint_cube(index):
            """Assigns the specified material index to the last 6 faces added to BMesh."""
            for face in bm.faces[-6:]:
                face.material_index = index

        # -------------------------------------------------------------------------
        # COMPONENT GENERATION (BMESH)
        # -------------------------------------------------------------------------

        # 1. THE DECK (Index 0: Asphalt)
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=bm.verts[-8:], vec=(width, length, 0.5))
        paint_cube(0) 
        
        # 2. THE DECK PILLARS (Index 1: Painted Metal)
        start_y = -(length / 2)
        for i in range(pillars):
            bmesh.ops.create_cube(bm, size=1.0)
            verts = bm.verts[-8:]
            bmesh.ops.scale(bm, verts=verts, vec=(width * 0.8, 1.0, 4.0))
            bmesh.ops.translate(bm, verts=verts, vec=(0, start_y + (i * (length / (pillars - 1))), -2.0))
            paint_cube(1) 

        # 3. THE HANDRAILS (Index 1: Painted Metal)
        for side_x in [-(width / 2) + 0.1, (width / 2) - 0.1]:
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, verts=bm.verts[-8:], vec=(0.1, length, 0.1))
            bmesh.ops.translate(bm, verts=bm.verts[-8:], vec=(side_x, 0, r_height))
            paint_cube(1) 

        # 4. THE MAIN TOWERS (Index 1: Painted Metal)
        for ty in [start_y, -start_y]:
            for tx in [-(width/2), (width/2)]:
                bmesh.ops.create_cube(bm, size=1.0)
                verts = bm.verts[-8:]
                bmesh.ops.scale(bm, verts=verts, vec=(0.8, 1.2, t_height + 2.0))
                bmesh.ops.translate(bm, verts=verts, vec=(tx, ty, (t_height - 2.0) / 2))
                paint_cube(1) 

        # 5. SUSPENSION CABLES (Index 2: Steel)
        # Parabola Math: z = a * y^2
        a = t_height / ((length / 2) ** 2)
        for i in range(posts):
            current_y = start_y + (i * (length / (posts - 1)))
            cable_z = (a * (current_y ** 2)) + r_height
            
            # Vertical drop-cables from arch to deck
            for tx in [-(width/2) + 0.1, (width/2) - 0.1]:
                bmesh.ops.create_cube(bm, size=1.0)
                verts = bm.verts[-8:]
                bmesh.ops.scale(bm, verts=verts, vec=(0.05, 0.05, cable_z))
                bmesh.ops.translate(bm, verts=verts, vec=(tx, current_y, cable_z / 2))
                paint_cube(2) 
                
            # Arching Main Cable (Connects the dots using trigonometry)
            if i > 0:
                prev_y = start_y + ((i-1) * (length / (posts - 1)))
                prev_z = (a * (prev_y ** 2)) + r_height
                dist = sqrt((current_y - prev_y)**2 + (cable_z - prev_z)**2)
                angle = atan2(cable_z - prev_z, current_y - prev_y)
                
                for tx in [-(width/2) + 0.1, (width/2) - 0.1]:
                    bmesh.ops.create_cube(bm, size=1.0)
                    verts = bm.verts[-8:]
                    bmesh.ops.scale(bm, verts=verts, vec=(0.15, dist, 0.15))
                    bmesh.ops.transform(bm, matrix=mathutils.Matrix.Rotation(angle, 4, 'X'), verts=verts)
                    bmesh.ops.translate(bm, verts=verts, vec=(tx, (prev_y + current_y) / 2, (prev_z + cable_z) / 2))
                    paint_cube(2) 

        # Finalize geometry
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        
        # -------------------------------------------------------------------------
        # MATERIAL ASSIGNMENT & SHADER SETUP
        # -------------------------------------------------------------------------
        
        def get_or_create_node_mat(name, color):
            """Fetches an existing material or creates a new node-based material."""
            mat = bpy.data.materials.get(name)
            if mat is None:
                mat = bpy.data.materials.new(name=name)
            
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            
            if bsdf:
                bsdf.inputs[0].default_value = color 
            mat.diffuse_color = color                
            
            return mat

        # Define materials
        mat_deck = get_or_create_node_mat("Bridge_Asphalt", (0.15, 0.15, 0.15, 1.0))
        mat_paint = get_or_create_node_mat("Bridge_Paint", self.custom_paint_color)
        mat_cable = get_or_create_node_mat("Bridge_Cables", (0.8, 0.8, 0.8, 1.0))
        
        # [CRITICAL] Append order matches BMesh face.material_index exactly
        obj.data.materials.append(mat_deck)  # Index 0
        obj.data.materials.append(mat_paint) # Index 1
        obj.data.materials.append(mat_cable) # Index 2
        
        bpy.ops.object.shade_smooth()
        
        return {'FINISHED'}
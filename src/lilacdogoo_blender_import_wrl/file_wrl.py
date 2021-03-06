"""
Author: LilacDogoo

This adds an 'Import from RIP menu item' in the 'import' menu in Blender.
This also hold all the capabilities of reading NinjaRipper [RIP] files into a 'PreBlender_Model' object.

This script was written by me (LilacDogoo).
"""
from typing import List, TextIO, BinaryIO

import os
import time
import random

import bpy
import bmesh

import lilacdogoo_blender_import_wrl


class BlenderOperator_wrl_import(bpy.types.Operator):
    bl_idname = "import_scene.wrl"
    bl_label = "N64 VRML Importer"
    bl_description = "Import Models from Nemu64 vrml dumps."
    bl_options = {'UNDO'}

    # Properties used by the file browser
    filepath: bpy.props.StringProperty(name="File Path", description="The file path used for importing the wrl file",
                                       maxlen=1024, default="", options={'HIDDEN'})
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN'})  # ????
    directory: bpy.props.StringProperty(maxlen=1024, default="", subtype='FILE_PATH', options={'HIDDEN'})
    filter_folder: bpy.props.BoolProperty(name="Filter Folders", description="", default=True, options={'HIDDEN'})
    filter_glob: bpy.props.StringProperty(default="*.wrl", options={'HIDDEN'})

    # Custom Properties used by the file browser
    p_reuse_materials: bpy.props.BoolProperty(name="Reuse Materials",
                                              description="IF the material uses the same diffuse texture THEN it will be used instead of creating a new material.",
                                              default=True)

    # p_load_textures_and_materials: bpy.props.BoolProperty(name="Load Textures and Materials",
    #                                                       description="Attempts to load textures.",
    #                                                       default=True)

    p_cull_back_facing: bpy.props.BoolProperty(name="Cull Backfaces",
                                               description="Generally enabled for video games models. Keep in mind, Models from these games are intended to 'back-face cull. Faces will exist in the exact same positions but have opposite normals.",
                                               default=True)

    def invoke(self, context, event):
        self.directory = "C:\\VRML"
        bpy.context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        time_start = time.time()  # Operation Timer

        scene: PreBlender_Scene = read_wrl_file(directory=self.directory, filename=self.filepath)
        to_blender(scene, self.p_reuse_materials, self.p_cull_back_facing)

        time_end = time.time()  # Operation Timer
        print("    Completed in %.4f seconds" % (time_end - time_start))
        return {'FINISHED'}


class PreBlender_Material:
    def __init__(self) -> None:
        super().__init__()
        self.name: str = "NoNameAssigned"
        self.index: int = -1
        self.ambient_intensity: float = 1
        self.diffuse_color: (float, float, float) = (1.0, 1.0, 1.0)
        self.specular_color: (float, float, float) = (1.0, 1.0, 1.0)  # TODO not implemented, not sure where it is even used yet
        self.emissive_color: (float, float, float) = (0.0, 0.0, 0.0)
        self.alpha: float = 1
        self.texture_url: str = None
        self.texture_repeat: bool = True
        self.first_mesh_linked = None

    def __str__(self):
        return self.name


def preBlender_Material_equals(A: PreBlender_Material, B: PreBlender_Material) -> bool:
    R = A.texture_url == B.texture_url and A.texture_repeat == B.texture_repeat and A.diffuse_color == B.diffuse_color and A.emissive_color == B.emissive_color and A.alpha == B.alpha and A.ambient_intensity == B.ambient_intensity
    return R


class PreBlender_Mesh:
    def __init__(self) -> None:
        super().__init__()
        self.name = None
        self.points: List[(float, float, float)] = []
        self.texcoords: List[(float, float)] = []
        self.colors: List[(float, float, float)] = []
        self.material: PreBlender_Material = None

    def __str__(self):
        return self.name


class PreBlender_Scene:
    def __init__(self) -> None:
        super().__init__()
        self.directory: str = ""
        self.filename: str = ""
        self.materials: List[PreBlender_Material] = []
        self.meshes: List[PreBlender_Mesh] = []


def read_wrl_file(directory: str = "C:\\VRML\\", filename: str = "output.wrl") -> PreBlender_Scene:
    scene = PreBlender_Scene()
    scene.directory = directory
    scene.filename = filename
    filepath: str = os.path.join(directory, filename)
    if lilacdogoo_blender_import_wrl.debug: print(filepath)
    # Begin Parsing File
    f: TextIO = open(filepath, 'r', encoding='UTF-8')
    content = f.readlines()
    if len(content) == 0: return None
    i: int = 0
    while i < len(content):
        s: List[str] = content[i].split()
        if (len(s) > 0) and (s[0] == "Shape") and (s[1] == "{"):  # Shape
            material = PreBlender_Material()
            mesh = PreBlender_Mesh()
            i += 1
            s = content[i].split()
            while not s[0] == "}":
                if s[0] == "appearance":  # Material
                    material.name = s[2]
                    i += 1
                    s = content[i].split()
                    while not s[0] == "}":
                        if s[0] == "material":  # Material Parameters
                            i += 1
                            s = content[i].split()
                            while not s[0] == "}":
                                if s[0] == "ambientIntensity": material.ambient_intensity = float(s[1])
                                if s[0] == "diffuseColor": material.diffuse_color = [float(s[1]), float(s[2]), float(s[3])]
                                if s[0] == "specularColor": material.specular_color = [float(s[1]), float(s[2]), float(s[3])]
                                if s[0] == "emisiveColor": material.emisive_color = [float(s[1]), float(s[2]), float(s[3])]
                                if s[0] == "shinines": material.specular = float(s[1])
                                if s[0] == "transparency": material.alpha = 1 - float(s[1])
                                i += 1
                                s = content[i].split()
                        elif s[0] == "texture":  # Texture Parameters
                            i += 1
                            s = content[i].split()
                            while not s[0] == "}":
                                if s[0] == "url": material.texture_url = s[1].strip("\"")
                                if s[0] == "repeatS": material.texture_repeat = s[1] == "TRUE"
                                i += 1
                                s = content[i].split()
                        i += 1
                        s = content[i].split()
                elif s[0] == "geometry":  # Mesh
                    mesh.name = s[2]
                    i += 1
                    s = content[i].split()
                    while not s[0] == "}":
                        if s[0] == "coord":  # Mesh Verticies
                            i += 1
                            s = content[i].split()
                            while not s[0] == "}":
                                if s[0] == "point":
                                    i += 1
                                    s = content[i].split()
                                    while not s[0] == "]":
                                        # Load Rotated so it is upright in Blender
                                        mesh.points.append((float(s[0]), -float(s[2].strip(",")), float(s[1])))
                                        i += 1
                                        s = content[i].split()
                                i += 1
                                s = content[i].split()
                        elif s[0] == "texCoord":  # Mesh Texture Coordinates
                            i += 1
                            s = content[i].split()
                            while not s[0] == "}":
                                if s[0] == "point":
                                    i += 1
                                    s = content[i].split()
                                    while not s[0] == "]":
                                        mesh.texcoords.append((float(s[0]), float(s[1].strip(","))))
                                        i += 1
                                        s = content[i].split()
                                i += 1
                                s = content[i].split()
                        elif s[0] == "color":  # Vertex Colors
                            i += 1
                            s = content[i].split()
                            while not s[0] == "}":
                                if s[0] == "color":
                                    i += 1
                                    s = content[i].split()
                                    while not s[0] == "]":
                                        mesh.colors.append((float(s[0]), float(s[1]), float(s[2].strip(","))))
                                        i += 1
                                        s = content[i].split()
                                i += 1
                                s = content[i].split()
                        i += 1
                        s = content[i].split()
                i += 1
                s = content[i].split()

            # Search for Duplicate Material
            _mat_dupe_: bool = False
            for _mat_ in scene.materials:
                if preBlender_Material_equals(material, _mat_):
                    material = _mat_  # use the duplicate instead
                    _mat_dupe_ = True
                    break
            # if no duplicate found then append
            if not _mat_dupe_:
                material.index = len(scene.materials)
                scene.materials.append(material)
            # Assign Material to Mesh
            mesh.material = material
            # Link mesh to material IF none already - For usage with some shader defaults.
            if mesh.material.first_mesh_linked is None:
                mesh.material.first_mesh_linked = mesh

            scene.meshes.append(mesh)
        i += 1
    f.close()
    return scene


# Pretty hack but should work reliably.
# Skip the header then check if every single byte after is zero.
def is_BMP_valid_transparency(path: str) -> bool:
    f: BinaryIO = open(os.path.join(path), 'rb')
    f.seek(0x36)
    b = f.read(1)
    while len(b) > 0:
        if b[0] > 0: return True  # A byte was not zero, transparency will be activated
        b = f.read(1)
    return False


def to_blender(scene: PreBlender_Scene, p_reuse_materials: bool, p_cull_back_facing: bool):
    if scene is None: return
    r = random.Random()

    # ?????? MATERIALS ??????
    blenderMaterials: List[bpy.types.Material] = []
    reusable_vertex_color_only_material: bpy.types.Material = None

    for mat in scene.materials:
        # Usage Flags
        path_diffuse: str = os.path.join(scene.directory, mat.texture_url) if mat.texture_url is not None else None
        if path_diffuse is None or not os.path.isfile(path_diffuse): path_diffuse = None
        use_vertex_color: bool = True if mat.first_mesh_linked is not None and len(mat.first_mesh_linked.colors) > 0 else False

        # Check if this texture is already in the project
        if p_reuse_materials:
            if path_diffuse is not None:
                found_existing_material: bool = False
                for M in bpy.data.materials:
                    if M.node_tree.nodes.find('Diffuse Color') != -1:
                        N = M.node_tree.nodes['Diffuse Color']
                        if N.image is not None and N.image.filepath == path_diffuse:
                            blenderMaterials.append(M)
                            found_existing_material = True
                            break
                if found_existing_material: continue
            elif use_vertex_color:
                if reusable_vertex_color_only_material is not None:
                    blenderMaterials.append(reusable_vertex_color_only_material)
                    continue
                found_existing_material: bool = False
                for M in bpy.data.materials:
                    if M.node_tree.nodes.find('Vertex Color OnlyWRL') != -1:
                        reusable_vertex_color_only_material = M
                        blenderMaterials.append(M)
                        found_existing_material = True
                        break
                if found_existing_material: continue

        path_alpha_map: str = None  # Another Usage Flag (Variable MUST be defined past this point)
        if path_diffuse is not None:
            path_alpha_map = os.path.join(scene.directory, mat.texture_url.replace("_c.", "_a."))
            if not os.path.isfile(path_alpha_map) or not is_BMP_valid_transparency(path_alpha_map):
                path_alpha_map = None
        use_ambient_intensity = True if mat.ambient_intensity is not None and mat.ambient_intensity != 1 else False

        # Create Blender Material
        blenderMaterial: bpy.types.Material = bpy.data.materials.new(mat.name)
        blenderMaterial.diffuse_color = (r.random(), r.random(), r.random(), 1.0)
        blenderMaterial.use_backface_culling = p_cull_back_facing
        blenderMaterial.use_nodes = True

        # ??? NODES ???
        # Principled BSDF
        nodes: bpy.types.Nodes = blenderMaterial.node_tree.nodes
        node_bsdf: bpy.types.Node = nodes['Principled BSDF']
        node_bsdf.inputs['Base Color'].default_value = mat.diffuse_color[0], mat.diffuse_color[1], mat.diffuse_color[2], 1.0
        # TODO Specular color is unused - I will implement it if I find a need to
        node_bsdf.inputs['Specular'].default_value = 0.0
        node_bsdf.inputs['Emission'].default_value = mat.emissive_color[0], mat.emissive_color[1], mat.emissive_color[2], 1.0
        node_bsdf.inputs['Alpha'].default_value = mat.alpha

        # Vector Math - Ambient intensity
        if use_ambient_intensity:
            node_ambient_intensity: bpy.types.Node = nodes.new('ShaderNodeVectorMath')
            node_ambient_intensity.name = "Ambient Intensity"
            node_ambient_intensity.label = "Ambient Intensity"
            node_ambient_intensity.location = (node_bsdf.location[0] - node_ambient_intensity.width - 50, node_bsdf.location[1])
            node_ambient_intensity.operation = 'SCALE'
            node_ambient_intensity.inputs['Scale'].default_value = mat.ambient_intensity

        # RGB Multiply - Vertex Color
        if use_vertex_color and path_diffuse is not None:
            node_mix_vertex_color: bpy.types.Node = nodes.new('ShaderNodeMixRGB')
            node_mix_vertex_color.name = "Mix Col & VertCol"
            node_mix_vertex_color.label = "Mix Col & VertCol"
            node_mix_vertex_color.blend_type = 'MULTIPLY'
            node_mix_vertex_color.inputs['Fac'].default_value = 1.0
            node_mix_vertex_color.inputs['Color1'].default_value = (1.0, 1.0, 1.0, 1.0)
            node_mix_vertex_color.inputs['Color2'].default_value = (1.0, 1.0, 1.0, 1.0)
            if use_ambient_intensity:
                node_mix_vertex_color.location = (node_ambient_intensity.location[0] - node_mix_vertex_color.width - 50, node_bsdf.location[1])
            else:
                node_mix_vertex_color.location = (node_bsdf.location[0] - node_mix_vertex_color.width - 50, node_bsdf.location[1])

        # Texture Node
        if path_diffuse is not None:
            node_texture_diffuse: bpy.types.Node = nodes.new('ShaderNodeTexImage')
            node_texture_diffuse.name = "Diffuse Color"
            node_texture_diffuse.label = "Diffuse Color"
            node_texture_diffuse.width = 300
            F = os.path.join(scene.directory, mat.texture_url)  # Filepath of image to add to blender
            if os.path.isfile(F):
                node_texture_diffuse.image = bpy.data.images.load(filepath=F, check_existing=True)
            node_texture_diffuse.extension = 'REPEAT' if mat.texture_repeat else 'CLIP'
            if use_vertex_color:
                node_texture_diffuse.location = (node_mix_vertex_color.location[0] - node_texture_diffuse.width - 50, node_bsdf.location[1])
            else:
                if use_ambient_intensity:
                    node_texture_diffuse.location = (node_ambient_intensity.location[0] - node_texture_diffuse.width - 50, node_bsdf.location[1])
                else:
                    node_texture_diffuse.location = (node_bsdf.location[0] - node_texture_diffuse.width - 50, node_bsdf.location[1])

        # Vertex Color Node
        if use_vertex_color:
            node_vertex_color: bpy.types.Node = nodes.new('ShaderNodeVertexColor')
            node_vertex_color.name = "Vertex Color"
            node_vertex_color.label = "Vertex Color"
            if path_diffuse is not None:
                node_vertex_color.name = "Vertex Color"
                node_vertex_color.location = (node_mix_vertex_color.location[0] - node_vertex_color.width - 50, node_texture_diffuse.location[1] - 300)
            else:
                if use_ambient_intensity:
                    node_vertex_color.name = "Vertex Color"
                    node_vertex_color.location = (node_ambient_intensity.location[0] - node_vertex_color.width - 50, node_ambient_intensity.location[1] - 30)
                else:
                    node_vertex_color.name = "Vertex Color OnlyWRL"  # The name of this node is used to locate it again in order to reuse this material later
                    node_vertex_color.location = (node_bsdf.location[0] - node_vertex_color.width - 50, node_bsdf.location[1] - 30)

        if path_alpha_map is not None:
            # Texture Aplha Inversion Node
            node_texture_alpha_inversion: bpy.types.Node = nodes.new('ShaderNodeMath')
            node_texture_alpha_inversion.name = "Invert Alpha"
            node_texture_alpha_inversion.label = "Invert Alpha"
            node_texture_alpha_inversion.operation = 'SUBTRACT'
            node_texture_alpha_inversion.inputs[0].default_value = 1.0
            node_texture_alpha_inversion.inputs[1].default_value = 0.0
            node_texture_alpha_inversion.location = node_bsdf.location[0] - node_texture_alpha_inversion.width - 50, node_bsdf.location[1] - 540

            # Texture Alpha Node
            node_texture_alpha: bpy.types.Node = nodes.new('ShaderNodeTexImage')
            node_texture_alpha.name = "Alpha Map"
            node_texture_alpha.label = "Alpha Map"
            node_texture_alpha.width = 300
            node_texture_alpha.image = bpy.data.images.load(filepath=path_alpha_map, check_existing=True)
            node_texture_alpha.location = node_texture_alpha_inversion.location[0] - node_texture_alpha.width - 50, node_bsdf.location[1] - 480

        # ??? NODE LINKS ???
        links: bpy.types.NodeLinks = blenderMaterial.node_tree.links
        if use_ambient_intensity:
            links.new(node_ambient_intensity.outputs['Vector'], node_bsdf.inputs['Base Color'])
            if path_diffuse is not None:
                if use_vertex_color:
                    links.new(node_mix_vertex_color.outputs['Color'], node_ambient_intensity.inputs['Vector'])
                    links.new(node_texture_diffuse.outputs['Color'], node_mix_vertex_color.inputs['Color1'])
                    links.new(node_vertex_color.outputs['Color'], node_mix_vertex_color.inputs['Color2'])
                else:
                    links.new(node_texture_diffuse.outputs['Color'], node_ambient_intensity.inputs['Vector'])
            else:
                if use_vertex_color:
                    links.new(node_vertex_color.outputs['Color'], node_ambient_intensity.inputs['Vector'])
        else:
            if path_diffuse is not None:
                if use_vertex_color:
                    links.new(node_mix_vertex_color.outputs['Color'], node_bsdf.inputs['Base Color'])
                    links.new(node_texture_diffuse.outputs['Color'], node_mix_vertex_color.inputs['Color1'])
                    links.new(node_vertex_color.outputs['Color'], node_mix_vertex_color.inputs['Color2'])
                else:
                    links.new(node_texture_diffuse.outputs['Color'], node_bsdf.inputs['Base Color'])
            else:
                if use_vertex_color:
                    links.new(node_vertex_color.outputs['Color'], node_bsdf.inputs['Base Color'])

        if path_alpha_map is not None:
            links.new(node_texture_alpha.outputs['Color'], node_texture_alpha_inversion.inputs[1])
            links.new(node_texture_alpha.outputs['Color'], node_bsdf.inputs['Alpha'])
            blenderMaterial.blend_method = 'CLIP'

        blenderMaterials.append(blenderMaterial)

    # ?????? MESHES ??????
    blender_collection: bpy.types.Collection = bpy.data.collections.new("WRL Import.000")
    for mesh in scene.meshes:
        # CREATE BLENDER STUFF
        blender_mesh: bpy.types.Mesh = bpy.data.meshes.new(mesh.name)
        blender_object: bpy.types.Object = bpy.data.objects.new(mesh.name, blender_mesh)
        blender_bMesh: bmesh.types.BMesh = bmesh.new()
        blender_bMesh.from_mesh(blender_mesh)

        # Add Data to Face Loops (UV, Color)
        blender_bMesh_uvLayer = blender_bMesh.loops.layers.uv.new() if len(mesh.texcoords) > 1 else None
        blender_bMesh_colorLayer = blender_bMesh.loops.layers.color.new() if len(mesh.colors) > 2 else None

        # Create Vertices
        blender_bMesh_verts = []  # Need to access this to create faces
        for point in mesh.points:
            blender_bMesh_verts.append(blender_bMesh.verts.new(point))
        blender_bMesh.verts.index_update()

        # Create Faces (All faces are triangles)
        for i in range(0, len(mesh.points), 3):
            # load faces backwards to correct normals direction
            blender_face_loop = [blender_bMesh_verts[i + 2], blender_bMesh_verts[i + 1], blender_bMesh_verts[i]]  # Converts to Blender format
            blender_bMesh_face: bmesh.types.BMFace = blender_bMesh.faces.new(blender_face_loop)
            # Assign UV coords - Backwards to match how the face was created (to fix normals)
            if blender_bMesh_uvLayer is not None:
                blender_bMesh_face.loops[0][blender_bMesh_uvLayer].uv = mesh.texcoords[i + 2]
                blender_bMesh_face.loops[1][blender_bMesh_uvLayer].uv = mesh.texcoords[i + 1]
                blender_bMesh_face.loops[2][blender_bMesh_uvLayer].uv = mesh.texcoords[i]
            # Assign Vertex Colors
            if blender_bMesh_colorLayer is not None:
                c = mesh.colors[i + 2]
                blender_bMesh_face.loops[0][blender_bMesh_colorLayer] = c[0], c[1], c[2], 1.0
                c = mesh.colors[i + 1]
                blender_bMesh_face.loops[1][blender_bMesh_colorLayer] = c[0], c[1], c[2], 1.0
                c = mesh.colors[i]
                blender_bMesh_face.loops[2][blender_bMesh_colorLayer] = c[0], c[1], c[2], 1.0

        # Push BMesh to Mesh
        blender_bMesh.to_mesh(blender_mesh)
        blender_bMesh.free()
        # Set Object Properties
        blender_mesh.materials.append(blenderMaterials[mesh.material.index])
        blender_object.color = blenderMaterials[mesh.material.index].diffuse_color
        # Add Object to New Collection
        blender_collection.objects.link(blender_object)
    # Add New Collection to Blender scene
    bpy.context.scene.collection.children.link(blender_collection)


if __name__ == "__main__":
    scene = read_wrl_file("C:\\VRML", "output.wrl")
    scene = scene

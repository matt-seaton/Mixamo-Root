 # -*- coding: utf-8 -*-

'''
    Copyright (C) 2022  Richard Perry
    Copyright (C) Average Godot Enjoyer (Johngoss725)
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    Note that Johngoss725's original contributions were published under a 
    Creative Commons 1.0 Universal License (CC0-1.0) located at
    <https://github.com/Johngoss725/Mixamo-To-Godot>.
'''

# Original Script Created By: Average Godot Enjoyer (Johngoss725)
# Bone Renaming Modifications, File Handling, And Addon By: Richard Perry
import bpy
import os
import logging
from pathlib import Path
from mathutils import Quaternion
import math
import numpy as np


log = logging.getLogger(__name__)

# in future remove_prefix should be renamed to rename prefix and a target prefix should be specifiable via ui
def fixBones(remove_prefix=False, name_prefix="mixamorig:"):
    bpy.ops.object.mode_set(mode = 'OBJECT')
        
    if not bpy.ops.object:
        log.warning('[Mixamo Root] Could not find amature object, please select the armature')

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.object.show_in_front = True

    if remove_prefix:
        for rig in bpy.context.selected_objects:
            if rig.type == 'ARMATURE':
                for mesh in rig.children:
                    for vg in mesh.vertex_groups:
                        new_name = vg.name
                        new_name = new_name.replace(name_prefix,"")
                        rig.pose.bones[vg.name].name = new_name
                        vg.name = new_name
                for bone in rig.pose.bones:
                    bone.name = bone.name.replace(name_prefix,"")
        for action in bpy.data.actions:
            fc = action.fcurves
            for f in fc:
                f.data_path = f.data_path.replace(name_prefix,"")
        
def scaleAll():
    bpy.ops.object.mode_set(mode='OBJECT')

    prev_context=bpy.context.area.type
        
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.context.area.type = 'GRAPH_EDITOR'
    bpy.context.space_data.dopesheet.filter_text = "Location"
    bpy.context.space_data.pivot_point = 'CURSOR'
    bpy.context.space_data.dopesheet.use_filter_invert = False
        
    bpy.ops.anim.channels_select_all(action='SELECT')   
        
    bpy.ops.transform.resize(value=(1, 0.01, 1), orient_type='GLOBAL',
    orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    orient_matrix_type='GLOBAL',
    constraint_axis=(False, True, False),
    mirror=True, use_proportional_edit=False,
    proportional_edit_falloff='SMOOTH',
    proportional_size=1,
    use_proportional_connected=False,
    use_proportional_projected=False)


def euler_to_quat(*angles):
    import math
    half_angles = [a/2 for a in angles]
    c1, s1 = math.cos(half_angles[0]), math.sin(half_angles[0])
    c2, s2 = math.cos(half_angles[1]), math.sin(half_angles[1])
    c3, s3 = math.cos(half_angles[2]), math.sin(half_angles[2])
    w = c1 * c2 * c3 - s1 * s2 * s3
    x = c1 * s2 * c3 + s1 * c2 * s3
    y = c1 * c2 * s3 - s1 * s2 * c3
    z = s1 * c2 * c3 + c1 * s2 * s3
    return Quaternion((w, x, y, z))


def decompose_quaternion(q):
    q.normalize()
    w = np.sqrt(1 + q[0]) / np.sqrt(2)
    x = q[1] / (np.sqrt(2) * w)
    y = q[2] / (np.sqrt(2) * w)
    z = q[3] / (np.sqrt(2) * w)
    return Quaternion(np.array([w, x, y, z])).normalized()

def copyHips(root_bone_name="Root", hip_bone_name="mixamorig:Hips", name_prefix="mixamorig:"):
    bpy.ops.object.mode_set(mode = 'POSE')
    bpy.context.area.ui_type = 'FCURVES'
    #SELECT OUR ROOT MOTION BONE 
    bpy.ops.pose.select_all(action='DESELECT')
    print(name_prefix, '!')
    bpy.context.object.pose.bones[name_prefix + root_bone_name].bone.select = True
    # SET FRAME TO ZERO
    bpy.ops.graph.cursor_set(frame=0.0, value=0.0)
    #ADD NEW KEYFRAME
    bpy.ops.anim.keyframe_insert_menu(type='Location')
    #SELECT ONLY HIPS AND LOCTAIUON GRAPH DATA
    bpy.ops.pose.select_all(action='DESELECT')
    bpy.context.object.pose.bones[hip_bone_name].bone.select = True        
    bpy.context.area.ui_type = 'DOPESHEET'
    bpy.context.space_data.dopesheet.filter_text = "Location"
    bpy.context.area.ui_type = 'FCURVES'
    #COPY THE LOCATION VALUES OF THE HIPS AND DELETE THEM         
    #bpy.ops.graph.copy()
    bpy.ops.graph.select_all(action='DESELECT')
    
    myFcurves = bpy.context.object.animation_data.action.fcurves
    hip_bone_fcurve = f'pose.bones["{hip_bone_name}"].location'
    root_bone_fcurve = f'pose.bones["{name_prefix}{root_bone_name}"].location'

    bpy.context.object.pose.bones[name_prefix + root_bone_name].bone.select = True
    
    # Clear out root bone fcurve
    for curve in myFcurves:
        if str(curve.data_path) == root_bone_fcurve:
            for key in curve.keyframe_points:
                curve.keyframe_points.remove(key)
    
    # copy x and z keyframes to root bone
    for curve in myFcurves:
        if str(curve.data_path) == hip_bone_fcurve and curve.array_index in [0, 2]:  # x and z hip locations
            for root_curve in myFcurves:
                if str(root_curve.data_path) == root_bone_fcurve and root_curve.array_index == curve.array_index:
                    for key in curve.keyframe_points:
                        root_curve.keyframe_points.insert(frame=key.co[0], value=key.co[1] * 100)
     
    # Remove xz tracks from hip bone
    for curve in myFcurves:
        if str(curve.data_path)==hip_bone_fcurve:
            if curve.array_index != 1:  # Keep y
                myFcurves.remove(curve)

    # Get the fcurves for the root bone's location
    fcurves = [fcurve for fcurve in myFcurves if fcurve.data_path == 'pose.bones["{}"].location'.format(name_prefix + root_bone_name) and fcurve.array_index in range(3)]

    # Set the minimum Y value of the root bone to 0
    z_fcurve = fcurves[1]
    for keyframe in z_fcurve.keyframe_points:
        if keyframe.co.y < 0:
            keyframe.co.y = 0
    
    # Looks like we're eliminating floating hips ?
    hips_fcurves = [hips_fcurve for hips_fcurve in myFcurves if hips_fcurve.data_path == 'pose.bones["{}"].location'.format(hip_bone_name) and hips_fcurve.array_index in range(3)]
    for keyframe in hips_fcurves[0].keyframe_points:
        if keyframe.co.y > 0:
            keyframe.co.y = 0
            #keyframe.co.y = keyframe.co.y / 2
    
    # Get quaternion keyframes
    hip_quats = {}
    for curve in myFcurves:
        hip_bone_fcurve = f'pose.bones["{hip_bone_name}"].rotation_quaternion'
        if str(curve.data_path)==hip_bone_fcurve:
            for key in curve.keyframe_points:
                frame, quat_component = key.co
                if int(round(frame)) not in hip_quats:  # convert float to int
                    hip_quats[int(round(frame))] = [0] * 4
                hip_quats[int(round(frame))][curve.array_index] = quat_component
    hip_quats = {f: Quaternion(q) for f, q in hip_quats.items()}

    ## Local hip rotation in local frame
    hip_rot = bpy.context.object.pose.bones[hip_bone_name].bone.matrix_local.to_quaternion()

    ## Convert keyframes to root bone frame
    ## hip_local @ hip_rot = hip_root_frame
    hip_quats = {f: q @ hip_rot for f, q in hip_quats.items()}
    
    ## Pull out y-axis component of rotation for root bone
    root_quats = {f: Quaternion((q.w, 0, q.y, 0)).normalized() for f, q in hip_quats.items()}
    for f in root_quats:
        root_quats[f].normalize()
    
    ## Subtract rotation from root bone from first frame, so root pone still points forward on clips
    ## where the hips are angled (e.g. strafe).  Leave this component on the hips
    first_frame = min(hip_quats.keys())
    hip_y_rot = root_quats[first_frame]
    for f, q in root_quats.items():
        root_quats[f] = hip_y_rot.inverted() @ root_quats[f]
    
    # hip_quat_root_frame = root_quat (Y) @ remainder (XZ)
    remainder = {f: root_quats[f].inverted() @ q for f, q in hip_quats.items()}
   
    # convert back to hip frame 
    remainder = {f: q @ hip_rot.inverted() for f, q in remainder.items()}

    # add rot tracks to root and set keyframes
    for x in range(4):
        curve = myFcurves.new(data_path=f'pose.bones["{name_prefix}{root_bone_name}"].rotation_quaternion', index=x, action_group=name_prefix + root_bone_name)
        for f, k in root_quats.items():
            curve.keyframe_points.insert(frame=f, value=k[x])
  
    # set hips keyframes
    for curve in myFcurves:
        if str(curve.data_path) != f'pose.bones["{hip_bone_name}"].rotation_quaternion':
            continue
        for f, k in remainder.items():
            curve.keyframe_points.insert(frame=f, value=k[curve.array_index])
  
  
def fix_bones_nla(remove_prefix=False, name_prefix="mixamorig:"):
    bpy.ops.object.mode_set(mode = 'OBJECT')
        
    if not bpy.ops.object:
        log.warning('[Mixamo Root] Could not find amature object, please select the armature')

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.object.show_in_front = True

def scale_all_nla(armature):
    bpy.ops.object.mode_set(mode='OBJECT')

    # prev_context=bpy.context.area.type

    for track in [x for x in armature.animation_data.nla_tracks]:
        bpy.context.active_nla_track = track
        for strip in track.strips:
            bpy.context.active_nla_strip = strip
            print(bpy.context.active_nla_strip)

        
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.context.area.type = 'GRAPH_EDITOR'
    bpy.context.space_data.dopesheet.filter_text = "Location"
    bpy.context.space_data.pivot_point = 'CURSOR'
    bpy.context.space_data.dopesheet.use_filter_invert = False
    
    bpy.ops.anim.channels_select_all(action='SELECT')   
        
    bpy.ops.transform.resize(value=(1, 0.01, 1), orient_type='GLOBAL',
    orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    orient_matrix_type='GLOBAL',
    constraint_axis=(False, True, False),
    mirror=True, use_proportional_edit=False,
    proportional_edit_falloff='SMOOTH',
    proportional_size=1,
    use_proportional_connected=False,
    use_proportional_projected=False)

def copy_hips_nla(root_bone_name="Root", hip_bone_name="mixamorig:Hips", name_prefix="mixamorig:"):
    hip_bone_name="Ctrl_Hips"
    bpy.ops.object.mode_set(mode='POSE')
    previous_context = bpy.context.area.ui_type
    bpy.ops.pose.select_all(action='DESELECT')
    while False:
        #SELECT OUR ROOT MOTION BONE 
        # bpy.context.object.pose.bones[name_prefix + root_bone_name].bone.select = True

        # bpy.ops.nla.tweakmode_enter()
        # bpy.context.area.ui_type = 'FCURVES'
        
        # # SET FRAME TO ZERO
        # bpy.ops.graph.cursor_set(frame=0.0, value=0.0)
        # #ADD NEW KEYFRAME
        # bpy.ops.anim.keyframe_insert_menu(type='Location')
        # #SELECT ONLY HIPS AND LOCTAIUON GRAPH DATA
        # bpy.ops.pose.select_all(action='DESELECT')
        # bpy.context.object.pose.bones[hip_bone_name].bone.select = True        
        # bpy.context.area.ui_type = 'DOPESHEET'
        # bpy.context.space_data.dopesheet.filter_text = "Location"
        # bpy.context.area.ui_type = 'FCURVES'
        # #COPY THE LOCATION VALUES OF THE HIPS AND DELETE THEM         
        # bpy.ops.graph.copy()
        # bpy.ops.graph.select_all(action='DESELECT')
            
        # myFcurves = bpy.context.object.animation_data.action.fcurves
                
        # for i in myFcurves:
        #     hip_bone_fcurve = 'pose.bones["'+hip_bone_name+'"].location'
        #     if str(i.data_path)==hip_bone_fcurve:
        #         myFcurves.remove(i)
                    
        # bpy.ops.pose.select_all(action='DESELECT')
        # bpy.context.object.pose.bones[name_prefix + root_bone_name].bone.select = True
        # bpy.ops.graph.paste()

        # for animation data in object
        # for 
        pass

    for track in bpy.context.object.animation_data.nla_tracks:
        bpy.context.object.animation_data.nla_tracks.active = track
        for strip in track.strips:
            bpy.context.object.pose.bones[name_prefix + root_bone_name].bone.select = True
            bpy.context.area.ui_type = 'NLA_EDITOR'
            bpy.ops.nla.tweakmode_enter()
            bpy.context.area.ui_type = 'FCURVES'
            hip_curves = [fc for fc in strip.fcurves if hip_bone_name in fc.data_path and fc.data_path.startswith('location')]
            
            # Copy Hips to root
            ## Insert keyframe for root bone
            start_frame = strip.action.frame_range[0]
            # frame sets the x axis cursor (determines the frame, and value the y axis cursor, which is the amplitude of the curve)
            bpy.ops.graph.cursor_set(frame=start_frame, value=0.0)
            bpy.ops.anim.keyframe_insert_menu(type='Location')
            bpy.ops.pose.select_all(action='DESELECT')

            ## Copy Location fcruves
            bpy.context.object.pose.bones[hip_bone_name].bone.select = True        
            bpy.context.area.ui_type = 'DOPESHEET'
            bpy.context.space_data.dopesheet.filter_text = "Location"
            bpy.context.area.ui_type = 'FCURVES'
            bpy.ops.graph.copy()
            bpy.ops.graph.select_all(action='DESELECT')

            ## We want to delete the hips locations
            allFcurves = strip.fcurves
            for fc in hip_curves:
                allFcurves.remove(fc)

            ## Paste location fcurves to the root bone
            bpy.ops.pose.select_all(action='DESELECT')
            bpy.context.object.pose.bones[name_prefix + root_bone_name].bone.select = True
            bpy.ops.graph.paste()


            loc_fcurves = [fc for fc in strip.fcurves if root_bone_name in fc.data_path and fc.data_path.startswith('location')]
            
            # Update Root Bone
            # set z of root to min 0 (not negative).
            for fc in loc_fcurves:
                # Z axis location curve
                if fc.array_index == 2:
                    for kp in fc.keyframe_points:
                        kp.co.z = min(0, abs(kp.co.z))
                        
            # Delete rotation curves for x(0) and y(1) axis. Should we delet Z rotation too? 
            # rot_fcurves = [fc for fc in strip.fcurves if root_bone_name in fc.data_path and fc.data_path.startswith('rotation') and (fc.array_index == 0 or fc.array_index == 1)]
            # for fc in rot_fcurves:
            #     strip.fcurves.remove(fc)
            # while(rot_fcurves):
            #     fc = rot_fcurves.pop()
            #     strip.fcurves.remove(fc)
            bpy.context.area.ui_type = 'NLA_EDITOR'
            bpy.ops.nla.tweakmode_exit()
            bpy.context.area.ui_type = previous_context
    bpy.ops.object.mode_set(mode='OBJECT')
    
def deleteArmature(imported_objects=set()):
    armature = None
    if bpy.context.selected_objects:
        armature = bpy.context.selected_objects[0]
    if imported_objects == set():
        log.warning("[Mixamo Root] No armature imported, nothing to delete")
    else:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for obj in imported_objects:
            bpy.data.objects[obj.name].select_set(True)
        
    bpy.ops.object.delete(use_global=False, confirm=False)
    if bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = armature

def import_armature(filepath, root_bone_name="Root", hip_bone_name="mixamorig:Hips", remove_prefix=False, name_prefix="mixamorig:",  insert_root=False, delete_armatures=False):
    old_objs = set(bpy.context.scene.objects)
    if insert_root:
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.import_scene.fbx(filepath = filepath)#,  automatic_bone_orientation=True)
    else:
        bpy.ops.import_scene.fbx(filepath = filepath)#,  automatic_bone_orientation=True)
    
    imported_objects = set(bpy.context.scene.objects) - old_objs
    imported_actions = [x.animation_data.action for x in imported_objects if x.animation_data]
    print("[Mixamo Root] Now importing: " + str(filepath))
    imported_actions[0].name = Path(filepath).resolve().stem # Only reads the first animation associated with an imported armature
    
    if insert_root:
        add_root_bone(root_bone_name, hip_bone_name, remove_prefix, name_prefix)
    
    
def add_root_bone(root_bone_name="Root", hip_bone_name="mixamorig:Hips", remove_prefix=False, name_prefix="mixamorig:"):
    armature = bpy.context.selected_objects[0]
    bpy.ops.object.mode_set(mode='EDIT')

    root_bone = armature.data.edit_bones.new(name_prefix + root_bone_name)
    root_bone.tail.z = .3

    armature.data.edit_bones[hip_bone_name].parent = armature.data.edit_bones[name_prefix + root_bone_name]
    bpy.ops.object.mode_set(mode='OBJECT')

    fixBones(remove_prefix=remove_prefix, name_prefix=name_prefix)
    scaleAll()
    if remove_prefix:
        hip_bone_name = hip_bone_name.replace(name_prefix, '')
        name_prefix = ''
    copyHips(root_bone_name=root_bone_name, hip_bone_name=hip_bone_name, name_prefix=name_prefix)

def add_root_bone_nla(root_bone_name="Root", hip_bone_name="mixamorig:Hips", name_prefix="mixamorig:"):#remove_prefix=False, name_prefix="mixamorig:"):
    armature = bpy.context.selected_objects[0]
    bpy.ops.object.mode_set(mode='EDIT')

    # Add root bone to edit bones
    root_bone = armature.data.edit_bones.new(name_prefix + root_bone_name)
    root_bone.tail.z = .25

    armature.data.edit_bones[hip_bone_name].parent = armature.data.edit_bones[name_prefix + root_bone_name]
    bpy.ops.object.mode_set(mode='OBJECT')

    # fix_bones_nla(remove_prefix=remove_prefix, name_prefix=name_prefix)
    # scale_all_nla()
    copy_hips_nla(root_bone_name=root_bone_name, hip_bone_name=hip_bone_name, name_prefix=name_prefix)

def push(obj, action, track_name=None, start_frame=0):
    # Simulate push :
    # * add a track
    # * add an action on track
    # * lock & mute the track
    # * remove active action from object
    tracks = obj.animation_data.nla_tracks
    new_track = tracks.new(prev=None)
    if track_name:
        new_track.name = track_name
    strip = new_track.strips.new(action.name, start_frame, action)
    obj.animation_data.action = None

def get_all_anims(source_dir, root_bone_name="Root", hip_bone_name="mixamorig:Hips", remove_prefix=False, name_prefix="mixamorig:",  insert_root=False, delete_armatures=False):
    files = os.listdir(source_dir)
    files = [f for f in files if f.endswith('.fbx')]
    num_files = len(files)
    current_context = bpy.context.area.ui_type
    old_objs = set(bpy.context.scene.objects)
    
    for file in files:
        print("file: " + str(file))
        if not file.endswith('.DS_Store') and file.endswith('.fbx'):
            try:
                filepath = source_dir+"/"+file
                import_armature(filepath, root_bone_name, hip_bone_name, remove_prefix, name_prefix, insert_root, delete_armatures)
                imported_objects = set(bpy.context.scene.objects) - old_objs
                if delete_armatures and num_files > 1:
                    deleteArmature(imported_objects)
                    num_files -= 1
            except Exception as e:
                raise
                log.error("[Mixamo Root] ERROR get_all_anims raised %s when processing %s" % (str(e), file))
                return -1
    bpy.context.area.ui_type = current_context
    bpy.context.scene.frame_start = 0
    bpy.ops.object.mode_set(mode='OBJECT')

def apply_all_anims(delete_applied_armatures=False, control_rig=None, push_nla=False):
    if control_rig and control_rig.type == 'ARMATURE':
        bpy.ops.object.mode_set(mode='OBJECT')

        imported_objects = set(bpy.context.scene.objects)
        imported_armatures = [x for x in imported_objects if x.type == 'ARMATURE' and x.name != control_rig.name]

        for obj in imported_armatures:
            action_name = obj.animation_data.action.name
            bpy.context.scene.mix_source_armature = obj
            bpy.context.view_layer.objects.active = control_rig

            bpy.ops.mr.import_anim_to_rig()

            bpy.context.view_layer.objects.active = control_rig
            selected_action = control_rig.animation_data.action
            selected_action.name = 'ctrl_' + action_name
            # created_actions.append(selected_action)

            if push_nla:
                push(control_rig, selected_action, None, int(selected_action.frame_start))

            if delete_applied_armatures:
                bpy.context.view_layer.objects.active = control_rig
                deleteArmature(set([obj]))


if __name__ == "__main__":
    dir_path = "" # If using script in place please set this before running.
    get_all_anims(r"C:\Users\matts\Downloads", insert_root=True)
    print("[Mixamo Root] Run as plugin, or copy script in text editor while setting parameter defaults.")

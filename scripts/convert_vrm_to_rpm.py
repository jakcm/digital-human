#!/usr/bin/env python3
"""
Comprehensive VRM → TalkingHead model conversion.
Renames bone nodes, morph target names, and reorganizes the scene
graph so mesh nodes are children of Armature (where TalkingHead
traverses to find blend shapes).
"""
import json, struct, sys, os

BONE_MAP = {
    'J_Bip_C_Hips': 'Hips',
    'J_Bip_C_Spine': 'Spine',
    'J_Bip_C_Chest': 'Spine1',
    'J_Bip_C_UpperChest': 'Spine2',
    'J_Bip_C_Neck': 'Neck',
    'J_Bip_C_Head': 'Head',
    'J_Bip_L_UpperArm': 'LeftArm',
    'J_Bip_R_UpperArm': 'RightArm',
    'J_Bip_L_LowerArm': 'LeftForeArm',
    'J_Bip_R_LowerArm': 'RightForeArm',
    'J_Bip_L_Hand': 'LeftHand',
    'J_Bip_R_Hand': 'RightHand',
    'J_Bip_L_UpperLeg': 'LeftUpLeg',
    'J_Bip_R_UpperLeg': 'RightUpLeg',
    'J_Bip_L_LowerLeg': 'LeftLeg',
    'J_Bip_R_LowerLeg': 'RightLeg',
    'J_Bip_L_Foot': 'LeftFoot',
    'J_Bip_R_Foot': 'RightFoot',
    'J_Bip_L_ToeBase': 'LeftToeBase',
    'J_Bip_R_ToeBase': 'RightToeBase',
    'J_Adj_L_FaceEye': 'LeftEye',
    'J_Adj_R_FaceEye': 'RightEye',
    'J_Bip_L_Shoulder': 'LeftShoulder',
    'J_Bip_R_Shoulder': 'RightShoulder',
    'J_Bip_L_Index1': 'LeftHandIndex1',
    'J_Bip_R_Index1': 'RightHandIndex1',
    'J_Bip_L_Index2': 'LeftHandIndex2',
    'J_Bip_R_Index2': 'RightHandIndex2',
    'J_Bip_L_Index3': 'LeftHandIndex3',
    'J_Bip_R_Index3': 'RightHandIndex3',
    'J_Bip_L_Middle1': 'LeftHandMiddle1',
    'J_Bip_R_Middle1': 'RightHandMiddle1',
    'J_Bip_L_Middle2': 'LeftHandMiddle2',
    'J_Bip_R_Middle2': 'RightHandMiddle2',
    'J_Bip_L_Middle3': 'LeftHandMiddle3',
    'J_Bip_R_Middle3': 'RightHandMiddle3',
    'J_Bip_L_Ring1': 'LeftHandRing1',
    'J_Bip_R_Ring1': 'RightHandRing1',
    'J_Bip_L_Ring2': 'LeftHandRing2',
    'J_Bip_R_Ring2': 'RightHandRing2',
    'J_Bip_L_Ring3': 'LeftHandRing3',
    'J_Bip_R_Ring3': 'RightHandRing3',
    'J_Bip_L_Little1': 'LeftHandPinky1',
    'J_Bip_R_Little1': 'RightHandPinky1',
    'J_Bip_L_Little2': 'LeftHandPinky2',
    'J_Bip_R_Little2': 'RightHandPinky2',
    'J_Bip_L_Little3': 'LeftHandPinky3',
    'J_Bip_R_Little3': 'RightHandPinky3',
    'LeftHandLittle1': 'LeftHandPinky1',
    'RightHandLittle1': 'RightHandPinky1',
    'LeftHandLittle2': 'LeftHandPinky2',
    'RightHandLittle2': 'RightHandPinky2',
    'LeftHandLittle3': 'LeftHandPinky3',
    'RightHandLittle3': 'RightHandPinky3',
    'J_Bip_L_Thumb1': 'LeftHandThumb1',
    'J_Bip_R_Thumb1': 'RightHandThumb1',
    'J_Bip_L_Thumb2': 'LeftHandThumb2',
    'J_Bip_R_Thumb2': 'RightHandThumb2',
    'J_Bip_L_Thumb3': 'LeftHandThumb3',
    'J_Bip_R_Thumb3': 'RightHandThumb3',
}

MORPH_MAP = {
    'Fcl_MTH_A': 'viseme_aa',
    'Fcl_MTH_I': 'viseme_I',
    'Fcl_MTH_U': 'viseme_U',
    'Fcl_MTH_E': 'viseme_E',
    'Fcl_MTH_O': 'viseme_O',
    'Fcl_MTH_Close': 'viseme_sil',
    'Fcl_ALL_Neutral': 'mood_neutral',
    'Fcl_ALL_Angry': 'mood_angry',
    'Fcl_ALL_Joy': 'mood_happy',
    'Fcl_ALL_Sorrow': 'mood_sad',
    'Fcl_ALL_Surprised': 'mood_surprised',
    'Fcl_ALL_Fun': 'mood_fun',
    'Fcl_EYE_Natural': 'eye_natural',
    'Fcl_EYE_Angry': 'browDownLeft',
    'Fcl_EYE_Close': 'eyeBlinkLeft',
    'Fcl_EYE_Close_R': 'eyeBlinkRight',
    'Fcl_EYE_Close_L': 'eyeBlinkLeft',
    'Fcl_EYE_Fun': 'eyeSquintLeft',
    'Fcl_EYE_Joy': 'eyeSquintLeft',
    'Fcl_EYE_Joy_R': 'eyeSquintRight',
    'Fcl_EYE_Joy_L': 'eyeSquintLeft',
    'Fcl_EYE_Sorrow': 'eyeSorrow',
    'Fcl_EYE_Surprised': 'eyeWideLeft',
    'Fcl_EYE_Spread': 'eyeWideRight',
    'Fcl_EYE_Iris_Hide': 'eyeLookOutLeft',
    'Fcl_EYE_Highlight_Hide': 'eyeLookInLeft',
    'Fcl_MTH_Up': 'mouthUpperUpLeft',
    'Fcl_MTH_Down': 'mouthLowerDownLeft',
    'Fcl_MTH_Angry': 'mouthPressLeft',
    'Fcl_MTH_Small': 'mouthPucker',
    'Fcl_MTH_Large': 'mouthOpen',
    'Fcl_MTH_Neutral': 'mouthClose',
    'Fcl_MTH_Fun': 'mouthSmileLeft',
    'Fcl_MTH_Joy': 'mouthSmile',
    'Fcl_MTH_Sorrow': 'mouthFrownLeft',
    'Fcl_MTH_Surprised': 'jawOpen',
    'Fcl_MTH_SkinFung': 'tongueOut',
    'Fcl_BRW_Angry': 'browDownLeft',
    'Fcl_BRW_Fun': 'browOuterUpLeft',
    'Fcl_BRW_Joy': 'browInnerUp',
    'Fcl_BRW_Sorrow': 'browInnerUp',
    'Fcl_BRW_Surprised': 'browOuterUpLeft',
    'Fcl_HA_Hide': 'noseSneerLeft',
}


def rename_morph_names(extras, log_list):
    if not extras:
        return
    target_names = extras.get('targetNames', [])
    if not target_names:
        return
    for i, name in enumerate(target_names):
        if name in MORPH_MAP:
            new_name = MORPH_MAP[name]
            if (name, new_name) not in log_list:
                log_list.append((name, new_name))
            target_names[i] = new_name


def process_glb(input_path, output_path):
    with open(input_path, 'rb') as f:
        magic = f.read(4)
        version = struct.unpack('<I', f.read(4))[0]
        length = struct.unpack('<I', f.read(4))[0]
        chunks = []
        while True:
            h = f.read(8)
            if len(h) < 8:
                break
            chunk_len = struct.unpack('<I', h[:4])[0]
            chunk_type = h[4:8]
            data = f.read(chunk_len)
            chunks.append({'type': chunk_type, 'data': data})

    gltf = json.loads(chunks[0]['data'].decode('utf-8'))
    nodes = gltf.get('nodes', [])

    bone_renames = []
    morph_renames = []

    # 1. Rename bone nodes
    for node in nodes:
        old_name = node.get('name', '')
        if old_name in BONE_MAP:
            new_name = BONE_MAP[old_name]
            node['name'] = new_name
            bone_renames.append((old_name, new_name))

    # 2. Rename Root → Armature
    if nodes and nodes[0].get('name') in ('Root', 'root', ''):
        old_root = nodes[0].get('name', '')
        nodes[0]['name'] = 'Armature'
        if old_root not in ('Armature',):
            bone_renames.insert(0, (old_root, 'Armature'))

    # 3. Rename morph targets
    for mesh in gltf.get('meshes', []):
        for prim in mesh.get('primitives', []):
            rename_morph_names(prim.get('extras', {}), morph_renames)

    # 4. Reorganize scene graph: make ALL non-bone scene nodes children of Armature
    # TalkingHead traverses armature.children to find morph targets, but VRM models
    # have mesh nodes (Face/Body/Hair) at scene root level. GLTFLoader with skinned
    # meshes handles reparenting differently, so we need EVERYTHING under Armature.
    armature_idx = None
    for i, node in enumerate(nodes):
        if node.get('name') == 'Armature':
            armature_idx = i
            break
    
    if armature_idx is not None:
        scene = gltf.get('scenes', [None])[0]
        if scene:
            scene_root_nodes = list(scene.get('nodes', []))
            armature_node = nodes[armature_idx]
            if 'children' not in armature_node:
                armature_node['children'] = []
            
            existing = set(armature_node['children'])
            added = []
            for idx in scene_root_nodes:
                if idx != armature_idx and idx not in existing:
                    armature_node['children'].append(idx)
                    added.append(idx)
            
            # Set scene root to only have Armature
            scene['nodes'] = [armature_idx]
            
            if added:
                print(f"\nReorganized scene: {len(added)} nodes moved under Armature")
                for idx in added:
                    print(f"  Node {idx}: {nodes[idx].get('name','?')} (mesh={nodes[idx].get('mesh','no')}, skin={nodes[idx].get('skin','no')})")

    # Print summary
    if bone_renames:
        renames_only = [(o, n) for o, n in bone_renames if '→' not in str(n)]
        reparents = [(o, n) for o, n in bone_renames if '→' in str(n)]
        if renames_only:
            print(f"Bone renames ({len(renames_only)}):")
            for old, new in renames_only:
                print(f"  {old:30s} → {new}")
        if reparents:
            for old, new in reparents:
                print(f"  {old:30s} {new}")
    else:
        print("No bone renames needed.")

    if morph_renames:
        print(f"\nMorph target renames ({len(morph_renames)}):")
        for old, new in morph_renames:
            print(f"  {old:30s} → {new}")
    else:
        print("No morph target renames needed.")

    # Verify morphs are now accessible under Armature
    armature_node = nodes[0]
    if armature_node.get('name') == 'Armature':
        print(f"\nArmature has {len(armature_node.get('children',[]))} children")
        for child_idx in armature_node.get('children', []):
            child = nodes[child_idx]
            print(f"  Child {child_idx}: {child.get('name','?')} (mesh={child.get('mesh','no')})")

    # Rebuild GLB
    new_json = json.dumps(gltf, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    while len(new_json) % 4 != 0:
        new_json += b' '

    with open(output_path, 'wb') as f:
        total_len = 12 + 8 + len(new_json) + sum(8 + len(c['data']) for c in chunks[1:])
        f.write(b'glTF')
        f.write(struct.pack('<I', version))
        f.write(struct.pack('<I', total_len))
        f.write(struct.pack('<I', len(new_json)))
        f.write(b'JSON')
        f.write(new_json)
        for chunk in chunks[1:]:
            f.write(struct.pack('<I', len(chunk['data'])))
            f.write(chunk['type'])
            f.write(chunk['data'])

    orig_size = os.path.getsize(input_path)
    new_size = os.path.getsize(output_path)
    print(f"\nOutput: {output_path} ({new_size} bytes, change: {new_size - orig_size:+d})")


if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'models/princess.glb'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'models/princess.glb'
    process_glb(input_file, output_file)

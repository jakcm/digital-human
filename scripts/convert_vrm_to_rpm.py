#!/usr/bin/env python3
"""
Comprehensive VRM → TalkingHead model conversion.
Renames bone nodes, morph target names, and adds missing finger joints
that TalkingHead requires but VRM models typically omit.

Missing finger joints needed by TalkingHead (present in RPM, absent in VRM):
  - Thumb2, Thumb3 (both hands)
  - Index2, Index3 (both hands)
  - Middle2, Middle3 (both hands)
  - Ring2, Ring3 (both hands)
  - VRM has Little1/2/3 (need to map to Pinky1/2/3)
"""
import json, struct, sys, os

# ── Bone name map ──
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
    # Index
    'J_Bip_L_Index1': 'LeftHandIndex1',
    'J_Bip_R_Index1': 'RightHandIndex1',
    'J_Bip_L_Index2': 'LeftHandIndex2',
    'J_Bip_R_Index2': 'RightHandIndex2',
    'J_Bip_L_Index3': 'LeftHandIndex3',
    'J_Bip_R_Index3': 'RightHandIndex3',
    # Middle
    'J_Bip_L_Middle1': 'LeftHandMiddle1',
    'J_Bip_R_Middle1': 'RightHandMiddle1',
    'J_Bip_L_Middle2': 'LeftHandMiddle2',
    'J_Bip_R_Middle2': 'RightHandMiddle2',
    'J_Bip_L_Middle3': 'LeftHandMiddle3',
    'J_Bip_R_Middle3': 'RightHandMiddle3',
    # Ring
    'J_Bip_L_Ring1': 'LeftHandRing1',
    'J_Bip_R_Ring1': 'RightHandRing1',
    'J_Bip_L_Ring2': 'LeftHandRing2',
    'J_Bip_R_Ring2': 'RightHandRing2',
    'J_Bip_L_Ring3': 'LeftHandRing3',
    'J_Bip_R_Ring3': 'RightHandRing3',
    # Little → Pinky
    'J_Bip_L_Little1': 'LeftHandPinky1',
    'J_Bip_R_Little1': 'RightHandPinky1',
    'J_Bip_L_Little2': 'LeftHandPinky2',
    'J_Bip_R_Little2': 'RightHandPinky2',
    'J_Bip_L_Little3': 'LeftHandPinky3',
    'J_Bip_R_Little3': 'RightHandPinky3',
    # Thumb
    'J_Bip_L_Thumb1': 'LeftHandThumb1',
    'J_Bip_R_Thumb1': 'RightHandThumb1',
    'J_Bip_L_Thumb2': 'LeftHandThumb2',
    'J_Bip_R_Thumb2': 'RightHandThumb2',
    'J_Bip_L_Thumb3': 'LeftHandThumb3',
    'J_Bip_R_Thumb3': 'RightHandThumb3',
}

# ── Missing finger joint definitions ──
# Each entry: (parent_name, missing_joint_name)
# These finger joints exist in Ready Player Me but NOT in VRM models
MISSING_FINGER_JOINTS = [
    # Left hand
    ('LeftHandThumb1', 'LeftHandThumb2'),
    ('LeftHandThumb2', 'LeftHandThumb3'),
    ('LeftHandIndex1', 'LeftHandIndex2'),
    ('LeftHandIndex2', 'LeftHandIndex3'),
    ('LeftHandMiddle1', 'LeftHandMiddle2'),
    ('LeftHandMiddle2', 'LeftHandMiddle3'),
    ('LeftHandRing1', 'LeftHandRing2'),
    ('LeftHandRing2', 'LeftHandRing3'),
    # Right hand
    ('RightHandThumb1', 'RightHandThumb2'),
    ('RightHandThumb2', 'RightHandThumb3'),
    ('RightHandIndex1', 'RightHandIndex2'),
    ('RightHandIndex2', 'RightHandIndex3'),
    ('RightHandMiddle1', 'RightHandMiddle2'),
    ('RightHandMiddle2', 'RightHandMiddle3'),
    ('RightHandRing1', 'RightHandRing2'),
    ('RightHandRing2', 'RightHandRing3'),
]

# ── Morph target name map ──
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
}

# Skirt/bust/secondary nodes that have no RPM equivalent but shouldn't be lost
# These are just kept as-is (they're secondary animation bones)


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


def add_synthetic_finger_joints(nodes, node_name_to_index):
    """
    Add missing finger joints as identity-transform nodes.
    Returns list of (parent_name, new_node_index, new_node_name) for logging.
    """
    added = []
    next_idx = len(nodes)

    for parent_name, child_name in MISSING_FINGER_JOINTS:
        # Check if this joint already exists in the node tree
        parent_idx = node_name_to_index.get(parent_name)
        if parent_idx is None:
            # Parent doesn't exist yet - might be one of our synthetic joints
            # Wait until parent is created
            continue

        # Check if child already exists
        if child_name in node_name_to_index:
            continue

        # Create a new identity-transform node
        new_node = {
            'name': child_name,
            'children': []
        }

        # Add it as child of parent
        parent_node = nodes[parent_idx]
        if 'children' not in parent_node:
            parent_node['children'] = []
        parent_node['children'].append(next_idx)

        nodes.append(new_node)
        node_name_to_index[child_name] = next_idx
        added.append((parent_name, next_idx, child_name))
        next_idx += 1

    return added


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

    # 4. Add missing finger joints
    # Build name→index map
    node_name_to_index = {}
    for i, node in enumerate(nodes):
        name = node.get('name', '')
        node_name_to_index[name] = i

    # Add synthetic joints in passes (to handle chains like Thumb1→Thumb2→Thumb3)
    added_joints = []
    for pass_num in range(3):  # Up to 3 passes for chains
        new_additions = add_synthetic_finger_joints(nodes, node_name_to_index)
        added_joints.extend(new_additions)
        if not new_additions:
            break

    # Print summary
    if bone_renames:
        print(f"Bone renames ({len(bone_renames)}):")
        for old, new in bone_renames:
            print(f"  {old:30s} → {new}")
    else:
        print("No bone renames needed.")

    if added_joints:
        print(f"\nAdded synthetic finger joints ({len(added_joints)}):")
        for parent, idx, name in added_joints:
            print(f"  Node {idx}: {name} (child of {parent})")
    else:
        print("\nNo synthetic joints needed.")

    if morph_renames:
        print(f"\nMorph target renames ({len(morph_renames)}):")
        for old, new in morph_renames:
            print(f"  {old:30s} → {new}")
    else:
        print("No morph target renames needed.")

    # Show VRM presets
    vrm_ext = gltf.get('extensions', {}).get('VRM', {})
    if vrm_ext:
        preset_map = {}
        for bg in vrm_ext.get('blendShapeMaster', {}).get('blendShapeGroups', []):
            preset_map[bg.get('presetName', '?')] = bg.get('name', '?')
        print(f"\nVRM presets: {json.dumps(preset_map, indent=2)}")

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

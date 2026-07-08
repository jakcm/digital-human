#!/usr/bin/env python3
"""
Comprehensive VRM → TalkingHead model conversion.
Renames bone nodes AND morph target (blendshape) names so the princess
model works with TalkingHead's ARKit/Oculus naming conventions.

Key mappings:
  VRM bone J_Bip_C_Hips → Hips (etc.)
  VRM morph Fcl_MTH_A → viseme_aa (for lipsync)
  VRM morph Fcl_ALL_Joy → mood_happy (for mood expressions)
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
    'J_Bip_L_Index1': 'LeftHandIndex1',
    'J_Bip_R_Index1': 'RightHandIndex1',
    'J_Bip_L_Middle1': 'LeftHandMiddle1',
    'J_Bip_R_Middle1': 'RightHandMiddle1',
    'J_Bip_L_Ring1': 'LeftHandRing1',
    'J_Bip_R_Ring1': 'RightHandRing1',
    'J_Bip_L_Little1': 'LeftHandLittle1',
    'J_Bip_R_Little1': 'RightHandLittle1',
    'J_Bip_L_Thumb1': 'LeftHandThumb1',
    'J_Bip_R_Thumb1': 'RightHandThumb1',
}

# ── Morph target name map (VRM Fcl_* → TalkingHead/ARKit) ──
# Viseme names (for lipsync) - the most critical ones
MORPH_MAP = {
    'Fcl_MTH_A': 'viseme_aa',
    'Fcl_MTH_I': 'viseme_I',
    'Fcl_MTH_U': 'viseme_U',
    'Fcl_MTH_E': 'viseme_E',
    'Fcl_MTH_O': 'viseme_O',
    'Fcl_MTH_Close': 'viseme_sil',

    # Combined expressions → mood prefix for TalkingHead mood system
    'Fcl_ALL_Neutral': 'mood_neutral',
    'Fcl_ALL_Angry': 'mood_angry',
    'Fcl_ALL_Joy': 'mood_happy',
    'Fcl_ALL_Sorrow': 'mood_sad',
    'Fcl_ALL_Surprised': 'mood_surprised',
    'Fcl_ALL_Fun': 'mood_fun',

    # Eye shapes → ARKit eye names
    'Fcl_EYE_Natural': 'eye_natural',
    'Fcl_EYE_Angry': 'browDownLeft',  # approximate
    'Fcl_EYE_Close': 'eyeBlinkLeft',
    'Fcl_EYE_Close_R': 'eyeBlinkRight',
    'Fcl_EYE_Close_L': 'eyeBlinkLeft',
    'Fcl_EYE_Joy': 'eyeSquintLeft',
    'Fcl_EYE_Joy_R': 'eyeSquintRight',
    'Fcl_EYE_Joy_L': 'eyeSquintLeft',
    'Fcl_EYE_Sorrow': 'eyeSorrow',
    'Fcl_EYE_Surprised': 'eyeWideLeft',
    'Fcl_EYE_Spread': 'eyeWideRight',

    # Mouth shapes → ARKit mouth names (approximate mappings)
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

    # Brow shapes → ARKit brow names
    'Fcl_BRW_Angry': 'browDownLeft',
    'Fcl_BRW_Fun': 'browOuterUpLeft',
    'Fcl_BRW_Joy': 'browInnerUp',
    'Fcl_BRW_Sorrow': 'browInnerUp',
    'Fcl_BRW_Surprised': 'browOuterUpLeft',
}


def rename_morph_names(extras, log_list):
    """Rename morph target names in extras.targetNames array"""
    if not extras:
        return
    target_names = extras.get('targetNames', [])
    if not target_names:
        return
    renamed = False
    for i, name in enumerate(target_names):
        if name in MORPH_MAP:
            new_name = MORPH_MAP[name]
            target_names[i] = new_name
            log_list.append((name, new_name))
            renamed = True
    if renamed:
        extras['targetNames'] = target_names


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

    # 3. Rename morph targets in all mesh primitives
    meshes = gltf.get('meshes', [])
    for mesh in meshes:
        for prim in mesh.get('primitives', []):
            extras = prim.get('extras', {})
            rename_morph_names(extras, morph_renames)

    # Print summary
    if bone_renames:
        print(f"Bone renames ({len(bone_renames)}):")
        for old, new in bone_renames:
            print(f"  {old:30s} → {new}")
    else:
        print("No bone renames needed.")

    if morph_renames:
        print(f"\nMorph target renames ({len(morph_renames)}):")
        for old, new in morph_renames:
            print(f"  {old:30s} → {new}")
    else:
        print("No morph target renames needed.")

    # 4. Show VRM 0.x blendShapeGroups info for reference
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

import os
import re
from glob import glob

def main():
    # --- 配置路径 ---
    PROJECT_ROOT = os.getcwd()
    
    # 模板文件路径
    TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "assets/obj_urdf_example.urdf")
    
    # COACD 生成结果的目录 (即上一步的输出目录)
    COACD_ROOT = os.path.join(PROJECT_ROOT, "data/OakInk-v2/coacd_object_preview/align_ds")

    # --- 检查模板 ---
    if not os.path.exists(TEMPLATE_PATH):
        print(f"错误: 找不到模板文件: {TEMPLATE_PATH}")
        # 如果模板不存在，这里提供一个默认的备用模板内容
        print("尝试使用默认内容...")
        template_content = """<?xml version="1.0"?>
<robot name="object">
  <link name="object">
    <visual>
      <origin xyz="0 0 0"/>
      <geometry>
        <mesh filename="PLACEHOLDER"/>
      </geometry>
    </visual>
    <collision>
      <origin xyz="0 0 0"/>
      <geometry>
        <mesh filename="PLACEHOLDER"/>
      </geometry>
    </collision>
    <inertial>
      <density value="100.0"/>
    </inertial>
  </link>
</robot>
"""
    else:
        with open(TEMPLATE_PATH, 'r') as f:
            template_content = f.read()

    print(f"开始为 {COACD_ROOT} 下的模型生成 URDF...")

    # --- 遍历目录 ---
    tasks = []
    for root, dirs, files in os.walk(COACD_ROOT):
        for file in files:
            if file.endswith(".obj") or file.endswith(".ply"):
                mesh_path = os.path.join(root, file)
                # URDF 文件名与模型同名，只是后缀不同
                urdf_name = os.path.splitext(file)[0] + ".urdf"
                urdf_path = os.path.join(root, urdf_name)
                tasks.append((file, urdf_path))

    total_files = len(tasks)
    print(f"找到 {total_files} 个模型文件。")

    # --- 批量生成 ---
    count = 0
    for mesh_filename, urdf_path in tasks:
        # 使用正则表达式替换 filename="..." 的内容
        # 这样无论模板里原来写的是什么路径，都会被替换成当前目录下的文件名
        # 例如：filename="/tmp/old.obj" -> filename="001.obj"
        
        # 1. 替换 filename="..."
        new_content = re.sub(r'filename=".*?"', f'filename="{mesh_filename}"', template_content)
        
        # 2. 也就是确保 URDF 和 OBJ 在同一目录下时，URDF 能引用到 OBJ
        
        with open(urdf_path, 'w') as f:
            f.write(new_content)
        
        count += 1
        if count % 100 == 0:
            print(f"已生成 {count}/{total_files} ...")

    print("\n" + "="*30)
    print("URDF 生成完成！")
    print(f"共生成: {count} 个文件")
    print("="*30)

if __name__ == "__main__":
    main()

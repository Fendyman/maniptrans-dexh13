import os
import subprocess
import argparse
from glob import glob

def main():
    # --- 配置路径 ---
    # 你的项目根目录
    PROJECT_ROOT = os.getcwd()
    
    # COACD 处理脚本的路径
    SCRIPT_PATH = os.path.join(PROJECT_ROOT, "maniptrans_envs/lib/utils/coacd_process.py")
    
    # 输入数据的根目录 (物体模型)
    INPUT_ROOT = os.path.join(PROJECT_ROOT, "data/OakInk-v2/object_preview/align_ds")
    
    # 输出数据的根目录 (生成的 COACD 模型)
    OUTPUT_ROOT = os.path.join(PROJECT_ROOT, "data/OakInk-v2/coacd_object_preview/align_ds")

    # --- 检查环境 ---
    if not os.path.exists(SCRIPT_PATH):
        print(f"错误: 找不到处理脚本: {SCRIPT_PATH}")
        print("请确保你在项目根目录 (ManipTrans) 下运行此脚本。")
        return

    if not os.path.exists(INPUT_ROOT):
        print(f"错误: 找不到输入目录: {INPUT_ROOT}")
        print("请检查数据是否已正确下载并解压。")
        return

    print(f"开始扫描目录: {INPUT_ROOT} ...")

    # --- 收集任务 ---
    tasks = []
    # 遍历所有子目录寻找 .obj 和 .ply 文件
    for root, dirs, files in os.walk(INPUT_ROOT):
        for file in files:
            if file.endswith(".obj") or file.endswith(".ply"):
                # 获取源文件绝对路径
                src_path = os.path.join(root, file)
                
                # 计算相对路径，以便在输出目录保持相同的结构
                rel_path = os.path.relpath(src_path, INPUT_ROOT)
                
                # 构建输出文件路径
                target_path = os.path.join(OUTPUT_ROOT, rel_path)
                
                tasks.append((src_path, target_path))

    total_tasks = len(tasks)
    print(f"共发现 {total_tasks} 个模型文件需要处理。")

    # --- 开始批量处理 ---
    success_count = 0
    fail_count = 0

    for idx, (src, target) in enumerate(tasks):
        # 打印进度
        print(f"[{idx+1}/{total_tasks}] Processing: {os.path.basename(src)}")

        # 1. 确保目标文件夹存在
        os.makedirs(os.path.dirname(target), exist_ok=True)

        # 2. 如果目标文件已存在，跳过（方便断点续传）
        if os.path.exists(target):
            print(f"  -> 跳过 (文件已存在)")
            success_count += 1
            continue

        # 3. 构建命令 (严格按照 README 参数)
        cmd = [
            "python", SCRIPT_PATH,
            "-i", src,
            "-o", target,
            "--max-convex-hull", "32",
            "--seed", "1",
            "-mi", "2000",
            "-md", "5",
            "-t", "0.07"
        ]

        try:
            # 执行命令，隐藏标准输出以免刷屏，只显示错误
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"  -> 错误: 处理失败 {src}")
            fail_count += 1
        except Exception as e:
            print(f"  -> 发生未知错误: {e}")
            fail_count += 1

    # --- 总结 ---
    print("\n" + "="*30)
    print("处理完成！")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"输出目录: {OUTPUT_ROOT}")
    print("="*30)

if __name__ == "__main__":
    main()

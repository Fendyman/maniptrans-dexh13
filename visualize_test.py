"""
简单的测试脚本 - 在无渲染模式下运行测试并输出统计结果
"""
import torch
import sys
sys.path.insert(0, '.')

# 运行测试
if __name__ == "__main__":
    import subprocess
    
    cmd = [
        "python", "main/rl/train.py",
        "task=ResDexHand",
        "dexhand=dexh13",
        "side=RH",
        "headless=true",
        "num_envs=4",
        "test=true",
        "randomStateInit=false",
        "dataIndices=[g0]",
        "usePIDControl=True",
        "actionsMovingAverage=0.4",
        "rh_base_model_checkpoint=runs/imitator_dexh13_rh__12-29-16-00-45/nn/last_imitator_dexh13_rh_ep_1000_rew__18.06_.pth",
        "checkpoint=runs/cross_g0_dexh13__12-29-17-41-28/nn/cross_g0_dexh13.pth",
        "num_rollouts_to_run=20"
    ]
    
    print("Running test with dexh13 hand...")
    print(" ".join(cmd))
    subprocess.run(cmd)

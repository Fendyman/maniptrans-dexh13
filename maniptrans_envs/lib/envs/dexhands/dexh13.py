from .base import DexHand
from .decorators import register_dexhand
from abc import ABC, abstractmethod
import numpy as np
from main.dataset.transform import aa_to_rotmat


class Dexh13(DexHand, ABC):
    """
    Dexh13 灵巧手配置类
    
    该灵巧手有4个手指（食指、中指、无名指、拇指），每个手指4个关节
    - 食指: right_index_joint_0/1/2/3 (joint_0控制侧向摆动，joint_1/2/3控制弯曲)
    - 中指: right_middle_joint_0/1/2/3
    - 无名指: right_ring_joint_0/1/2/3  
    - 拇指: right_thumb_joint_0/1/2/3
    
    注意：该手没有小指(pinky)
    URDF中包含tactile links (fixed joints)，共28个bodies
    """
    def __init__(self):
        super().__init__()
        self._urdf_path = None
        self.side = None
        self.name = "dexh13"
        self.self_collision = True
        
        # 基础body名称（不带前缀）- 按URDF中的顺序排列，共28个bodies
        # 包括所有tactile links (通过fixed joint连接)
        self.body_names = [
            "palm_link",                    # 0
            # 食指 (indices 1-7)
            "index_link_0",                 # 1
            "index_link_1",                 # 2
            "index_link_2",                 # 3
            "index_link_3",                 # 4
            "index_tactile_link_2",         # 5
            "index_tactile_link_1",         # 6
            "index_tactile_link_0",         # 7
            # 中指 (indices 8-14)
            "middle_link_0",                # 8
            "middle_link_1",                # 9
            "middle_link_2",                # 10
            "middle_link_3",                # 11
            "middle_tactile_link_2",        # 12
            "middle_tactile_link_1",        # 13
            "middle_tactile_link_0",        # 14
            # 无名指 (indices 15-21)
            "ring_link_0",                  # 15
            "ring_link_1",                  # 16
            "ring_link_2",                  # 17
            "ring_link_3",                  # 18
            "ring_tactile_link_2",          # 19
            "ring_tactile_link_1",          # 20
            "ring_tactile_link_0",          # 21
            # 拇指 (indices 22-27)
            "thumb_link_0",                 # 22
            "thumb_link_1",                 # 23
            "thumb_link_2",                 # 24
            "thumb_link_3",                 # 25
            "thumb_tactile_link_1",         # 26
            "thumb_tactile_link_0",         # 27
        ]
        
        # 基础DOF名称（不带前缀）
        self.dof_names = [
            # 食指 4个DOF
            "index_joint_0",
            "index_joint_1",
            "index_joint_2",
            "index_joint_3",
            # 中指 4个DOF
            "middle_joint_0",
            "middle_joint_1",
            "middle_joint_2",
            "middle_joint_3",
            # 无名指 4个DOF
            "ring_joint_0",
            "ring_joint_1",
            "ring_joint_2",
            "ring_joint_3",
            # 拇指 4个DOF
            "thumb_joint_0",
            "thumb_joint_1",
            "thumb_joint_2",
            "thumb_joint_3",
        ]
        
        # MANO手到Dexh13的映射
        # Dexh13没有小指，所以pinky映射到ring（无名指）
        # 包括tactile links的映射
        self.hand2dex_mapping = {
            "wrist": ["palm_link"],
            # 拇指
            "thumb_proximal": ["thumb_link_0", "thumb_link_1", "thumb_tactile_link_0"],  # one-to-many mapping
            "thumb_intermediate": ["thumb_link_2"],
            "thumb_distal": ["thumb_link_3", "thumb_tactile_link_1"],
            "thumb_tip": ["thumb_link_3"],  # 没有单独的tip link，使用最后一节
            # 食指
            "index_proximal": ["index_link_0", "index_link_1", "index_tactile_link_0"],
            "index_intermediate": ["index_link_2", "index_tactile_link_1"],
            "index_distal": ["index_link_3", "index_tactile_link_2"],
            "index_tip": ["index_link_3"],
            # 中指
            "middle_proximal": ["middle_link_0", "middle_link_1", "middle_tactile_link_0"],
            "middle_intermediate": ["middle_link_2", "middle_tactile_link_1"],
            "middle_distal": ["middle_link_3", "middle_tactile_link_2"],
            "middle_tip": ["middle_link_3"],
            # 无名指
            "ring_proximal": ["ring_link_0", "ring_link_1", "ring_tactile_link_0"],
            "ring_intermediate": ["ring_link_2", "ring_tactile_link_1"],
            "ring_distal": ["ring_link_3", "ring_tactile_link_2"],
            "ring_tip": ["ring_link_3"],
            # 小指 - 映射到无名指（因为dexh13没有小指）
            "pinky_proximal": ["ring_link_0", "ring_link_1"],
            "pinky_intermediate": ["ring_link_2"],
            "pinky_distal": ["ring_link_3"],
            "pinky_tip": ["ring_link_3"],
        }
        
        self.dex2hand_mapping = self.reverse_mapping(self.hand2dex_mapping)
        
        # 接触体名称（用于力反馈）- 使用tactile link会更准确
        self.contact_body_names = [
            "thumb_link_3",
            "index_link_3",
            "middle_link_3",
            "ring_link_3",
            "ring_link_3",  # pinky映射到ring
        ]
        
        # 骨骼连接关系（用于可视化）
        # 使用新的索引: palm=0, index=1-4(7), middle=8-11(14), ring=15-18(21), thumb=22-25(27)
        self.bone_links = [
            [0, 1],   # palm to index_0
            [0, 8],   # palm to middle_0
            [0, 15],  # palm to ring_0
            [0, 22],  # palm to thumb_0
            # 食指链
            [1, 2],
            [2, 3],
            [3, 4],
            # 中指链
            [8, 9],
            [9, 10],
            [10, 11],
            # 无名指链
            [15, 16],
            [16, 17],
            [17, 18],
            # 拇指链
            [22, 23],
            [23, 24],
            [24, 25],
        ]
        
        # 权重索引（用于损失计算）- 使用新索引
        self.weight_idx = {
            "thumb_tip": [25],
            "index_tip": [4],
            "middle_tip": [11],
            "ring_tip": [18],
            "pinky_tip": [18],  # 映射到ring
            "level_1_joints": [1, 2, 8, 9, 15, 16, 22, 23],
            "level_2_joints": [3, 4, 10, 11, 17, 18, 24, 25],
        }

        # PID控制参数（用于PID控制模式）
        self.Kp_rot = 0.3
        self.Ki_rot = 0.001
        self.Kd_rot = 0.005
        self.Kp_pos = 20
        self.Ki_pos = 0.01
        self.Kd_pos = 2

    def __str__(self):
        return self.name


@register_dexhand("dexh13_rh")
class Dexh13RH(Dexh13):
    """Dexh13 右手"""
    def __init__(self):
        super().__init__()
        self._urdf_path = "assets/dexh13_hand/dexh13_hand_right.urdf"
        self.side = "rh"
        
        # 添加 "right_" 前缀
        self.body_names = ["right_" + name for name in self.body_names]
        self.dof_names = ["right_" + name for name in self.dof_names]
        
        # 相对旋转矩阵 - 将MANO坐标系转换到dexh13坐标系
        # 根据URDF分析，dexh13的palm朝向是X轴正方向，手指伸展方向
        # 需要根据实际测试调整这个旋转
        self.relative_rotation = (
            aa_to_rotmat(np.array([np.pi, 0, 0])) 
            @ aa_to_rotmat(np.array([0, np.pi / 2, 0]))
        )
        
        # 更新mapping中的前缀
        self.hand2dex_mapping = {k: ["right_" + dex_v for dex_v in v] for k, v in self.hand2dex_mapping.items()}
        self.dex2hand_mapping = self.reverse_mapping(self.hand2dex_mapping)
        self.contact_body_names = ["right_" + name for name in self.contact_body_names]

    def __str__(self):
        return super().__str__() + "_rh"


@register_dexhand("dexh13_lh") 
class Dexh13LH(Dexh13):
    """
    Dexh13 左手
    注意：当前只有右手URDF，左手需要另外创建镜像URDF
    如果没有左手URDF，可以暂时使用右手URDF作为占位符
    """
    def __init__(self):
        super().__init__()
        # 如果有左手URDF，修改这个路径
        # 目前使用右手URDF作为占位符（实际使用时需要创建左手URDF）
        self._urdf_path = "assets/dexh13_hand/dexh13_hand_left.urdf"
        self.side = "lh"
        
        # 添加 "left_" 前缀
        self.body_names = ["left_" + name for name in self.body_names]
        self.dof_names = ["left_" + name for name in self.dof_names]
        
        # 左手的相对旋转
        self.relative_rotation = aa_to_rotmat(np.array([0, -np.pi / 2, 0]))
        
        # 更新mapping中的前缀
        self.hand2dex_mapping = {k: ["left_" + dex_v for dex_v in v] for k, v in self.hand2dex_mapping.items()}
        self.dex2hand_mapping = self.reverse_mapping(self.hand2dex_mapping)
        self.contact_body_names = ["left_" + name for name in self.contact_body_names]

    def __str__(self):
        return super().__str__() + "_lh"

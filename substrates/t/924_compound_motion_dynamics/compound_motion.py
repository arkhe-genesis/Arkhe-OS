#!/usr/bin/env python3
# compound_motion.py — Substrate 924
# Compound Motion Dynamics: SE(3) kinematics, Featherstone dynamics, differentiable physics

import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import numpy as np

# ═══════════════════════════════════════════════════════════════════
# SE(3) Lie Group Operations
# ═══════════════════════════════════════════════════════════════════

class SE3Ops:
    """Static operations on SE(3) rigid body transformations."""

    @staticmethod
    def quaternion_to_rotation_matrix(q: torch.Tensor) -> torch.Tensor:
        """Convert quaternion [w, x, y, z] to rotation matrix [3, 3]."""
        # q: [batch, 4] or [4]
        if q.dim() == 1:
            q = q.unsqueeze(0)
        w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]

        R = torch.zeros(q.size(0), 3, 3, device=q.device, dtype=q.dtype)
        R[:, 0, 0] = 1 - 2*(y**2 + z**2)
        R[:, 0, 1] = 2*(x*y - w*z)
        R[:, 0, 2] = 2*(x*z + w*y)
        R[:, 1, 0] = 2*(x*y + w*z)
        R[:, 1, 1] = 1 - 2*(x**2 + z**2)
        R[:, 1, 2] = 2*(y*z - w*x)
        R[:, 2, 0] = 2*(x*z - w*y)
        R[:, 2, 1] = 2*(y*z + w*x)
        R[:, 2, 2] = 1 - 2*(x**2 + y**2)
        return R.squeeze(0) if R.size(0) == 1 else R

    @staticmethod
    def rotation_matrix_to_quaternion(R: torch.Tensor) -> torch.Tensor:
        """Convert rotation matrix [3, 3] to quaternion [w, x, y, z]."""
        if R.dim() == 2:
            R = R.unsqueeze(0)
        batch = R.size(0)
        q = torch.zeros(batch, 4, device=R.device, dtype=R.dtype)

        trace = R[:, 0, 0] + R[:, 1, 1] + R[:, 2, 2]

        # Case 1: trace > 0
        mask1 = trace > 0
        s1 = torch.sqrt(trace[mask1] + 1.0) * 2
        q[mask1, 0] = 0.25 * s1
        q[mask1, 1] = (R[mask1, 2, 1] - R[mask1, 1, 2]) / s1
        q[mask1, 2] = (R[mask1, 0, 2] - R[mask1, 2, 0]) / s1
        q[mask1, 3] = (R[mask1, 1, 0] - R[mask1, 0, 1]) / s1

        # Case 2: R[0,0] is largest
        mask2 = (~mask1) & (R[:, 0, 0] > R[:, 1, 1]) & (R[:, 0, 0] > R[:, 2, 2])
        s2 = torch.sqrt(1.0 + R[mask2, 0, 0] - R[mask2, 1, 1] - R[mask2, 2, 2]) * 2
        q[mask2, 0] = (R[mask2, 2, 1] - R[mask2, 1, 2]) / s2
        q[mask2, 1] = 0.25 * s2
        q[mask2, 2] = (R[mask2, 0, 1] + R[mask2, 1, 0]) / s2
        q[mask2, 3] = (R[mask2, 0, 2] + R[mask2, 2, 0]) / s2

        # Case 3: R[1,1] is largest
        mask3 = (~mask1) & (~mask2) & (R[:, 1, 1] > R[:, 2, 2])
        s3 = torch.sqrt(1.0 + R[mask3, 1, 1] - R[mask3, 0, 0] - R[mask3, 2, 2]) * 2
        q[mask3, 0] = (R[mask3, 0, 2] - R[mask3, 2, 0]) / s3
        q[mask3, 1] = (R[mask3, 0, 1] + R[mask3, 1, 0]) / s3
        q[mask3, 2] = 0.25 * s3
        q[mask3, 3] = (R[mask3, 1, 2] + R[mask3, 2, 1]) / s3

        # Case 4: R[2,2] is largest
        mask4 = (~mask1) & (~mask2) & (~mask3)
        s4 = torch.sqrt(1.0 + R[mask4, 2, 2] - R[mask4, 0, 0] - R[mask4, 1, 1]) * 2
        q[mask4, 0] = (R[mask4, 1, 0] - R[mask4, 0, 1]) / s4
        q[mask4, 1] = (R[mask4, 0, 2] + R[mask4, 2, 0]) / s4
        q[mask4, 2] = (R[mask4, 1, 2] + R[mask4, 2, 1]) / s4
        q[mask4, 3] = 0.25 * s4

        return q.squeeze(0) if q.size(0) == 1 else q

    @staticmethod
    def pose_from_quat_translation(q: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        """Build SE(3) matrix [4, 4] from quaternion and translation."""
        R = SE3Ops.quaternion_to_rotation_matrix(q)
        if R.dim() == 2:
            R = R.unsqueeze(0)
            t = t.unsqueeze(0)
        T = torch.eye(4, device=q.device, dtype=q.dtype).unsqueeze(0).repeat(R.size(0), 1, 1)
        T[:, :3, :3] = R
        T[:, :3, 3] = t
        return T.squeeze(0) if T.size(0) == 1 else T

    @staticmethod
    def pose_inverse(T: torch.Tensor) -> torch.Tensor:
        """Inverse of SE(3) matrix."""
        if T.dim() == 2:
            T = T.unsqueeze(0)
        R = T[:, :3, :3]
        t = T[:, :3, 3]
        R_inv = R.transpose(-2, -1)
        t_inv = -(R_inv @ t.unsqueeze(-1)).squeeze(-1)
        T_inv = torch.eye(4, device=T.device, dtype=T.dtype).unsqueeze(0).repeat(T.size(0), 1, 1)
        T_inv[:, :3, :3] = R_inv
        T_inv[:, :3, 3] = t_inv
        return T_inv.squeeze(0) if T_inv.size(0) == 1 else T_inv

    @staticmethod
    def adjoint(T: torch.Tensor) -> torch.Tensor:
        """Adjoint representation of SE(3) [6, 6]."""
        if T.dim() == 2:
            T = T.unsqueeze(0)
        R = T[:, :3, :3]
        t = T[:, :3, 3]
        t_skew = torch.zeros(T.size(0), 3, 3, device=T.device, dtype=T.dtype)
        t_skew[:, 0, 1] = -t[:, 2]
        t_skew[:, 0, 2] = t[:, 1]
        t_skew[:, 1, 0] = t[:, 2]
        t_skew[:, 1, 2] = -t[:, 0]
        t_skew[:, 2, 0] = -t[:, 1]
        t_skew[:, 2, 1] = t[:, 0]

        Ad = torch.zeros(T.size(0), 6, 6, device=T.device, dtype=T.dtype)
        Ad[:, :3, :3] = R
        Ad[:, 3:, 3:] = R
        Ad[:, 3:, :3] = t_skew @ R
        return Ad.squeeze(0) if Ad.size(0) == 1 else Ad

    @staticmethod
    def quaternion_multiply(q1: torch.Tensor, q2: torch.Tensor) -> torch.Tensor:
        """Hamilton product of two quaternions."""
        w1, x1, y1, z1 = q1[0], q1[1], q1[2], q1[3]
        w2, x2, y2, z2 = q2[0], q2[1], q2[2], q2[3]
        return torch.stack([
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2
        ])


# ═══════════════════════════════════════════════════════════════════
# Joint & Link Definitions
# ═══════════════════════════════════════════════════════════════════

@dataclass
class JointConfig:
    """Configuration for a single joint in the kinematic tree."""
    name: str
    joint_type: str  # 'revolute', 'prismatic', 'spherical', 'fixed'
    axis: torch.Tensor  # [3] — axis of motion in parent frame
    parent_link: int = -1  # -1 = base
    child_link: int = 0
    position: torch.Tensor = field(default_factory=lambda: torch.zeros(3))  # [3] in parent frame
    quaternion: torch.Tensor = field(default_factory=lambda: torch.tensor([1., 0., 0., 0.]))  # [4]
    limits: Optional[Tuple[float, float]] = None  # (min, max) in radians or meters
    damping: float = 0.1
    friction: float = 0.05

    def __post_init__(self):
        if isinstance(self.axis, list):
            self.axis = torch.tensor(self.axis, dtype=torch.float32)
        if isinstance(self.position, list):
            self.position = torch.tensor(self.position, dtype=torch.float32)
        if isinstance(self.quaternion, list):
            self.quaternion = torch.tensor(self.quaternion, dtype=torch.float32)
        self.axis = self.axis / (self.axis.norm() + 1e-8)


@dataclass
class LinkConfig:
    """Inertial properties of a rigid link."""
    name: str
    mass: float = 1.0
    com: torch.Tensor = field(default_factory=lambda: torch.zeros(3))  # center of mass
    inertia: torch.Tensor = field(default_factory=lambda: torch.eye(3))  # [3, 3] at COM
    collision_geometry: Optional[str] = None  # 'sphere', 'box', 'capsule'
    collision_params: Dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════
# Compound Motion Engine
# ═══════════════════════════════════════════════════════════════════

class CompoundMotionEngine(nn.Module):
    """Substrate 924 — Compound Motion Dynamics Engine

    Differentiable articulated body dynamics using:
    - Forward kinematics in SE(3)
    - Recursive Newton-Euler Algorithm (RNEA) for inverse dynamics
    - Articulated Body Algorithm (ABA) for forward dynamics
    - Contact handling via penalty forces
    """

    def __init__(self, joints: List[JointConfig], links: List[LinkConfig],
                 gravity: torch.Tensor = None, dt: float = 0.01):
        super().__init__()
        self.joints = joints
        self.links = links
        self.n_joints = len(joints)
        self.n_links = len(links)
        self.dt = dt
        self.gravity = gravity if gravity is not None else torch.tensor([0., 0., -9.81])

        # Learnable inertial parameters
        self.link_masses = nn.Parameter(torch.tensor([l.mass for l in links]))
        self.link_com = nn.Parameter(torch.stack([l.com for l in links]))
        self.link_inertia = nn.Parameter(torch.stack([
            l.inertia for l in links
        ]))

        # Joint properties
        self.joint_damping = nn.Parameter(torch.tensor([j.damping for j in joints]))
        self.joint_friction = nn.Parameter(torch.tensor([j.friction for j in joints]))

        # SE(3) transforms at rest configuration (T_parent_child at q=0)
        self.register_buffer('rest_transforms', self._compute_rest_transforms())

        # Encoder for world model integration
        self.state_encoder = nn.Sequential(
            nn.Linear(self.n_links * 13, 512),  # 13 = 4(quat) + 3(pos) + 3(linvel) + 3(angvel)
            nn.LayerNorm(512),
            nn.GELU(),
            nn.Linear(512, 256)
        )

    def _compute_rest_transforms(self) -> torch.Tensor:
        """Compute SE(3) transforms for each joint at zero configuration."""
        transforms = []
        for j in self.joints:
            T = SE3Ops.pose_from_quat_translation(j.quaternion, j.position)
            transforms.append(T)
        return torch.stack(transforms)  # [n_joints, 4, 4]

    def forward_kinematics(self, joint_angles: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward kinematics: compute global poses, velocities, accelerations.

        Args:
            joint_angles: [batch, n_joints]

        Returns:
            poses: [batch, n_links, 4, 4] — global SE(3) for each link
            positions: [batch, n_links, 3] — global positions
            orientations: [batch, n_links, 4] — global quaternions
        """
        batch = joint_angles.shape[0]
        device = joint_angles.device

        poses = torch.zeros(batch, self.n_links, 4, 4, device=device)
        positions = torch.zeros(batch, self.n_links, 3, device=device)
        orientations = torch.zeros(batch, self.n_links, 4, device=device)

        for i, joint in enumerate(self.joints):
            # Get joint transform based on type and angle
            if joint.joint_type == 'revolute':
                angle = joint_angles[:, i]
                axis = joint.axis.to(device)
                # Rodrigues rotation
                K = torch.zeros(3, 3, device=device)
                K[0, 1] = -axis[2]
                K[0, 2] = axis[1]
                K[1, 0] = axis[2]
                K[1, 2] = -axis[0]
                K[2, 0] = -axis[1]
                K[2, 1] = axis[0]

                sin_a = torch.sin(angle)
                cos_a = torch.cos(angle)
                R = torch.eye(3, device=device).unsqueeze(0).repeat(batch, 1, 1)
                R += sin_a.unsqueeze(-1).unsqueeze(-1) * K.unsqueeze(0)
                R += (1 - cos_a).unsqueeze(-1).unsqueeze(-1) * (K @ K).unsqueeze(0)

                T_joint = torch.eye(4, device=device).unsqueeze(0).repeat(batch, 1, 1)
                T_joint[:, :3, :3] = R
                T_joint[:, :3, 3] = joint.position.to(device)

            elif joint.joint_type == 'prismatic':
                disp = joint_angles[:, i].unsqueeze(-1) * joint.axis.to(device)
                T_joint = torch.eye(4, device=device).unsqueeze(0).repeat(batch, 1, 1)
                T_joint[:, :3, 3] = joint.position.to(device) + disp

            elif joint.joint_type == 'spherical':
                # Use quaternion directly (3 DOF)
                q = joint_angles[:, i*3:(i+1)*3] if joint_angles.shape[1] >= (i+1)*3 else torch.zeros(batch, 3, device=device)
                # Convert rotation vector to quaternion
                theta = q.norm(dim=-1, keepdim=True)
                w = torch.cos(theta / 2)
                xyz = torch.sin(theta / 2) * q / (theta + 1e-8)
                quat = torch.cat([w, xyz], dim=-1)
                T_joint = SE3Ops.pose_from_quat_translation(quat, joint.position.to(device))

            else:  # fixed
                T_joint = self.rest_transforms[i].unsqueeze(0).repeat(batch, 1, 1)

            # Accumulate: global = parent_global @ T_joint
            if joint.parent_link == -1:
                poses[:, joint.child_link] = T_joint
            else:
                poses[:, joint.child_link] = poses[:, joint.parent_link] @ T_joint

            positions[:, joint.child_link] = poses[:, joint.child_link, :3, 3]
            orientations[:, joint.child_link] = SE3Ops.rotation_matrix_to_quaternion(
                poses[:, joint.child_link, :3, :3]
            )

        return poses, positions, orientations

    def inverse_dynamics_rnea(self, joint_angles: torch.Tensor,
                               joint_velocities: torch.Tensor,
                               joint_accelerations: torch.Tensor,
                               external_forces: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Recursive Newton-Euler Algorithm for inverse dynamics.
        Computes joint torques given desired accelerations.

        Args:
            joint_angles: [batch, n_joints]
            joint_velocities: [batch, n_joints]
            joint_accelerations: [batch, n_joints]
            external_forces: [batch, n_links, 6] — optional external wrenches

        Returns:
            torques: [batch, n_joints]
        """
        batch = joint_angles.shape[0]
        device = joint_angles.device

        # Forward pass: compute velocities and accelerations
        poses, _, _ = self.forward_kinematics(joint_angles)

        # Simplified RNEA (full implementation requires spatial algebra)
        # For now: proportional-damping model
        torques = (joint_accelerations * self.link_masses.unsqueeze(0)
                   + joint_velocities * self.joint_damping.unsqueeze(0)
                   + torch.sign(joint_velocities) * self.joint_friction.unsqueeze(0))

        return torques

    def forward_dynamics_aba(self, joint_angles: torch.Tensor,
                              joint_velocities: torch.Tensor,
                              joint_torques: torch.Tensor,
                              external_forces: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Articulated Body Algorithm for forward dynamics.
        Computes accelerations given torques.

        Placeholder: uses simplified mass matrix inverse.
        Full ABA requires spatial inertia propagation.
        """
        # Simplified: τ = M(q)q̈ + C(q, q̇)q̇ + G(q)
        # q̈ = M⁻¹(τ - C - G)
        M = torch.diag(self.link_masses).unsqueeze(0)  # [1, n_links, n_links]
        M_inv = torch.inverse(M + torch.eye(self.n_links, device=M.device).unsqueeze(0) * 1e-4)

        # Coriolis + gravity (simplified)
        C = joint_velocities * self.joint_damping.unsqueeze(0)
        G = torch.ones_like(joint_angles) * self.gravity[2] * 0.1

        accelerations = (M_inv @ (joint_torques - C - G).unsqueeze(-1)).squeeze(-1)
        return accelerations

    def compute_contact_forces(self, positions: torch.Tensor,
                                floor_height: float = 0.0,
                                stiffness: float = 1000.0,
                                damping: float = 50.0) -> torch.Tensor:
        """
        Penalty-based contact forces with ground plane.

        Args:
            positions: [batch, n_links, 3]

        Returns:
            forces: [batch, n_links, 3]
        """
        penetration = torch.clamp(floor_height - positions[:, :, 2], min=0.0)
        # Spring-damper model
        forces = torch.zeros_like(positions)
        forces[:, :, 2] = stiffness * penetration
        return forces

    def simulate_step(self, state: Tuple[torch.Tensor, torch.Tensor],
                      actions: torch.Tensor,
                      contact_floor: bool = True) -> Tuple[torch.Tensor, torch.Tensor, Dict]:
        """
        Integrate one timestep with semi-implicit Euler.

        Args:
            state: (joint_angles [batch, n_joints], joint_velocities [batch, n_joints])
            actions: [batch, n_joints] — joint torques

        Returns:
            new_angles, new_velocities, info dict
        """
        joint_angles, joint_velocities = state

        # Forward dynamics
        accelerations = self.forward_dynamics_aba(joint_angles, joint_velocities, actions)

        # Contact forces (optional)
        if contact_floor:
            _, positions, _ = self.forward_kinematics(joint_angles)
            contact_forces = self.compute_contact_forces(positions)
            # Simplified: add contact effect to accelerations
            accelerations += contact_forces.sum(dim=1)[:, :self.n_joints] * 0.01

        # Semi-implicit Euler integration
        new_velocities = joint_velocities + accelerations * self.dt
        new_angles = joint_angles + new_velocities * self.dt

        # Joint limits
        for i, joint in enumerate(self.joints):
            if joint.limits is not None:
                new_angles[:, i] = torch.clamp(new_angles[:, i],
                                                joint.limits[0],
                                                joint.limits[1])

        info = {
            "accelerations": accelerations,
            "contact_forces": contact_forces if contact_floor else None,
            "kinetic_energy": 0.5 * (self.link_masses.unsqueeze(0) * new_velocities**2).sum(),
        }

        return new_angles, new_velocities, info

    def encode_state(self, joint_angles: torch.Tensor,
                     joint_velocities: torch.Tensor) -> torch.Tensor:
        """Encode compound motion state for World Model integration."""
        poses, positions, orientations = self.forward_kinematics(joint_angles)

        # Flatten: quat(4) + pos(3) + vel(3) + ang_vel_estimate(3) per link
        batch = joint_angles.shape[0]
        lin_vel = joint_velocities.unsqueeze(-1) * torch.ones(batch, self.n_links, 3, device=joint_angles.device)
        ang_vel = joint_velocities.unsqueeze(-1) * torch.ones(batch, self.n_links, 3, device=joint_angles.device)

        state_vec = torch.cat([
            orientations,      # [batch, n_links, 4]
            positions,         # [batch, n_links, 3]
            lin_vel,           # [batch, n_links, 3]
            ang_vel,           # [batch, n_links, 3]
        ], dim=-1)  # [batch, n_links, 13]

        return self.state_encoder(state_vec.view(batch, -1))


# ═══════════════════════════════════════════════════════════════════
# Pre-configured Robot Models
# ═══════════════════════════════════════════════════════════════════

def create_pendulum(n_links: int = 2, link_length: float = 1.0) -> Tuple[List[JointConfig], List[LinkConfig]]:
    """Create an n-link pendulum (serial chain)."""
    joints = []
    links = []
    for i in range(n_links):
        joints.append(JointConfig(
            name=f"joint_{i}",
            joint_type="revolute",
            axis=[0., 0., 1.],
            parent_link=i-1,
            child_link=i,
            position=[0., 0., -link_length] if i > 0 else [0., 0., 0.],
            limits=(-np.pi, np.pi),
        ))
        links.append(LinkConfig(
            name=f"link_{i}",
            mass=1.0,
            com=torch.tensor([0., 0., -link_length/2]),
        ))
    return joints, links


def create_humanoid_arm() -> Tuple[List[JointConfig], List[LinkConfig]]:
    """Create a 7-DOF humanoid arm (simplified)."""
    joints = [
        JointConfig("shoulder_pitch", "revolute", [0, 1, 0], -1, 0, [0, 0, 0]),
        JointConfig("shoulder_roll", "revolute", [1, 0, 0], 0, 1, [0, 0, 0]),
        JointConfig("shoulder_yaw", "revolute", [0, 0, 1], 1, 2, [0, 0, 0]),
        JointConfig("elbow_pitch", "revolute", [0, 1, 0], 2, 3, [0, 0, -0.3]),
        JointConfig("wrist_roll", "revolute", [1, 0, 0], 3, 4, [0, 0, -0.3]),
        JointConfig("wrist_yaw", "revolute", [0, 0, 1], 4, 5, [0, 0, -0.3]),
        JointConfig("wrist_pitch", "revolute", [0, 1, 0], 5, 6, [0, 0, -0.1]),
    ]
    links = [LinkConfig(f"link_{i}", mass=0.5 + i*0.1) for i in range(7)]
    return joints, links


# ═══════════════════════════════════════════════════════════════════
# Integration with World Model
# ═══════════════════════════════════════════════════════════════════

class CompoundMotionPrior(nn.Module):
    """Neural prior that injects compound motion awareness into World Model."""

    def __init__(self, state_dim: int, engine: CompoundMotionEngine):
        super().__init__()
        self.engine = engine
        self.projection = nn.Sequential(
            nn.Linear(256, state_dim),
            nn.LayerNorm(state_dim),
            nn.GELU(),
        )
        self.periodicity_encoder = nn.Linear(engine.n_joints, state_dim)

    def forward(self, joint_angles: torch.Tensor, joint_velocities: torch.Tensor) -> torch.Tensor:
        """Generate physics prior from compound motion state."""
        encoded = self.engine.encode_state(joint_angles, joint_velocities)
        projected = self.projection(encoded)

        # Periodicity features (resonance with Lightclock Harmony 899)
        periodic = torch.sin(joint_angles)  # [batch, n_joints]
        periodic_feat = self.periodicity_encoder(periodic)

        return projected + 0.3 * periodic_feat


if __name__ == "__main__":
    # Demo: double pendulum
    joints, links = create_pendulum(n_links=2, link_length=1.0)
    engine = CompoundMotionEngine(joints, links)

    q = torch.zeros(1, 2)
    q[0, 0] = np.pi / 4  # 45 degrees
    dq = torch.zeros(1, 2)

    print("🔧 Substrate 924 — Compound Motion Dynamics Demo")
    print(f"   Links: {engine.n_links}, Joints: {engine.n_joints}")

    poses, positions, orientations = engine.forward_kinematics(q)
    print(f"   Link 0 position: {positions[0, 0].tolist()}")
    print(f"   Link 1 position: {positions[0, 1].tolist()}")

    # Simulate 100 steps
    state = (q, dq)
    for step in range(100):
        torques = torch.zeros(1, 2)
        state, info = engine.simulate_step(state, torques)[:2], engine.simulate_step(state, torques)[2]
        state = (state[0], state[1])
        if step % 20 == 0:
            print(f"   Step {step}: angles={state[0][0].tolist()}, KE={info['kinetic_energy'].item():.4f}")

    print("✅ Compound Motion simulation complete")

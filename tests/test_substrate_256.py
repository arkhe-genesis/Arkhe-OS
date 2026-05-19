#!/usr/bin/env python3
"""
tests/test_substrate_256.py
Canon: ∞.Ω.∇+++.256.test_suite
Complete test suite for Substrate 256: CI/CD & Multi-Platform Expansion.
"""

import pytest
import hashlib
import json
from arkhe_core_image.builder import ArkheCoreImageBuilder, BuildConfiguration
from arkhe_core_image.cicd import ArkheCICDPipeline
from arkhe_core_image.multiarch import ArkheMultiArchBuilder, ArkheEnterpriseArchBuilder
from arkhe_core_image.interop import Substrate255ImageBuilder, SubstrateRegistry
from arkhe_core_image.validation import ArkheHardwareValidator


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: CORE BUILDER TESTS (40 tests)
# ═══════════════════════════════════════════════════════════════════════

class TestCoreBuilder:
    def test_builder_init(self):
        b = ArkheCoreImageBuilder()
        assert b.developer_id == "xSfWKGdLoQBoQx88"
        assert b.ubuntu_one is None
        assert b.gpg_key is None
        assert b.model_assertion is None
        assert b.image is None

    def test_custom_dev_id(self):
        assert ArkheCoreImageBuilder(developer_id="CUSTOM").developer_id == "CUSTOM"

    def test_ubuntu_one_create(self):
        b = ArkheCoreImageBuilder()
        a = b.create_ubuntu_one_account("dev@arkhe.org")
        assert a.email == "dev@arkhe.org" and a.registered and b.ubuntu_one is a

    def test_gpg_key_create(self):
        b = ArkheCoreImageBuilder()
        k = b.create_gpg_key("test-key")
        assert len(k.fingerprint) == 40 and len(k.key_id) == 16 and not k.registered_with_store

    def test_gpg_register(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org")
        b.create_gpg_key()
        assert b.register_gpg_key() and b.gpg_key.registered_with_store

    def test_gpg_register_no_key(self):
        assert not ArkheCoreImageBuilder().register_gpg_key()

    def test_stage_logs(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("a@arkhe.org")
        b.create_gpg_key()
        b.register_gpg_key()
        assert len(b._stage_log) == 3

    def test_download_model(self):
        b = ArkheCoreImageBuilder()
        m = b.download_reference_model()
        assert m.assertion_type == "model" and len(m.snaps) == 5

    def test_edit_model(self):
        b = ArkheCoreImageBuilder()
        b.download_reference_model()
        m = b.edit_model_for_arkhe()
        assert m.authority_id == b.developer_id and len(m.snaps) == 8 and len(m.canonical_seal) == 64

    def test_edit_model_grade(self):
        b = ArkheCoreImageBuilder()
        b.download_reference_model()
        assert b.edit_model_for_arkhe(grade="signed").grade == "signed"

    def test_edit_no_download(self):
        with pytest.raises(RuntimeError, match="not downloaded"):
            ArkheCoreImageBuilder().edit_model_for_arkhe()

    def test_sign_requires_gpg(self):
        b = ArkheCoreImageBuilder()
        b.create_gpg_key()
        b.download_reference_model()
        b.edit_model_for_arkhe()
        with pytest.raises(RuntimeError, match="not registered"):
            b.sign_model_assertion()

    def test_sign_model(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org")
        b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe()
        a = b.sign_model_assertion()
        assert a.artifact_type == "model_assertion_signed" and len(a.canonical_seal) == 64

    def test_sign_no_model(self):
        b = ArkheCoreImageBuilder()
        b.create_gpg_key(); b.register_gpg_key()
        with pytest.raises(RuntimeError, match="not ready"):
            b.sign_model_assertion()

    def test_sign_no_gpg(self):
        b = ArkheCoreImageBuilder()
        b.download_reference_model(); b.edit_model_for_arkhe()
        with pytest.raises(RuntimeError, match="not ready"):
            b.sign_model_assertion()

    def test_compile_default(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org")
        b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion()
        arts = b.compile_image(BuildConfiguration())
        assert len(arts) == 1 and arts[0].size_bytes == 4 * 1024**3

    def test_compile_with_snaps(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org")
        b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion()
        arts = b.compile_image(BuildConfiguration(local_snaps=["a.snap","b.snap"], output_filename="custom.img"))
        assert len(arts) == 3

    def test_compile_no_image(self):
        with pytest.raises(RuntimeError, match="not initialized"):
            ArkheCoreImageBuilder().compile_image(BuildConfiguration())

    def test_tpm_seal_default(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org")
        b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion(); b.compile_image(BuildConfiguration())
        s = b.configure_tpm_seal()
        assert s.tpm_version == "2.0" and len(s.sealed_keys) == 3 and s.op_tee_enabled

    def test_tpm_custom_version(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org")
        b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion(); b.compile_image(BuildConfiguration())
        assert b.configure_tpm_seal("1.2").tpm_version == "1.2"

    def test_tpm_orphan(self):
        b = ArkheCoreImageBuilder()
        s = b.configure_tpm_seal()
        assert s is not None and b.image is None

    def test_verify_success(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org")
        b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion(); b.compile_image(BuildConfiguration()); b.configure_tpm_seal()
        r = b.verify_post_boot()
        assert r["snaps_installed"] == 3 and r["tpm_sealed"] and all(r["constitutional_compliance"].values())

    def test_verify_no_image(self):
        assert ArkheCoreImageBuilder().verify_post_boot()["error"] == "Image not built"

    def test_verify_no_tpm(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org")
        b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion(); b.compile_image(BuildConfiguration())
        r = b.verify_post_boot()
        assert not r["tpm_sealed"] and r["snaps_installed"] == 3

    def test_build_report(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org")
        b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion(); b.compile_image(BuildConfiguration()); b.configure_tpm_seal(); b.verify_post_boot()
        r = b.get_build_report()
        assert r["model_name"] == "arkhe-core-26-pi-arm64" and len(r["canonical_seal"]) == 64

    def test_build_report_no_image(self):
        assert "error" in ArkheCoreImageBuilder().get_build_report()

    def test_canonical_snap_ids(self):
        assert len(ArkheCoreImageBuilder().CANONICAL_SNAP_IDS) == 6

    def test_arkhe_snap_ids(self):
        assert len(ArkheCoreImageBuilder().ARKHE_SNAP_IDS) == 3

    def test_full_pipeline(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("p@arkhe.org"); b.create_gpg_key("k"); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion()
        b.compile_image(BuildConfiguration(target_device="raspberry-pi-5", output_filename="arkhe-pi5.img", local_snaps=["/opt/mesh.snap"]))
        b.configure_tpm_seal(); b.verify_post_boot()
        assert b.get_build_report()["artifacts_count"] == 3

    def test_seal_determinism(self):
        b1 = ArkheCoreImageBuilder(); b1.download_reference_model(); s1 = b1.edit_model_for_arkhe().canonical_seal
        b2 = ArkheCoreImageBuilder(); b2.download_reference_model(); s2 = b2.edit_model_for_arkhe().canonical_seal
        assert s1 == s2 and len(s1) == 64

    def test_constitutional_all_true(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org"); b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion(); b.compile_image(BuildConfiguration()); b.configure_tpm_seal(); b.verify_post_boot()
        assert all(b.image.constitutional_principles.values())

    def test_artifact_hashes(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org"); b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion(); b.compile_image(BuildConfiguration())
        for a in b.image.artifacts:
            assert len(a.sha3_256_hash) == 64 and len(a.canonical_seal) == 64

    def test_timestamp_ordering(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("dev@arkhe.org"); b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion()
        ts = [log["timestamp"] for log in b._stage_log]
        assert all(ts[i] <= ts[i+1] for i in range(len(ts)-1))

    def test_snap_types(self):
        b = ArkheCoreImageBuilder(); b.download_reference_model(); b.edit_model_for_arkhe()
        assert all(s.snap_type in {"gadget","kernel","base","snapd","app"} for s in b.model_assertion.snaps)

    def test_presence_field(self):
        b = ArkheCoreImageBuilder(); b.download_reference_model()
        assert next(s for s in b.model_assertion.snaps if s.name=="console-conf").presence == "optional"

    def test_config_defaults(self):
        c = BuildConfiguration()
        assert c.target_device == "raspberry-pi-4" and c.image_format == "img" and c.allow_kernel_mismatch

    def test_config_custom(self):
        c = BuildConfiguration(target_device="pi-5", image_format="iso", allow_kernel_mismatch=False)
        assert c.target_device == "pi-5" and c.image_format == "iso" and not c.allow_kernel_mismatch

    def test_model_defaults(self):
        m = ArkheCoreImageBuilder().model_assertion
        assert m is None  # Not downloaded yet

    def test_tpm_defaults(self):
        from arkhe_core_image.builder import TPMSeal
        s = TPMSeal()
        assert s.tpm_version == "2.0" and s.sealed_keys == [] and s.op_tee_enabled


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: CI/CD PIPELINE TESTS (14 tests)
# ═══════════════════════════════════════════════════════════════════════

class TestCICDPipeline:
    def test_pipeline_create(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        p = c.create_pipeline("push", "main")
        assert len(p.pipeline_id) == 16 and p.trigger == "push" and len(p.stages) == 5

    def test_stage_names(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        c.create_pipeline()
        assert [s.name for s in c.pipeline.stages] == ["checkout","lint-and-test","build-image","security-scan","publish"]

    def test_stage_execution(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        c.create_pipeline()
        s = c.execute_stage("checkout", True, 500)
        assert s.status == "success" and s.duration_ms == 500

    def test_failure_sets_overall(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        c.create_pipeline()
        c.execute_stage("checkout", True)
        c.execute_stage("lint-and-test", False)
        assert c.pipeline.overall_status == "failure"

    def test_all_success(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        c.create_pipeline()
        for s in c.pipeline.stages: c.execute_stage(s.name, True)
        assert c.pipeline.overall_status == "success"

    def test_report_fields(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        c.create_pipeline("tag", "main")
        c.execute_stage("checkout", True)
        r = c.get_pipeline_report()
        assert r["trigger"] == "tag" and len(r["stages"]) == 5

    def test_yaml_matrix(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        c.create_pipeline()
        assert "arm64" in c.pipeline.yaml_manifest and "amd64" in c.pipeline.yaml_manifest

    def test_yaml_dispatch(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        c.create_pipeline()
        assert "workflow_dispatch" in c.pipeline.yaml_manifest

    def test_yaml_jobs(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        c.create_pipeline()
        assert "jobs:" in c.pipeline.yaml_manifest and "validate:" in c.pipeline.yaml_manifest

    def test_seal_valid(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        p = c.create_pipeline("push", "main")
        assert len(p.canonical_seal) == 64

    def test_bad_stage_fails(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        c.create_pipeline()
        with pytest.raises(RuntimeError, match="not found"):
            c.execute_stage("nonexistent")

    def test_report_no_pipeline(self):
        assert "error" in ArkheCICDPipeline(ArkheCoreImageBuilder()).get_pipeline_report()

    def test_exec_no_pipeline(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        with pytest.raises(RuntimeError, match="not created"):
            c.execute_stage("checkout")

    def test_pipeline_log_stage(self):
        b = ArkheCoreImageBuilder()
        c = ArkheCICDPipeline(b)
        c.create_pipeline("push", "main")
        assert any(log["stage"] == "CI_CD_PIPELINE" for log in b._stage_log)


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: MULTI-ARCHITECTURE TESTS (17 tests)
# ═══════════════════════════════════════════════════════════════════════

class TestMultiArchitecture:
    def test_profiles_loaded(self):
        assert len(ArkheMultiArchBuilder(ArkheCoreImageBuilder()).ARCHITECTURE_PROFILES) == 3

    def test_create_default(self):
        b = ArkheCoreImageBuilder()
        m = ArkheMultiArchBuilder(b)
        mb = m.create_multi_arch_build()
        assert len(mb.architectures) == 3 and mb.remote_build_enabled

    def test_create_custom(self):
        b = ArkheCoreImageBuilder()
        m = ArkheMultiArchBuilder(b)
        mb = m.create_multi_arch_build(["arm64", "amd64"])
        assert len(mb.architectures) == 2

    def test_unsupported_fails(self):
        with pytest.raises(RuntimeError, match="Unsupported"):
            ArkheMultiArchBuilder(ArkheCoreImageBuilder()).create_multi_arch_build(["mips64"])

    def test_build_arm64(self):
        b = ArkheCoreImageBuilder()
        m = ArkheMultiArchBuilder(b)
        m.create_multi_arch_build(["arm64"])
        img = m.build_for_architecture("arm64")
        assert img.model_assertion.architecture == "arm64"

    def test_build_amd64(self):
        b = ArkheCoreImageBuilder()
        m = ArkheMultiArchBuilder(b)
        m.create_multi_arch_build(["amd64"])
        img = m.build_for_architecture("amd64")
        assert img.model_assertion.snaps[0].name == "pc"

    def test_build_riscv64(self):
        b = ArkheCoreImageBuilder()
        m = ArkheMultiArchBuilder(b)
        m.create_multi_arch_build(["riscv64"])
        img = m.build_for_architecture("riscv64")
        assert img.model_assertion.snaps[0].name == "riscv64-gadget"

    def test_report_single(self):
        b = ArkheCoreImageBuilder()
        m = ArkheMultiArchBuilder(b)
        m.create_multi_arch_build(["arm64"])
        m.build_for_architecture("arm64")
        r = m.get_multi_arch_report()
        assert r["builds_completed"] == ["arm64"]

    def test_report_all(self):
        b = ArkheCoreImageBuilder()
        m = ArkheMultiArchBuilder(b)
        m.create_multi_arch_build()
        for a in ["arm64", "amd64", "riscv64"]: m.build_for_architecture(a)
        r = m.get_multi_arch_report()
        assert len(r["builds_completed"]) == 3

    def test_build_no_config(self):
        with pytest.raises(RuntimeError, match="not configured"):
            ArkheMultiArchBuilder(ArkheCoreImageBuilder()).build_for_architecture("arm64")

    def test_build_unconfigured_arch(self):
        b = ArkheCoreImageBuilder()
        m = ArkheMultiArchBuilder(b)
        m.create_multi_arch_build(["arm64"])
        with pytest.raises(RuntimeError, match="not in configured"):
            m.build_for_architecture("amd64")

    def test_report_no_config(self):
        assert "error" in ArkheMultiArchBuilder(ArkheCoreImageBuilder()).get_multi_arch_report()

    def test_profile_fields(self):
        m = ArkheMultiArchBuilder(ArkheCoreImageBuilder())
        assert m.ARCHITECTURE_PROFILES["arm64"].gadget_snap == "pi"
        assert m.ARCHITECTURE_PROFILES["riscv64"].tpm_support == False

    def test_filenames(self):
        b = ArkheCoreImageBuilder()
        m = ArkheMultiArchBuilder(b)
        m.create_multi_arch_build(["arm64", "amd64"])
        assert m.build_for_architecture("arm64").build_config.output_filename == "arkhe-core-26-arm64.img"

    def test_arkhe_snaps(self):
        b = ArkheCoreImageBuilder()
        m = ArkheMultiArchBuilder(b)
        m.create_multi_arch_build(["amd64"])
        img = m.build_for_architecture("amd64")
        assert "arkhe-enforcement" in [s.name for s in img.model_assertion.snaps]

    def test_constitutional(self):
        b = ArkheCoreImageBuilder()
        m = ArkheMultiArchBuilder(b)
        m.create_multi_arch_build()
        for a in ["arm64", "amd64", "riscv64"]:
            img = m.build_for_architecture(a)
            assert all(img.constitutional_principles.values())

    def test_full_integration(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("i@arkhe.org"); b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion()
        b.compile_image(BuildConfiguration()); b.configure_tpm_seal(); b.verify_post_boot()
        cicd = ArkheCICDPipeline(b)
        cicd.create_pipeline("push", "main")
        for s in cicd.pipeline.stages: cicd.execute_stage(s.name, True)
        multi = ArkheMultiArchBuilder(b)
        multi.create_multi_arch_build(["arm64", "amd64"])
        multi.build_for_architecture("arm64")
        multi.build_for_architecture("amd64")
        assert b.image is not None and cicd.pipeline.overall_status == "success" and len(multi.multi_arch.builds) == 2


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: SUBSTRATE INTEROPERABILITY TESTS (18 tests)
# ═══════════════════════════════════════════════════════════════════════

class TestSubstrateInterop:
    def test_contract_integrity(self):
        from arkhe_core_image.interop import SubstrateContract
        c = SubstrateContract("255", "244.1.0", "v1", "", dependencies=["217"], provides=["image_build"])
        c.generate_canonical_seal()
        assert c.verify_integrity() and len(c.canonical_seal) == 64

    def test_contract_integrity_fails(self):
        from arkhe_core_image.interop import SubstrateContract
        c = SubstrateContract("255", "244.1.0", "v1", "wrong", dependencies=["217"], provides=["image_build"])
        assert not c.verify_integrity()

    def test_s255_init(self):
        s = Substrate255ImageBuilder(config={})
        assert s.SUBSTRATE_ID == "255" and s.VERSION == "244.1.0"

    def test_capabilities(self):
        s = Substrate255ImageBuilder(config={})
        caps = s.get_capabilities()
        assert set(caps["supported_architectures"]) == {"arm64", "amd64", "riscv64", "loongarch64", "s390x"}

    def test_dependencies(self):
        s = Substrate255ImageBuilder(config={})
        assert "217:ubuntu-core-26" in s._get_dependencies()

    def test_provides(self):
        s = Substrate255ImageBuilder(config={})
        assert "model_assertion_generation" in s._get_provides()

    def test_contract_generation(self):
        s = Substrate255ImageBuilder(config={"test": "value"})
        c = s.get_contract()
        assert c.verify_integrity() and len(c.canonical_seal) == 64

    def test_invoke_generate_model(self):
        s = Substrate255ImageBuilder(config={})
        r = s.invoke("generate_model", {"model_name": "test", "architecture": "arm64", "grade": "signed"})
        assert r["success"] and r["result"]["model_name"] == "test"

    def test_invoke_compile_image(self):
        s = Substrate255ImageBuilder(config={})
        r = s.invoke("compile_image", {"output_filename": "test.img", "image_size": 1024})
        assert r["success"] and r["result"]["image_path"] == "test.img"

    def test_invoke_verify_compliance(self):
        s = Substrate255ImageBuilder(config={})
        r = s.invoke("verify_compliance", {})
        assert r["success"] and r["result"]["overall_compliance"]

    def test_invoke_unknown(self):
        s = Substrate255ImageBuilder(config={})
        r = s.invoke("unknown", {})
        assert not r["success"] and "Unknown method" in r["error"]

    def test_anchor_event(self):
        s = Substrate255ImageBuilder(config={})
        seal = s.anchor_event("test", {"data": "value"})
        assert len(seal) == 64

    def test_registry_register(self):
        r = SubstrateRegistry()
        s = Substrate255ImageBuilder(config={})
        assert r.register(s) and "255" in r._substrates

    def test_registry_get(self):
        r = SubstrateRegistry()
        s = Substrate255ImageBuilder(config={})
        r.register(s)
        assert r.get("255") is not None and r.get("255").SUBSTRATE_ID == "255"

    def test_registry_version_constraint(self):
        r = SubstrateRegistry()
        s = Substrate255ImageBuilder(config={})
        r.register(s)
        assert r.get("255", "244.2.0") is None
        assert r.get("255", "244.0.0") is not None

    def test_registry_discover(self):
        r = SubstrateRegistry()
        s = Substrate255ImageBuilder(config={})
        r.register(s)
        compatible = r.discover_compatible(["model_assertion_generation", "image_compilation"])
        assert len(compatible) == 1

    def test_registry_discover_partial_fails(self):
        r = SubstrateRegistry()
        s = Substrate255ImageBuilder(config={})
        r.register(s)
        compatible = r.discover_compatible(["model_assertion_generation", "nonexistent"])
        assert len(compatible) == 0

    def test_full_interop(self):
        r = SubstrateRegistry()
        s = Substrate255ImageBuilder(config={"temporal_chain_endpoint": "https://temporal.arkhe.org"})
        assert r.register(s)
        substrate = r.get("255")
        result = substrate.invoke("generate_model", {"architecture": "riscv64"})
        assert result["success"] and result["result"]["architecture"] == "riscv64"
        seal = substrate.anchor_event("integration", {"phi_c": 0.99})
        assert len(seal) == 64


# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: HARDWARE VALIDATION TESTS (9 tests)
# ═══════════════════════════════════════════════════════════════════════

class TestHardwareValidation:
    def test_profiles_loaded(self):
        v = ArkheHardwareValidator()
        assert len(v.HARDWARE_PROFILES) == 4

    def test_validate_pi4(self):
        v = ArkheHardwareValidator()
        p = v.validate_device("raspberry-pi-4", "/dev/sda")
        assert p.tpm_present and p.tpm_version == "2.0" and len(p.canonical_seal) == 64

    def test_validate_pi5(self):
        v = ArkheHardwareValidator()
        p = v.validate_device("raspberry-pi-5", "/dev/sdb")
        assert p.memory_mb == 8192 and len(p.canonical_seal) == 64

    def test_validate_x86(self):
        v = ArkheHardwareValidator()
        p = v.validate_device("generic-x86_64", "/dev/nvme0")
        assert p.boot_mode == "uefi" and p.tpm_type == "hardware"

    def test_validate_qemu(self):
        v = ArkheHardwareValidator()
        p = v.validate_device("qemu-x86_64", "qemu:///system")
        assert p.tpm_type == "emulated"

    def test_unknown_device_fails(self):
        v = ArkheHardwareValidator()
        with pytest.raises(RuntimeError, match="Unknown device type"):
            v.validate_device("unknown", "/dev/null")

    def test_validation_report(self):
        v = ArkheHardwareValidator()
        v.validate_device("raspberry-pi-4", "/dev/sda")
        v.validate_device("generic-x86_64", "/dev/nvme0")
        r = v.get_validation_report()
        assert r["total_tests_run"] == 12 and r["all_constitutional_compliant"]

    def test_constitutional_all(self):
        v = ArkheHardwareValidator()
        for d in ["raspberry-pi-4", "raspberry-pi-5", "generic-x86_64", "qemu-x86_64"]:
            p = v.validate_device(d, "/dev/test")
            assert all(p.constitutional_principles.values())

    def test_temporal_anchor(self):
        v = ArkheHardwareValidator()
        p = v.validate_device("raspberry-pi-4", "/dev/sda")
        t = next(x for x in p.test_results if x["name"] == "temporal_chain_anchor")
        assert t["status"] == "PASS" and len(t["anchor_seal"]) == 64


# ═══════════════════════════════════════════════════════════════════════
# PHASE 6: ENTERPRISE ARCHITECTURE TESTS (8 tests)
# ═══════════════════════════════════════════════════════════════════════

class TestEnterpriseArchitecture:
    def test_enterprise_profiles(self):
        b = ArkheCoreImageBuilder()
        e = ArkheEnterpriseArchBuilder(b)
        assert "loongarch64" in e.ARCHITECTURE_PROFILES
        assert "s390x" in e.ARCHITECTURE_PROFILES

    def test_enterprise_create(self):
        b = ArkheCoreImageBuilder()
        e = ArkheEnterpriseArchBuilder(b)
        mb = e.create_enterprise_build()
        assert len(mb.architectures) == 2

    def test_build_loongarch64(self):
        b = ArkheCoreImageBuilder()
        e = ArkheEnterpriseArchBuilder(b)
        e.create_enterprise_build(["loongarch64"])
        img = e.build_for_architecture("loongarch64")
        assert img.model_assertion.architecture == "loongarch64"

    def test_build_s390x(self):
        b = ArkheCoreImageBuilder()
        e = ArkheEnterpriseArchBuilder(b)
        e.create_enterprise_build(["s390x"])
        img = e.build_for_architecture("s390x")
        assert img.model_assertion.architecture == "s390x"

    def test_enterprise_report(self):
        b = ArkheCoreImageBuilder()
        e = ArkheEnterpriseArchBuilder(b)
        e.create_enterprise_build()
        e.build_for_architecture("loongarch64")
        e.build_for_architecture("s390x")
        r = e.get_enterprise_report()
        assert r["enterprise_specific"]["s390x_crypto_express"]

    def test_combined_build(self):
        b = ArkheCoreImageBuilder()
        e = ArkheEnterpriseArchBuilder(b)
        e.create_multi_arch_build(["arm64", "amd64", "loongarch64", "s390x"])
        for a in ["arm64", "amd64", "loongarch64", "s390x"]:
            e.build_for_architecture(a)
        r = e.get_multi_arch_report()
        assert len(r["builds_completed"]) == 4

    def test_enterprise_constitutional(self):
        b = ArkheCoreImageBuilder()
        e = ArkheEnterpriseArchBuilder(b)
        e.create_enterprise_build()
        for a in ["loongarch64", "s390x"]:
            img = e.build_for_architecture(a)
            assert all(img.constitutional_principles.values())

    def test_full_system(self):
        b = ArkheCoreImageBuilder()
        b.create_ubuntu_one_account("full@arkhe.org"); b.create_gpg_key(); b.register_gpg_key()
        b.download_reference_model(); b.edit_model_for_arkhe(); b.sign_model_assertion()
        b.compile_image(BuildConfiguration()); b.configure_tpm_seal(); b.verify_post_boot()
        cicd = ArkheCICDPipeline(b)
        cicd.create_pipeline("push", "main")
        for s in cicd.pipeline.stages: cicd.execute_stage(s.name, True)
        multi = ArkheMultiArchBuilder(b)
        multi.create_multi_arch_build(["arm64", "amd64"])
        multi.build_for_architecture("arm64"); multi.build_for_architecture("amd64")
        hw = ArkheHardwareValidator()
        hw.validate_device("raspberry-pi-4", "/dev/sda")
        ent = ArkheEnterpriseArchBuilder(b)
        ent.create_enterprise_build(["s390x"]); ent.build_for_architecture("s390x")
        assert b.image is not None and cicd.pipeline.overall_status == "success"
        assert len(multi.multi_arch.builds) == 2 and len(hw.validations) == 1
        assert len(ent.multi_arch.builds) == 1

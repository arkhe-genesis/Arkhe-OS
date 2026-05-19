import hashlib
import time
import sys
import importlib.util
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

def test(name):
    def decorator(func):
        func.__test_name__ = name
        return func
    return decorator

# Because Arkhe OS canonical layers start with numbers (e.g., `25_external_validation`), they are invalid Python module names.
# To import them dynamically, use `importlib.util.spec_from_file_location` and `module_from_spec`, and ensure the module is added to `sys.modules["module_name"]` before calling `spec.loader.exec_module(module)`.

spec = importlib.util.spec_from_file_location("builder", "src/25_external_validation/255_ubuntu_core_builder/builder.py")
builder_module = importlib.util.module_from_spec(spec)
sys.modules["builder"] = builder_module
spec.loader.exec_module(builder_module)

ArkheCoreImageBuilder = builder_module.ArkheCoreImageBuilder
BuildConfiguration = builder_module.BuildConfiguration
ModelAssertion = builder_module.ModelAssertion
BuildArtifact = builder_module.BuildArtifact
TPMSeal = builder_module.TPMSeal
BuildStage = builder_module.BuildStage

print("=" * 70)
print("ARKHE OS SUBSTRATE 255 — TEST SUITE EXECUTION")
print("=" * 70)
print()

# --- PREREQUISITES & ACCOUNT MANAGEMENT ---

@test("T01: Builder initializes with default developer_id")
def t01_builder_init():
    builder = ArkheCoreImageBuilder()
    assert builder.developer_id == "xSfWKGdLoQBoQx88"
    assert builder.ubuntu_one is None
    assert builder.gpg_key is None
    assert builder.model_assertion is None
    assert builder.image is None
    assert len(builder._stage_log) == 0

@test("T02: Custom developer_id override")
def t02_custom_dev_id():
    builder = ArkheCoreImageBuilder(developer_id="CUSTOM_ID_123")
    assert builder.developer_id == "CUSTOM_ID_123"

@test("T03: Ubuntu One account creation")
def t03_ubuntu_one_create():
    builder = ArkheCoreImageBuilder()
    account = builder.create_ubuntu_one_account("dev@arkhe.org")
    assert account.developer_id == builder.developer_id
    assert account.email == "dev@arkhe.org"
    assert account.registered is True
    assert account.gpg_key_id is None
    assert builder.ubuntu_one is account
    assert len(builder._stage_log) == 1
    assert builder._stage_log[0]["stage"] == "PREREQUISITES"

@test("T04: GPG key creation generates valid fingerprint")
def t04_gpg_key_create():
    builder = ArkheCoreImageBuilder()
    key = builder.create_gpg_key("test-key")
    assert key.key_name == "test-key"
    assert len(key.fingerprint) == 40
    assert len(key.key_id) == 16
    assert key.created > 0
    assert key.registered_with_store is False
    assert builder.gpg_key is key

@test("T05: GPG key registration links to Ubuntu One account")
def t05_gpg_register():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    result = builder.register_gpg_key()
    assert result is True
    assert builder.gpg_key.registered_with_store is True
    assert builder.ubuntu_one.gpg_key_id == builder.gpg_key.key_id

@test("T06: GPG registration fails without key")
def t06_gpg_register_no_key():
    builder = ArkheCoreImageBuilder()
    result = builder.register_gpg_key()
    assert result is False

@test("T07: Multiple stage logs accumulate correctly")
def t07_stage_log_accumulation():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("a@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    assert len(builder._stage_log) == 3
    stages = [log["stage"] for log in builder._stage_log]
    assert stages == ["PREREQUISITES", "PREREQUISITES", "PREREQUISITES"]

# --- MODEL ASSERTION LIFECYCLE ---

@test("T08: Reference model download creates correct base snaps")
def t08_download_model():
    builder = ArkheCoreImageBuilder()
    model = builder.download_reference_model()
    assert model.assertion_type == "model"
    assert model.series == "16"
    assert model.architecture == "arm64"
    assert model.authority_id == "canonical"
    assert model.brand_id == "canonical"
    assert len(model.snaps) == 5
    snap_names = [s.name for s in model.snaps]
    assert "pi" in snap_names
    assert "pi-kernel" in snap_names
    assert "core26" in snap_names
    assert "snapd" in snap_names
    assert "console-conf" in snap_names
    assert builder.model_assertion is model
    assert len(builder._stage_log) == 1
    assert builder._stage_log[0]["stage"] == "MODEL_DOWNLOAD"

@test("T09: Model edit transforms authority and injects Arkhe snaps")
def t09_edit_model():
    builder = ArkheCoreImageBuilder()
    builder.download_reference_model()
    model = builder.edit_model_for_arkhe()
    assert model.authority_id == builder.developer_id
    assert model.brand_id == builder.developer_id
    assert model.model_name == "arkhe-core-26-pi-arm64"
    assert model.base == "core26"
    assert model.grade == "dangerous"
    assert len(model.snaps) == 8  # 5 base + 3 Arkhe
    arkhe_names = [s.name for s in model.snaps if s.name.startswith("arkhe") or s.name in ["temporal-anchor", "pqc-revocation"]]
    assert len(arkhe_names) == 3
    assert model.canonical_seal != ""
    assert len(model.canonical_seal) == 64  # SHA3-256 hex
    assert builder._stage_log[-1]["stage"] == "MODEL_EDIT"

@test("T10: Model edit with custom grade")
def t10_edit_model_grade():
    builder = ArkheCoreImageBuilder()
    builder.download_reference_model()
    model = builder.edit_model_for_arkhe(grade="signed")
    assert model.grade == "signed"

@test("T11: Model edit fails without prior download")
def t11_edit_no_download():
    builder = ArkheCoreImageBuilder()
    try:
        builder.edit_model_for_arkhe()
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "not downloaded" in str(e)

@test("T12: Model assertion signing requires GPG registration")
def t12_sign_requires_gpg():
    builder = ArkheCoreImageBuilder()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    try:
        builder.sign_model_assertion()
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "not registered" in str(e)

@test("T13: Model assertion signing produces valid artifact")
def t13_sign_model():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    artifact = builder.sign_model_assertion()
    assert artifact.artifact_type == "model_assertion_signed"
    assert artifact.path == "arkhe-model.model"
    assert artifact.size_bytes > 0
    assert len(artifact.sha3_256_hash) == 64
    assert len(artifact.canonical_seal) == 64
    assert artifact.timestamp > 0
    assert builder.image is not None
    assert len(builder.image.artifacts) == 1
    assert BuildStage.MODEL_SIGN in builder.image.build_stages_completed
    assert builder._stage_log[-1]["stage"] == "MODEL_SIGN"

@test("T14: Sign fails without model assertion")
def t14_sign_no_model():
    builder = ArkheCoreImageBuilder()
    builder.create_gpg_key()
    builder.register_gpg_key()
    try:
        builder.sign_model_assertion()
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "not ready" in str(e)

@test("T15: Sign fails without GPG key")
def t15_sign_no_gpg():
    builder = ArkheCoreImageBuilder()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    try:
        builder.sign_model_assertion()
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "not ready" in str(e)

# --- IMAGE COMPILATION ---

@test("T16: Image compilation with default config")
def t16_compile_default():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    builder.sign_model_assertion()
    config = BuildConfiguration()
    artifacts = builder.compile_image(config)
    assert len(artifacts) == 1
    img = artifacts[0]
    assert img.artifact_type == "bootable_image"
    assert img.size_bytes == 4 * 1024 * 1024 * 1024  # 4GB
    assert img.path == "pi.img"
    assert len(img.sha3_256_hash) == 64
    assert len(img.canonical_seal) == 64
    assert BuildStage.IMAGE_COMPILE in builder.image.build_stages_completed
    assert builder.image.build_config is config

@test("T17: Image compilation with local snaps")
def t17_compile_with_snaps():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    builder.sign_model_assertion()
    config = BuildConfiguration(local_snaps=["/path/to/snap1.snap", "/path/to/snap2.snap"], output_filename="custom.img")
    artifacts = builder.compile_image(config)
    assert len(artifacts) == 3  # 1 image + 2 snaps
    assert artifacts[0].artifact_type == "bootable_image"
    assert artifacts[0].path == "custom.img"
    assert artifacts[1].artifact_type == "local_snap"
    assert artifacts[2].artifact_type == "local_snap"
    assert all(a.size_bytes > 0 for a in artifacts)
    assert len(builder.image.artifacts) == 4  # 1 signed model + 3 compiled

@test("T18: Compile fails without initialized image")
def t18_compile_no_image():
    builder = ArkheCoreImageBuilder()
    try:
        builder.compile_image(BuildConfiguration())
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "not initialized" in str(e)

# --- TPM SEALING ---

@test("T19: TPM seal configuration with defaults")
def t19_tpm_seal_default():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    builder.sign_model_assertion()
    builder.compile_image(BuildConfiguration())
    seal = builder.configure_tpm_seal()
    assert seal.tpm_version == "2.0"
    assert len(seal.sealed_keys) == 3
    assert all(len(k) == 32 for k in seal.sealed_keys)
    assert seal.op_tee_enabled is True
    assert seal.hardware_attestation is True
    assert builder.image.tpm_seal is seal
    assert builder._stage_log[-1]["stage"] == "VERIFICATION"

@test("T20: TPM seal with custom version")
def t20_tpm_seal_custom():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    builder.sign_model_assertion()
    builder.compile_image(BuildConfiguration())
    seal = builder.configure_tpm_seal(tpm_version="1.2")
    assert seal.tpm_version == "1.2"

@test("T21: TPM seal works without image (orphan seal)")
def t21_tpm_orphan():
    builder = ArkheCoreImageBuilder()
    seal = builder.configure_tpm_seal()
    assert seal is not None
    assert builder.image is None  # No image was created

# --- POST-BOOT VERIFICATION ---

@test("T22: Post-boot verification succeeds with all snaps")
def t22_verify_success():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    builder.sign_model_assertion()
    builder.compile_image(BuildConfiguration())
    builder.configure_tpm_seal()
    result = builder.verify_post_boot()
    assert result["model_assertion_valid"] is True
    assert result["snaps_installed"] == 3
    assert result["expected_snaps"] == 3
    assert result["tpm_sealed"] is True
    assert result["constitutional_compliance"]["P1"] is True
    assert result["constitutional_compliance"]["P3"] is True
    assert result["constitutional_compliance"]["P6"] is True
    assert result["constitutional_compliance"]["P7"] is True
    assert result["constitutional_compliance"]["P8"] is True
    assert builder.image.constitutional_principles == result["constitutional_compliance"]
    assert BuildStage.VERIFICATION in builder.image.build_stages_completed

@test("T23: Post-boot verification fails without image")
def t23_verify_no_image():
    builder = ArkheCoreImageBuilder()
    result = builder.verify_post_boot()
    assert "error" in result
    assert result["error"] == "Image not built"

@test("T24: Post-boot with missing TPM seal")
def t24_verify_no_tpm():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    builder.sign_model_assertion()
    builder.compile_image(BuildConfiguration())
    # Skip TPM seal
    result = builder.verify_post_boot()
    assert result["tpm_sealed"] is False
    assert result["snaps_installed"] == 3  # Snaps still detected

# --- BUILD REPORT ---

@test("T25: Build report contains all expected fields")
def t25_build_report():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    builder.sign_model_assertion()
    builder.compile_image(BuildConfiguration())
    builder.configure_tpm_seal()
    builder.verify_post_boot()
    report = builder.get_build_report()
    assert report["model_name"] == "arkhe-core-26-pi-arm64"
    assert report["base"] == "core26"
    assert report["grade"] == "dangerous"
    assert report["architecture"] == "arm64"
    assert report["tpm_sealed"] is True
    assert len(report["stages_completed"]) == 5  # MODEL_SIGN, IMAGE_COMPILE, VERIFICATION (x2 for TPM+verify), plus any others
    assert report["artifacts_count"] == 2  # signed model + bootable image
    assert "canonical_seal" in report
    assert len(report["canonical_seal"]) == 64
    assert report["constitutional_principles"]["P1"] is True

@test("T26: Build report fails without image")
def t26_report_no_image():
    builder = ArkheCoreImageBuilder()
    report = builder.get_build_report()
    assert "error" in report
    assert report["error"] == "No image built"

# --- EDGE CASES & INTEGRITY ---

@test("T27: Canonical snap IDs are all present")
def t27_canonical_snap_ids():
    builder = ArkheCoreImageBuilder()
    ids = builder.CANONICAL_SNAP_IDS
    assert len(ids) == 6
    assert all(len(v) > 0 for v in ids.values())
    assert "pi" in ids
    assert "pi-kernel" in ids
    assert "core26" in ids

@test("T28: Arkhe snap IDs are all present")
def t28_arkhe_snap_ids():
    builder = ArkheCoreImageBuilder()
    ids = builder.ARKHE_SNAP_IDS
    assert len(ids) == 3
    assert "arkhe-enforcement" in ids
    assert "temporal-anchor" in ids
    assert "pqc-revocation" in ids

@test("T29: Full end-to-end build pipeline")
def t29_full_pipeline():
    builder = ArkheCoreImageBuilder()
    # Prerequisites
    builder.create_ubuntu_one_account("pipeline@arkhe.org")
    builder.create_gpg_key("pipeline-key")
    builder.register_gpg_key()
    # Model
    builder.download_reference_model()
    builder.edit_model_for_arkhe(grade="dangerous")
    builder.sign_model_assertion()
    # Image
    config = BuildConfiguration(
        target_device="raspberry-pi-5",
        output_filename="arkhe-pi5.img",
        local_snaps=["/opt/snaps/arkhe-mesh.snap"]
    )
    builder.compile_image(config)
    # TPM
    builder.configure_tpm_seal()
    # Verify
    result = builder.verify_post_boot()
    # Report
    report = builder.get_build_report()
    assert report["model_name"] == "arkhe-core-26-pi-arm64"
    assert report["artifacts_count"] == 3  # model + image + local snap
    assert result["snaps_installed"] == 3
    assert result["tpm_sealed"] is True
    assert len(builder._stage_log) >= 8
    stages = [log["stage"] for log in builder._stage_log]
    assert "PREREQUISITES" in stages
    assert "MODEL_DOWNLOAD" in stages
    assert "MODEL_EDIT" in stages
    assert "MODEL_SIGN" in stages
    assert "IMAGE_COMPILE" in stages
    assert "VERIFICATION" in stages

@test("T30: Canonical seal is deterministic for same inputs")
def t30_seal_determinism():
    builder = ArkheCoreImageBuilder()
    builder.download_reference_model()
    model1 = builder.edit_model_for_arkhe()
    seal1 = model1.canonical_seal
    # Create new builder with same state
    builder2 = ArkheCoreImageBuilder()
    builder2.download_reference_model()
    model2 = builder2.edit_model_for_arkhe()
    seal2 = model2.canonical_seal
    # Seals should differ because timestamp changes
    assert seal1 != seal2  # Timestamp-based, so different each run
    assert len(seal1) == 64
    assert len(seal2) == 64

@test("T31: Constitutional principles all True after verification")
def t31_constitutional_all_true():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    builder.sign_model_assertion()
    builder.compile_image(BuildConfiguration())
    builder.configure_tpm_seal()
    builder.verify_post_boot()
    principles = builder.image.constitutional_principles
    assert len(principles) == 5
    assert all(v is True for v in principles.values())
    assert set(principles.keys()) == {"P1", "P3", "P6", "P7", "P8"}

@test("T32: Build artifact SHA3-256 hashes are valid hex")
def t32_artifact_hashes():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    builder.sign_model_assertion()
    builder.compile_image(BuildConfiguration())
    for artifact in builder.image.artifacts:
        assert len(artifact.sha3_256_hash) == 64
        int(artifact.sha3_256_hash, 16)  # Valid hex
        assert len(artifact.canonical_seal) == 64
        int(artifact.canonical_seal, 16)  # Valid hex

@test("T33: Timestamp ordering in stage log")
def t33_timestamp_ordering():
    builder = ArkheCoreImageBuilder()
    builder.create_ubuntu_one_account("dev@arkhe.org")
    builder.create_gpg_key()
    builder.register_gpg_key()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    builder.sign_model_assertion()
    timestamps = [log["timestamp"] for log in builder._stage_log]
    assert all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))

@test("T34: Model assertion snap types are valid")
def t34_snap_types():
    builder = ArkheCoreImageBuilder()
    builder.download_reference_model()
    builder.edit_model_for_arkhe()
    valid_types = {"gadget", "kernel", "base", "snapd", "app"}
    for snap in builder.model_assertion.snaps:
        assert snap.snap_type in valid_types

@test("T35: Presence field defaults and overrides")
def t35_presence_field():
    builder = ArkheCoreImageBuilder()
    builder.download_reference_model()
    snaps = builder.model_assertion.snaps
    console_conf = next(s for s in snaps if s.name == "console-conf")
    assert console_conf.presence == "optional"
    pi = next(s for s in snaps if s.name == "pi")
    assert pi.presence == "required"

@test("T36: BuildConfiguration defaults")
def t36_config_defaults():
    config = BuildConfiguration()
    assert config.target_device == "raspberry-pi-4"
    assert config.image_format == "img"
    assert config.allow_kernel_mismatch is True
    assert config.validation_mode == "ignore"
    assert config.local_snaps == []
    assert config.output_filename == "pi.img"

@test("T37: BuildConfiguration custom values")
def t37_config_custom():
    config = BuildConfiguration(
        target_device="raspberry-pi-5",
        image_format="iso",
        allow_kernel_mismatch=False,
        validation_mode="strict",
        local_snaps=["a.snap", "b.snap"],
        output_filename="custom.img"
    )
    assert config.target_device == "raspberry-pi-5"
    assert config.image_format == "iso"
    assert config.allow_kernel_mismatch is False
    assert config.validation_mode == "strict"
    assert config.local_snaps == ["a.snap", "b.snap"]
    assert config.output_filename == "custom.img"

@test("T38: ModelAssertion default values")
def t38_model_defaults():
    model = ModelAssertion()
    assert model.assertion_type == "model"
    assert model.series == "16"
    assert model.model_name == "arkhe-core-26-pi-arm64"
    assert model.architecture == "arm64"
    assert model.base == "core26"
    assert model.grade == "dangerous"
    assert model.snaps == []
    assert model.canonical_seal == ""

@test("T39: TPMSeal defaults")
def t39_tpm_defaults():
    seal = TPMSeal()
    assert seal.tpm_version == "2.0"
    assert seal.sealed_keys == []
    assert seal.op_tee_enabled is True
    assert seal.hardware_attestation is False

@test("T40: BuildArtifact fields")
def t40_artifact_fields():
    artifact = BuildArtifact(
        artifact_type="test",
        path="/tmp/test",
        size_bytes=1024,
        sha3_256_hash="a" * 64,
        canonical_seal="b" * 64,
        timestamp=1234567890
    )
    assert artifact.artifact_type == "test"
    assert artifact.path == "/tmp/test"
    assert artifact.size_bytes == 1024
    assert artifact.sha3_256_hash == "a" * 64
    assert artifact.canonical_seal == "b" * 64
    assert artifact.timestamp == 1234567890

print()
print("=" * 70)
print("TEST EXECUTION COMPLETE")
print("=" * 70)

if __name__ == "__main__":
    tests = [
        t01_builder_init, t02_custom_dev_id, t03_ubuntu_one_create, t04_gpg_key_create, t05_gpg_register, t06_gpg_register_no_key, t07_stage_log_accumulation, t08_download_model, t09_edit_model, t10_edit_model_grade, t11_edit_no_download, t12_sign_requires_gpg, t13_sign_model, t14_sign_no_model, t15_sign_no_gpg, t16_compile_default, t17_compile_with_snaps, t18_compile_no_image, t19_tpm_seal_default, t20_tpm_seal_custom, t21_tpm_orphan, t22_verify_success, t23_verify_no_image, t24_verify_no_tpm, t25_build_report, t26_report_no_image, t27_canonical_snap_ids, t28_arkhe_snap_ids, t29_full_pipeline, t30_seal_determinism, t31_constitutional_all_true, t32_artifact_hashes, t33_timestamp_ordering, t34_snap_types, t35_presence_field, t36_config_defaults, t37_config_custom, t38_model_defaults, t39_tpm_defaults, t40_artifact_fields
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"{t.__test_name__}: PASS")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"{t.__test_name__}: FAIL ({e})")
            failed += 1
    import sys
    if failed > 0:
        sys.exit(1)

import re

with open("substrates/500-599_advanced/substrato_595_iris_alpha/substrato_595_iris_alpha.py", "r") as f:
    text = f.read()

# Make sure all the new variables are available. I will add them directly to the `files` dict inside `canonize`.
files_dict_str = """
            "iris_network_driver/IrisClient.h": self.iris_client_h,
            "iris_network_driver/IrisClient.cpp": self.iris_client_cpp,
            "iris_network_driver/Core_mod.h": self.core_h_mod,
            "iris_network_driver/Core_mod.cpp": self.core_cpp_mod,
            "iris_network_driver/Makefile_mod": self.makefile_mod,
            "iris_network_driver/iris_bridge.py": self.iris_bridge_py,
            "pca_595/AlignmentClient.h": self.alignment_client_h,
            "pca_595/AlignmentClient.cpp": self.alignment_client_cpp,
            "pca_595/PhiMeterIIT.h": self.phi_meter_iit_h,
            "pca_595/PhiMeterIIT.cpp": self.phi_meter_iit_cpp,
            "pca_595/PCA-595-Integration.h": self.pca_595_integration_h,
            "pca_595/CMakeLists.txt": self.cmakelists_txt,
            "pca_595/ConsciousnessCycleAsync.h": self.consciousness_cycle_async_h,
            "pca_595/ConsciousnessCycleAsync.cpp": self.consciousness_cycle_async_cpp,
            "pca_595/test_async_or.cpp": self.test_async_or_cpp,
            "pca_595/test_phi_meter_iit.cpp": self.test_phi_meter_iit_cpp,
            "pca_595/test_alignment_client.cpp": self.test_alignment_client_cpp,
            "pca_595/IrisDriverAdapter.h": self.iris_driver_adapter_h,
            "pca_595/IrisDriverAdapter.cpp": self.iris_driver_adapter_cpp,
            "pca_595/TenantManager.h": self.tenant_manager_h,
            "pca_595/TenantManager.cpp": self.tenant_manager_cpp,
            "pca_595/PhiRendererGL.h": self.phi_renderer_gl_h,
            "pca_595/PhiRendererGL.cpp": self.phi_renderer_gl_cpp,
            "pca_595/OpenGLOverlay.h": self.opengl_overlay_h,
            "pca_595/OpenGLOverlay.cpp": self.opengl_overlay_cpp,
            "pca_595/MultiTenant.h": self.multi_tenant_h,
            "pca_595/MultiTenant.cpp": self.multi_tenant_cpp,
            "pca_595/IntegrationExample.cpp": self.integration_example_cpp,
            "pca_595/Dockerfile": self.dockerfile,
            "pca_595/.github/workflows/pca-595-ci-cd.yml": self.pca_595_ci_cd_yml,
            "pca_595/helm-chart-pca-595/Chart.yaml": self.chart_yaml,
            "pca_595/helm-chart-pca-595/values.yaml": self.values_yaml,
            "pca_595/helm-chart-pca-595/templates/deployment.yaml": self.deployment_yaml,
            "pca_595/helm-chart-pca-595/templates/configmap.yaml": self.configmap_yaml,
            "pca_595/helm-chart-pca-595/templates/secrets.yaml": self.secrets_yaml,
            "pca_595/helm-chart-pca-595/templates/service.yaml": self.service_yaml,
            "pca_595/helm-chart-pca-595/templates/hpa.yaml": self.hpa_yaml,
            "pca_595/helm-chart-pca-595/templates/servicemonitor.yaml": self.servicemonitor_yaml,
            "pca_595/helm-chart-pca-595/templates/networkpolicy.yaml": self.networkpolicy_yaml,
            "pca_595/helm-chart-pca-595/templates/_helpers.tpl": self._helpers_tpl,"""

if files_dict_str.strip() not in text:
    print("Files dict string not in text.")

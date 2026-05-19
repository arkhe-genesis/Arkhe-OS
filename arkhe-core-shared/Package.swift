// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ArkheCoreShared",
    products: [
        .library(
            name: "ArkheCoreShared",
            targets: ["ArkheCoreShared"]
        ),
    ],
    targets: [
        .target(
            name: "ArkheCoreShared",
            path: "Sources/ArkheCoreShared" // Dummy path to satisfy SPM, real integration would use xcframework
        ),
    ]
)

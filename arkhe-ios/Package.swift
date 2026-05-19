// swift-tools-version: 5.9
// Package.swift — Canon: ∞.Ω.∇+++.246.ios_package

import PackageDescription

let package = Package(
    name: "ArkheCore",
    platforms: [
        .iOS(.v15),
        .macOS(.v13),
        .watchOS(.v9),
        .tvOS(.v16)
    ],
    products: [
        .library(
            name: "ArkheCore",
            targets: ["ArkheCore"]
        ),
    ],
    dependencies: [
        .package(path: "../arkhe-core-shared"),
        .package(url: "https://github.com/apple/swift-crypto", from: "3.0.0"),
    ],
    targets: [
        .target(
            name: "ArkheCore",
            dependencies: [
                .product(name: "ArkheCoreShared", package: "arkhe-core-shared"),
                .product(name: "Crypto", package: "swift-crypto"),
            ],
            path: "Sources/ArkheCore",
            swiftSettings: [
                .define("ARKHE_CANON", .when(configuration: .release)),
                .define("ARKHE_SUBSTRATE_246"),
            ]
        ),
        .testTarget(
            name: "ArkheCoreTests",
            dependencies: ["ArkheCore"],
            path: "Tests/ArkheCoreTests"
        ),
    ]
)

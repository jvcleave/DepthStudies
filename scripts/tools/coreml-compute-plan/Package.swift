// swift-tools-version: 6.2

import PackageDescription

let package = Package(
    name: "CoreMLComputePlanReport",
    platforms: [
        .macOS(.v15),
    ],
    products: [
        .executable(name: "coreml-compute-plan-report", targets: ["CoreMLComputePlanReport"]),
    ],
    targets: [
        .executableTarget(name: "CoreMLComputePlanReport"),
    ]
)

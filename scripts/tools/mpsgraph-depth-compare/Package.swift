// swift-tools-version: 6.2

import PackageDescription

let package = Package(
    name: "MPSGraphDepthCompare",
    platforms: [
        .macOS("27.0"),
    ],
    products: [
        .executable(name: "mpsgraph-depth-compare", targets: ["MPSGraphDepthCompare"]),
    ],
    targets: [
        .executableTarget(name: "MPSGraphDepthCompare"),
    ],
    swiftLanguageModes: [.v5]
)

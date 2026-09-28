import CoreML
import CryptoKit
import Darwin
import Foundation

private enum ToolError: Error, CustomStringConvertible {
    case usage(String)
    case unsupportedModelStructure

    var description: String {
        switch self {
        case let .usage(message):
            message
        case .unsupportedModelStructure:
            "The model is not an ML Program."
        }
    }
}

private enum RequestedComputeUnits: String, CaseIterable, Codable {
    case all
    case cpuAndGPU = "cpu-and-gpu"
    case cpuAndNeuralEngine = "cpu-and-neural-engine"

    var coreMLValue: MLComputeUnits {
        switch self {
        case .all:
            .all
        case .cpuAndGPU:
            .cpuAndGPU
        case .cpuAndNeuralEngine:
            .cpuAndNeuralEngine
        }
    }

    var displayName: String {
        switch self {
        case .all:
            "All"
        case .cpuAndGPU:
            "CPU + GPU"
        case .cpuAndNeuralEngine:
            "CPU + Neural Engine"
        }
    }
}

private struct Arguments {
    let modelURL: URL
    let outputURL: URL
    let computeUnits: [RequestedComputeUnits]

    static func parse(_ arguments: [String]) throws -> Arguments {
        var modelPath: String?
        var outputPath: String?
        var computeUnits = RequestedComputeUnits.allCases
        var index = 0

        while index < arguments.count {
            switch arguments[index] {
            case "--model":
                index += 1
                guard index < arguments.count else {
                    throw ToolError.usage("--model requires a path")
                }
                modelPath = arguments[index]
            case "--output":
                index += 1
                guard index < arguments.count else {
                    throw ToolError.usage("--output requires a .json path")
                }
                outputPath = arguments[index]
            case "--compute-units":
                index += 1
                guard index < arguments.count else {
                    throw ToolError.usage("--compute-units requires a comma-separated value")
                }
                computeUnits = try arguments[index].split(separator: ",").map { value in
                    guard let parsed = RequestedComputeUnits(rawValue: String(value)) else {
                        throw ToolError.usage(
                            "Unknown compute-units value '\(value)'. Expected all, cpu-and-gpu, or cpu-and-neural-engine."
                        )
                    }
                    return parsed
                }
            case "--help", "-h":
                throw ToolError.usage(Self.usage)
            default:
                throw ToolError.usage("Unknown argument: \(arguments[index])\n\n\(Self.usage)")
            }
            index += 1
        }

        guard let modelPath else {
            throw ToolError.usage("Missing --model\n\n\(Self.usage)")
        }
        guard let outputPath else {
            throw ToolError.usage("Missing --output\n\n\(Self.usage)")
        }
        guard !computeUnits.isEmpty else {
            throw ToolError.usage("--compute-units must contain at least one value")
        }

        let workingDirectory = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        let modelURL = URL(fileURLWithPath: modelPath, relativeTo: workingDirectory).standardizedFileURL
        let outputURL = URL(fileURLWithPath: outputPath, relativeTo: workingDirectory).standardizedFileURL
        guard outputURL.pathExtension == "json" else {
            throw ToolError.usage("--output must end in .json")
        }
        guard FileManager.default.fileExists(atPath: modelURL.path) else {
            throw ToolError.usage("Model does not exist: \(modelURL.path)")
        }

        return Arguments(modelURL: modelURL, outputURL: outputURL, computeUnits: computeUnits)
    }

    static let usage = """
    Usage:
      coreml-compute-plan-report \\
        --model /path/to/Model.mlpackage \\
        --output /path/to/report.json \\
        [--compute-units all,cpu-and-gpu,cpu-and-neural-engine]

    The command writes the JSON report and a Markdown summary with the same base name.
    """
}

private struct Report: Codable {
    let schemaVersion: Int
    let generatedAt: String
    let host: HostReport
    let model: ModelReport
    let availableComputeDevices: [String]
    let plans: [PlanReport]
    let limitations: [String]
}

private struct HostReport: Codable {
    let hardwareModel: String
    let operatingSystem: String
    let processArchitecture: String
    let developerTools: String
}

private struct ModelReport: Codable {
    let name: String
    let sourceFileName: String
    let sourceTreeSHA256: String
    let functionNames: [String]
}

private struct PlanReport: Codable {
    let requestedComputeUnits: RequestedComputeUnits
    let operations: [OperationReport]
    let summary: PlanSummary
}

private struct OperationReport: Codable {
    let path: String
    let operatorName: String
    let inputBindings: [String: [String]]
    let outputNames: [String]
    let preferredComputeDevice: String?
    let supportedComputeDevices: [String]
    let estimatedCostWeight: Double?
}

private struct PlanSummary: Codable {
    let operationCount: Int
    let preferredDeviceCounts: [String: Int]
    let estimatedCostWeightByPreferredDevice: [String: Double]
    let operatorCounts: [String: Int]
    let operationsWithoutDeviceUsage: Int
    let operationsWithoutEstimatedCost: Int
}

@main
private enum CoreMLComputePlanReportMain {
    static func main() async {
        do {
            let arguments = try Arguments.parse(Array(CommandLine.arguments.dropFirst()))
            let report = try await makeReport(arguments: arguments)
            try write(report: report, to: arguments.outputURL)
            let markdownURL = arguments.outputURL.deletingPathExtension().appendingPathExtension("md")
            try renderMarkdown(report: report).write(to: markdownURL, atomically: true, encoding: .utf8)
            print("Wrote \(arguments.outputURL.path)")
            print("Wrote \(markdownURL.path)")
        } catch let error as ToolError {
            FileHandle.standardError.write(Data("error: \(error.description)\n".utf8))
            exit(EXIT_FAILURE)
        } catch {
            FileHandle.standardError.write(Data("error: \(error)\n".utf8))
            exit(EXIT_FAILURE)
        }
    }

    private static func makeReport(arguments: Arguments) async throws -> Report {
        let compiledURL: URL
        if arguments.modelURL.pathExtension == "mlmodelc" {
            compiledURL = arguments.modelURL
        } else {
            print("Compiling \(arguments.modelURL.lastPathComponent)…")
            compiledURL = try await MLModel.compileModel(at: arguments.modelURL)
        }

        var plans: [PlanReport] = []
        var programForMetadata: MLModelStructure.Program?

        for requestedUnits in arguments.computeUnits {
            print("Loading compute plan for \(requestedUnits.displayName)…")
            let configuration = MLModelConfiguration()
            configuration.computeUnits = requestedUnits.coreMLValue
            let computePlan = try await MLComputePlan.load(contentsOf: compiledURL, configuration: configuration)
            guard case let .program(program) = computePlan.modelStructure else {
                throw ToolError.unsupportedModelStructure
            }
            programForMetadata = program
            plans.append(makePlanReport(program: program, computePlan: computePlan, requestedUnits: requestedUnits))
        }

        guard let programForMetadata else {
            throw ToolError.unsupportedModelStructure
        }

        return Report(
            schemaVersion: 1,
            generatedAt: ISO8601DateFormatter().string(from: Date()),
            host: HostReport(
                hardwareModel: sysctlString("hw.model") ?? "unknown",
                operatingSystem: ProcessInfo.processInfo.operatingSystemVersionString,
                processArchitecture: processArchitecture,
                developerTools: commandOutput(executable: "/usr/bin/xcodebuild", arguments: ["-version"])
                    ?? "unknown"
            ),
            model: ModelReport(
                name: arguments.modelURL.deletingPathExtension().lastPathComponent,
                sourceFileName: arguments.modelURL.lastPathComponent,
                sourceTreeSHA256: try treeSHA256(at: arguments.modelURL),
                functionNames: programForMetadata.functions.keys.sorted()
            ),
            availableComputeDevices: MLComputeDevice.allComputeDevices.map(deviceName).sorted(),
            plans: plans,
            limitations: [
                "Core ML's public MLModelStructure.Program.ValueType API does not expose per-operation tensor shapes or data types. Correlate operation paths and output names with the source MIL inventory.",
                "MLComputePlan reports anticipated device usage and estimated relative cost; it is not a runtime trace.",
            ]
        )
    }

    private static func makePlanReport(
        program: MLModelStructure.Program,
        computePlan: MLComputePlan,
        requestedUnits: RequestedComputeUnits
    ) -> PlanReport {
        var operations: [OperationReport] = []

        for functionName in program.functions.keys.sorted() {
            guard let function = program.functions[functionName] else { continue }
            appendOperations(
                in: function.block,
                pathPrefix: functionName,
                computePlan: computePlan,
                destination: &operations
            )
        }

        var preferredDeviceCounts: [String: Int] = [:]
        var estimatedCostByDevice: [String: Double] = [:]
        var operatorCounts: [String: Int] = [:]
        var operationsWithoutDeviceUsage = 0
        var operationsWithoutEstimatedCost = 0

        for operation in operations {
            operatorCounts[operation.operatorName, default: 0] += 1
            if let preferred = operation.preferredComputeDevice {
                preferredDeviceCounts[preferred, default: 0] += 1
                if let weight = operation.estimatedCostWeight {
                    estimatedCostByDevice[preferred, default: 0] += weight
                }
            } else {
                operationsWithoutDeviceUsage += 1
            }
            if operation.estimatedCostWeight == nil {
                operationsWithoutEstimatedCost += 1
            }
        }

        return PlanReport(
            requestedComputeUnits: requestedUnits,
            operations: operations,
            summary: PlanSummary(
                operationCount: operations.count,
                preferredDeviceCounts: preferredDeviceCounts,
                estimatedCostWeightByPreferredDevice: estimatedCostByDevice,
                operatorCounts: operatorCounts,
                operationsWithoutDeviceUsage: operationsWithoutDeviceUsage,
                operationsWithoutEstimatedCost: operationsWithoutEstimatedCost
            )
        )
    }

    private static func appendOperations(
        in block: MLModelStructure.Program.Block,
        pathPrefix: String,
        computePlan: MLComputePlan,
        destination: inout [OperationReport]
    ) {
        for (operationIndex, operation) in block.operations.enumerated() {
            let operationPath = "\(pathPrefix).\(operationIndex)"
            let usage = computePlan.deviceUsage(for: operation)
            let cost = computePlan.estimatedCost(of: operation)
            let bindings = operation.inputs.mapValues { argument in
                argument.bindings.map { binding in
                    switch binding {
                    case let .name(name):
                        return name
                    case .value:
                        return "<constant>"
                    @unknown default:
                        return "<unknown>"
                    }
                }
            }
            destination.append(
                OperationReport(
                    path: operationPath,
                    operatorName: operation.operatorName,
                    inputBindings: bindings,
                    outputNames: operation.outputs.map(\.name),
                    preferredComputeDevice: usage.map { deviceName($0.preferred) },
                    supportedComputeDevices: usage?.supported.map(deviceName).sorted() ?? [],
                    estimatedCostWeight: cost?.weight
                )
            )

            for (blockIndex, nestedBlock) in operation.blocks.enumerated() {
                appendOperations(
                    in: nestedBlock,
                    pathPrefix: "\(operationPath).block\(blockIndex)",
                    computePlan: computePlan,
                    destination: &destination
                )
            }
        }
    }

    private static func write(report: Report, to outputURL: URL) throws {
        try FileManager.default.createDirectory(
            at: outputURL.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        try encoder.encode(report).write(to: outputURL, options: .atomic)
    }

    private static func renderMarkdown(report: Report) -> String {
        var lines: [String] = [
            "# \(report.model.name) Core ML Compute Plan",
            "",
            "Generated: `\(report.generatedAt)`",
            "",
            "- Hardware: `\(report.host.hardwareModel)`",
            "- OS: `\(report.host.operatingSystem)`",
            "- Architecture: `\(report.host.processArchitecture)`",
            "- Developer tools: `\(report.host.developerTools.replacingOccurrences(of: "\n", with: "; "))`",
            "- Source tree SHA-256: `\(report.model.sourceTreeSHA256)`",
            "- Available devices: \(report.availableComputeDevices.map { "`\($0)`" }.joined(separator: ", "))",
            "",
        ]

        for plan in report.plans {
            lines.append("## \(plan.requestedComputeUnits.displayName)")
            lines.append("")
            lines.append("| Preferred device | Operation count | Estimated cost weight |")
            lines.append("| --- | ---: | ---: |")
            let devices = Set(plan.summary.preferredDeviceCounts.keys)
                .union(plan.summary.estimatedCostWeightByPreferredDevice.keys)
                .sorted()
            for device in devices {
                let count = plan.summary.preferredDeviceCounts[device, default: 0]
                let cost = plan.summary.estimatedCostWeightByPreferredDevice[device, default: 0]
                lines.append("| \(device) | \(count) | \(format(cost)) |")
            }
            lines.append("| Unreported | \(plan.summary.operationsWithoutDeviceUsage) | — |")
            lines.append("")
            lines.append("Operations without an estimated cost: \(plan.summary.operationsWithoutEstimatedCost).")
            lines.append("")

            let nonPrimaryOperations = plan.operations
                .filter { operation in
                    guard let device = operation.preferredComputeDevice else { return false }
                    switch plan.requestedComputeUnits {
                    case .cpuAndNeuralEngine:
                        return device != "Neural Engine"
                    case .cpuAndGPU:
                        return device != "GPU"
                    case .all:
                        return device != "Neural Engine"
                    }
                }
                .sorted {
                    ($0.estimatedCostWeight ?? -1, $0.path) > ($1.estimatedCostWeight ?? -1, $1.path)
                }

            lines.append("### Highest-cost non-primary operations")
            lines.append("")
            if nonPrimaryOperations.isEmpty {
                lines.append("None reported.")
            } else {
                lines.append("| Path | Operator | Preferred device | Estimated cost weight | Outputs |")
                lines.append("| --- | --- | --- | ---: | --- |")
                for operation in nonPrimaryOperations.prefix(25) {
                    let weight = operation.estimatedCostWeight.map(format) ?? "—"
                    lines.append(
                        "| `\(operation.path)` | `\(operation.operatorName)` | \(operation.preferredComputeDevice ?? "Unreported") | \(weight) | \(operation.outputNames.map { "`\($0)`" }.joined(separator: ", ")) |"
                    )
                }
            }
            lines.append("")
        }

        lines.append("## Limitations")
        lines.append("")
        lines.append(contentsOf: report.limitations.map { "- \($0)" })
        lines.append("")
        lines.append("The adjacent JSON file is the authoritative machine-readable report.")
        lines.append("")
        return lines.joined(separator: "\n")
    }
}

private func deviceName(_ device: MLComputeDevice) -> String {
    switch device {
    case .cpu:
        "CPU"
    case .gpu:
        "GPU"
    case .neuralEngine:
        "Neural Engine"
    @unknown default:
        device.description
    }
}

private func format(_ value: Double) -> String {
    String(format: "%.6f", value)
}

private var processArchitecture: String {
#if arch(arm64)
    "arm64"
#elseif arch(x86_64)
    "x86_64"
#else
    "unknown"
#endif
}

private func sysctlString(_ name: String) -> String? {
    var size = 0
    guard sysctlbyname(name, nil, &size, nil, 0) == 0, size > 0 else { return nil }
    var value = [CChar](repeating: 0, count: size)
    guard sysctlbyname(name, &value, &size, nil, 0) == 0 else { return nil }
    let bytes = value.prefix { $0 != 0 }.map { UInt8(bitPattern: $0) }
    return String(decoding: bytes, as: UTF8.self)
}

private func commandOutput(executable: String, arguments: [String]) -> String? {
    let process = Process()
    let output = Pipe()
    process.executableURL = URL(fileURLWithPath: executable)
    process.arguments = arguments
    process.standardOutput = output
    process.standardError = Pipe()
    do {
        try process.run()
        process.waitUntilExit()
        guard process.terminationStatus == 0 else { return nil }
        let data = output.fileHandleForReading.readDataToEndOfFile()
        return String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines)
    } catch {
        return nil
    }
}

private func treeSHA256(at rootURL: URL) throws -> String {
    var isDirectory: ObjCBool = false
    FileManager.default.fileExists(atPath: rootURL.path, isDirectory: &isDirectory)
    let fileURLs: [URL]
    if isDirectory.boolValue {
        let keys: [URLResourceKey] = [.isRegularFileKey]
        let enumerator = FileManager.default.enumerator(
            at: rootURL,
            includingPropertiesForKeys: keys,
            options: [.skipsHiddenFiles]
        )
        fileURLs = (enumerator?.allObjects as? [URL] ?? []).filter { url in
            (try? url.resourceValues(forKeys: Set(keys)).isRegularFile) == true
        }.sorted { lhs, rhs in
            lhs.path.replacingOccurrences(of: rootURL.path, with: "")
                < rhs.path.replacingOccurrences(of: rootURL.path, with: "")
        }
    } else {
        fileURLs = [rootURL]
    }

    var hasher = SHA256()
    for fileURL in fileURLs {
        let relativePath = fileURL.path.replacingOccurrences(of: rootURL.path, with: "")
        hasher.update(data: Data(relativePath.utf8))
        let handle = try FileHandle(forReadingFrom: fileURL)
        defer { try? handle.close() }
        while let data = try handle.read(upToCount: 1_048_576), !data.isEmpty {
            hasher.update(data: data)
        }
    }
    return hasher.finalize().map { String(format: "%02x", $0) }.joined()
}

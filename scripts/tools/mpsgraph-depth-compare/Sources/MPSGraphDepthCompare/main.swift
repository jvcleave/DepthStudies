import CryptoKit
import Darwin
import Foundation
import Metal
import MetalPerformanceShaders
import MetalPerformanceShadersGraph

private enum CompareError: Error, CustomStringConvertible
{
    case usage(String)
    case unavailable(String)
    case invalidGraph(String)
    case execution(String)

    var description: String
    {
        switch self
        {
            case let .usage(message), let .unavailable(message),
                 let .invalidGraph(message), let .execution(message):
                return message
        }
    }
}

private enum InputDataType: String, Codable
{
    case float32
    case float16

    var graphType: MPSDataType
    {
        switch self
        {
            case .float32: return .float32
            case .float16: return .float16
        }
    }

    var byteCount: Int
    {
        switch self
        {
            case .float32: return MemoryLayout<Float>.size
            case .float16: return MemoryLayout<Float16>.size
        }
    }
}

private struct Arguments
{
    let baselineURL: URL
    let candidateURL: URL
    let outputURL: URL
    let width: Int
    let height: Int
    let warmups: Int
    let iterations: Int
    let baselineInputDataType: InputDataType
    let candidateInputDataType: InputDataType
    let maximumNormalizedRMSE: Double
    let maximumAbsoluteError: Double

    static func parse(_ values: [String]) throws -> Arguments
    {
        var strings: [String: String] = [:]
        let validKeys: Set<String> = [
            "--baseline",
            "--candidate",
            "--output",
            "--width",
            "--height",
            "--warmups",
            "--iterations",
            "--baseline-input-data-type",
            "--candidate-input-data-type",
            "--maximum-normalized-rmse",
            "--maximum-absolute-error",
        ]
        var index = 0
        while index < values.count
        {
            let key = values[index]
            if key == "--help" || key == "-h"
            {
                throw CompareError.usage(usage)
            }
            guard key.hasPrefix("--"), index + 1 < values.count
            else { throw CompareError.usage("Invalid arguments\n\n\(usage)") }
            guard validKeys.contains(key)
            else { throw CompareError.usage("Unknown argument: \(key)\n\n\(usage)") }
            strings[key] = values[index + 1]
            index += 2
        }

        guard let baseline = strings["--baseline"],
              let candidate = strings["--candidate"],
              let output = strings["--output"],
              let width = strings["--width"].flatMap(Int.init),
              let height = strings["--height"].flatMap(Int.init)
        else { throw CompareError.usage("Missing a required argument\n\n\(usage)") }
        let warmups = strings["--warmups"].flatMap(Int.init) ?? 5
        let iterations = strings["--iterations"].flatMap(Int.init) ?? 30
        let baselineInputDataType = try parseInputDataType(
            strings["--baseline-input-data-type"] ?? "float32",
            option: "--baseline-input-data-type"
        )
        let candidateInputDataType = try parseInputDataType(
            strings["--candidate-input-data-type"] ?? "float16",
            option: "--candidate-input-data-type"
        )
        let maximumNormalizedRMSE = strings["--maximum-normalized-rmse"]
            .flatMap(Double.init) ?? 0.002
        let maximumAbsoluteError = strings["--maximum-absolute-error"]
            .flatMap(Double.init) ?? 0.0005
        guard width > 0, height > 0, warmups >= 0, iterations > 0
        else { throw CompareError.usage("Dimensions and iterations must be positive") }
        guard maximumNormalizedRMSE.isFinite, maximumNormalizedRMSE > 0,
              maximumAbsoluteError.isFinite, maximumAbsoluteError > 0
        else { throw CompareError.usage("Quality thresholds must be finite and positive") }

        let workingDirectory = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        let baselineURL = URL(fileURLWithPath: baseline, relativeTo: workingDirectory).standardizedFileURL
        let candidateURL = URL(fileURLWithPath: candidate, relativeTo: workingDirectory).standardizedFileURL
        let outputURL = URL(fileURLWithPath: output, relativeTo: workingDirectory).standardizedFileURL
        for packageURL in [baselineURL, candidateURL]
        {
            guard FileManager.default.fileExists(atPath: packageURL.path)
            else { throw CompareError.usage("Missing graph package: \(packageURL.path)") }
        }
        return Arguments(
            baselineURL: baselineURL,
            candidateURL: candidateURL,
            outputURL: outputURL,
            width: width,
            height: height,
            warmups: warmups,
            iterations: iterations,
            baselineInputDataType: baselineInputDataType,
            candidateInputDataType: candidateInputDataType,
            maximumNormalizedRMSE: maximumNormalizedRMSE,
            maximumAbsoluteError: maximumAbsoluteError
        )
    }

    private static func parseInputDataType(
        _ rawValue: String,
        option: String
    ) throws -> InputDataType
    {
        guard let inputDataType = InputDataType(rawValue: rawValue)
        else { throw CompareError.usage("\(option) must be float32 or float16") }
        return inputDataType
    }

    static let usage = """
    Usage:
      mpsgraph-depth-compare \\
        --baseline /path/to/Float32Input.mpsgraphpackage \\
        --candidate /path/to/Float16Input.mpsgraphpackage \\
        --width 384 --height 384 \\
        --output /path/to/report.json \\
        [--baseline-input-data-type float32] \\
        [--candidate-input-data-type float16] \\
        [--maximum-normalized-rmse 0.002] \\
        [--maximum-absolute-error 0.0005] \\
        [--warmups 5] [--iterations 30]
    """
}

private struct Report: Codable
{
    let schemaVersion: Int
    let generatedAt: String
    let host: Host
    let shape: [Int]
    let warmups: Int
    let iterations: Int
    let baseline: GraphResult
    let candidate: GraphResult
    let quality: Quality
}

private struct Host: Codable
{
    let hardwareModel: String
    let operatingSystem: String
    let gpu: String
}

private struct GraphResult: Codable
{
    let packageName: String
    let packageTreeSHA256: String
    let inputDataType: InputDataType
    let inputBytes: Int
    let timingsMilliseconds: TimingSummary
}

private struct TimingSummary: Codable
{
    let minimum: Double
    let median: Double
    let p90: Double
    let p99: Double
    let maximum: Double
    let mean: Double
}

private struct Quality: Codable
{
    let passed: Bool
    let maximumAllowedNormalizedRootMeanSquareError: Double
    let maximumAllowedAbsoluteError: Double
    let meanAbsoluteError: Double
    let maximumAbsoluteError: Double
    let rootMeanSquareError: Double
    let normalizedRootMeanSquareError: Double
    let minimumPSNRDecibels: Double
}

private final class GraphRunner
{
    let packageURL: URL
    let inputDataType: InputDataType
    let inputBuffer: MTLBuffer
    let outputBuffer: MTLBuffer
    private let executable: MPSGraphExecutable
    private let commandQueue: MTLCommandQueue
    private let inputTensor: MPSGraphTensorData
    private let outputTensor: MPSGraphTensorData

    init(
        packageURL: URL,
        inputDataType: InputDataType,
        width: Int,
        height: Int,
        device: MTLDevice
    ) throws
    {
        self.packageURL = packageURL
        self.inputDataType = inputDataType
        guard let commandQueue = device.makeCommandQueue()
        else { throw CompareError.unavailable("Could not create a Metal command queue") }
        self.commandQueue = commandQueue

        let descriptor = MPSGraphCompilationDescriptor()
        descriptor.optimizationLevel = .level0
        executable = MPSGraphExecutable(package: packageURL, descriptor: descriptor)
        executable.options = .none
        let inputShape: [NSNumber] = [1, 3, NSNumber(value: height), NSNumber(value: width)]
        let outputShape: [NSNumber] = [1, 1, NSNumber(value: height), NSNumber(value: width)]
        let outputTypes = executable.getOutputTypes(
            with: MPSGraphDevice(mtlDevice: device),
            inputTypes: [MPSGraphShapedType(shape: inputShape, dataType: inputDataType.graphType)],
            compilationDescriptor: descriptor
        )
        guard let outputTypes, outputTypes.count == 1,
              outputTypes[0].shape == outputShape,
              outputTypes[0].dataType == .float16
        else { throw CompareError.invalidGraph("Unexpected graph output for \(packageURL.lastPathComponent)") }

        let pixelCount = width * height
        guard let inputBuffer = device.makeBuffer(
            length: pixelCount * 3 * inputDataType.byteCount,
            options: .storageModeShared
        ), let outputBuffer = device.makeBuffer(
            length: pixelCount * MemoryLayout<Float16>.size,
            options: .storageModeShared
        )
        else { throw CompareError.unavailable("Could not allocate shared Metal buffers") }
        self.inputBuffer = inputBuffer
        self.outputBuffer = outputBuffer
        inputTensor = MPSGraphTensorData(
            inputBuffer,
            shape: inputShape,
            dataType: inputDataType.graphType
        )
        outputTensor = MPSGraphTensorData(
            outputBuffer,
            shape: outputShape,
            dataType: .float16
        )
    }

    func setInput(_ values: [Float])
    {
        switch inputDataType
        {
            case .float32:
                let destination = inputBuffer.contents().bindMemory(
                    to: Float.self,
                    capacity: values.count
                )
                for index in values.indices { destination[index] = values[index] }
            case .float16:
                let destination = inputBuffer.contents().bindMemory(
                    to: Float16.self,
                    capacity: values.count
                )
                for index in values.indices { destination[index] = Float16(values[index]) }
        }
    }

    func run() throws -> Double
    {
        guard let rawCommandBuffer = commandQueue.makeCommandBuffer()
        else { throw CompareError.unavailable("Could not create a command buffer") }
        let commandBuffer = MPSCommandBuffer(commandBuffer: rawCommandBuffer)
        let descriptor = MPSGraphExecutableExecutionDescriptor()
        let started = DispatchTime.now().uptimeNanoseconds
        _ = executable.encode(
            to: commandBuffer,
            inputs: [inputTensor],
            results: [outputTensor],
            executionDescriptor: descriptor
        )
        commandBuffer.commit()
        commandBuffer.waitUntilCompleted()
        guard rawCommandBuffer.status == .completed
        else
        {
            throw CompareError.execution(
                rawCommandBuffer.error?.localizedDescription ?? "Graph command failed"
            )
        }
        return Double(DispatchTime.now().uptimeNanoseconds - started) / 1_000_000
    }

    func output(count: Int) -> [Float]
    {
        let source = outputBuffer.contents().bindMemory(to: Float16.self, capacity: count)
        return (0 ..< count).map { Float(source[$0]) }
    }
}

@main
private enum MPSGraphDepthCompareMain
{
    static func main()
    {
        do
        {
            let arguments = try Arguments.parse(Array(CommandLine.arguments.dropFirst()))
            guard let device = MTLCreateSystemDefaultDevice()
            else { throw CompareError.unavailable("Metal is unavailable") }
            let baseline = try GraphRunner(
                packageURL: arguments.baselineURL,
                inputDataType: arguments.baselineInputDataType,
                width: arguments.width,
                height: arguments.height,
                device: device
            )
            let candidate = try GraphRunner(
                packageURL: arguments.candidateURL,
                inputDataType: arguments.candidateInputDataType,
                width: arguments.width,
                height: arguments.height,
                device: device
            )
            let input = makeInput(width: arguments.width, height: arguments.height)
            baseline.setInput(input)
            candidate.setInput(input)

            for index in 0 ..< arguments.warmups
            {
                if index.isMultiple(of: 2)
                {
                    _ = try baseline.run()
                    _ = try candidate.run()
                }
                else
                {
                    _ = try candidate.run()
                    _ = try baseline.run()
                }
            }

            var baselineTimings: [Double] = []
            var candidateTimings: [Double] = []
            for index in 0 ..< arguments.iterations
            {
                if index.isMultiple(of: 2)
                {
                    baselineTimings.append(try baseline.run())
                    candidateTimings.append(try candidate.run())
                }
                else
                {
                    candidateTimings.append(try candidate.run())
                    baselineTimings.append(try baseline.run())
                }
            }

            let pixelCount = arguments.width * arguments.height
            let baselineOutput = baseline.output(count: pixelCount)
            let candidateOutput = candidate.output(count: pixelCount)
            let quality = compare(
                baselineOutput,
                candidateOutput,
                maximumNormalizedRMSE: arguments.maximumNormalizedRMSE,
                allowedMaximumAbsoluteError: arguments.maximumAbsoluteError
            )
            let report = Report(
                schemaVersion: 1,
                generatedAt: ISO8601DateFormatter().string(from: Date()),
                host: Host(
                    hardwareModel: sysctlString("hw.model") ?? "unknown",
                    operatingSystem: ProcessInfo.processInfo.operatingSystemVersionString,
                    gpu: device.name
                ),
                shape: [1, 3, arguments.height, arguments.width],
                warmups: arguments.warmups,
                iterations: arguments.iterations,
                baseline: GraphResult(
                    packageName: arguments.baselineURL.lastPathComponent,
                    packageTreeSHA256: try treeSHA256(at: arguments.baselineURL),
                    inputDataType: arguments.baselineInputDataType,
                    inputBytes: pixelCount * 3 * arguments.baselineInputDataType.byteCount,
                    timingsMilliseconds: summarize(baselineTimings)
                ),
                candidate: GraphResult(
                    packageName: arguments.candidateURL.lastPathComponent,
                    packageTreeSHA256: try treeSHA256(at: arguments.candidateURL),
                    inputDataType: arguments.candidateInputDataType,
                    inputBytes: pixelCount * 3 * arguments.candidateInputDataType.byteCount,
                    timingsMilliseconds: summarize(candidateTimings)
                ),
                quality: quality
            )
            try write(report, to: arguments.outputURL)
            print(try jsonString(report))
            guard quality.passed else { exit(EXIT_FAILURE) }
        }
        catch let error as CompareError
        {
            FileHandle.standardError.write(Data("error: \(error.description)\n".utf8))
            exit(EXIT_FAILURE)
        }
        catch
        {
            FileHandle.standardError.write(Data("error: \(error)\n".utf8))
            exit(EXIT_FAILURE)
        }
    }
}

private func makeInput(width: Int, height: Int) -> [Float]
{
    let planeSize = width * height
    var values = [Float](repeating: 0, count: planeSize * 3)
    for y in 0 ..< height
    {
        for x in 0 ..< width
        {
            let index = y * width + x
            values[index] = Float((x * 255) / max(width - 1, 1))
            values[planeSize + index] = Float((y * 255) / max(height - 1, 1))
            values[2 * planeSize + index] = Float((x + y) % 256)
        }
    }
    return values
}

private func summarize(_ values: [Double]) -> TimingSummary
{
    let sorted = values.sorted()
    return TimingSummary(
        minimum: sorted.first ?? 0,
        median: percentile(sorted, 0.50),
        p90: percentile(sorted, 0.90),
        p99: percentile(sorted, 0.99),
        maximum: sorted.last ?? 0,
        mean: values.reduce(0, +) / Double(max(values.count, 1))
    )
}

private func percentile(_ sorted: [Double], _ fraction: Double) -> Double
{
    guard !sorted.isEmpty else { return 0 }
    let rank = fraction * Double(sorted.count - 1)
    let lower = Int(rank.rounded(.down))
    let upper = Int(rank.rounded(.up))
    if lower == upper { return sorted[lower] }
    let interpolation = rank - Double(lower)
    return sorted[lower] + (sorted[upper] - sorted[lower]) * interpolation
}

private func compare(
    _ baseline: [Float],
    _ candidate: [Float],
    maximumNormalizedRMSE: Double,
    allowedMaximumAbsoluteError: Double
) -> Quality
{
    var absoluteSum = 0.0
    var squareSum = 0.0
    var maximumAbsoluteError = 0.0
    var baselineMinimum = Double.greatestFiniteMagnitude
    var baselineMaximum = -Double.greatestFiniteMagnitude
    var baselinePeak = 0.0
    for index in baseline.indices
    {
        let reference = Double(baseline[index])
        let difference = reference - Double(candidate[index])
        let absolute = abs(difference)
        absoluteSum += absolute
        squareSum += difference * difference
        maximumAbsoluteError = max(maximumAbsoluteError, absolute)
        baselineMinimum = min(baselineMinimum, reference)
        baselineMaximum = max(baselineMaximum, reference)
        baselinePeak = max(baselinePeak, abs(reference))
    }
    let count = Double(max(baseline.count, 1))
    let rmse = sqrt(squareSum / count)
    let normalizedRMSE = rmse / max(baselinePeak, 1e-12)
    let referenceRange = max(baselineMaximum - baselineMinimum, 1e-12)
    let psnr = 20 * log10(referenceRange / max(rmse, 1e-12))
    return Quality(
        passed: normalizedRMSE <= maximumNormalizedRMSE
            && maximumAbsoluteError <= allowedMaximumAbsoluteError,
        maximumAllowedNormalizedRootMeanSquareError: maximumNormalizedRMSE,
        maximumAllowedAbsoluteError: allowedMaximumAbsoluteError,
        meanAbsoluteError: absoluteSum / count,
        maximumAbsoluteError: maximumAbsoluteError,
        rootMeanSquareError: rmse,
        normalizedRootMeanSquareError: normalizedRMSE,
        minimumPSNRDecibels: psnr
    )
}

private func write(_ report: Report, to outputURL: URL) throws
{
    try FileManager.default.createDirectory(
        at: outputURL.deletingLastPathComponent(),
        withIntermediateDirectories: true
    )
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
    try encoder.encode(report).write(to: outputURL, options: .atomic)
}

private func jsonString(_ report: Report) throws -> String
{
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
    return String(decoding: try encoder.encode(report), as: UTF8.self)
}

private func sysctlString(_ name: String) -> String?
{
    var size = 0
    guard sysctlbyname(name, nil, &size, nil, 0) == 0, size > 0 else { return nil }
    var value = [CChar](repeating: 0, count: size)
    guard sysctlbyname(name, &value, &size, nil, 0) == 0 else { return nil }
    let bytes = value.prefix { $0 != 0 }.map { UInt8(bitPattern: $0) }
    return String(decoding: bytes, as: UTF8.self)
}

private func treeSHA256(at rootURL: URL) throws -> String
{
    let keys: Set<URLResourceKey> = [.isRegularFileKey]
    let enumerator = FileManager.default.enumerator(
        at: rootURL,
        includingPropertiesForKeys: Array(keys),
        options: [.skipsHiddenFiles]
    )
    let fileURLs = (enumerator?.allObjects as? [URL] ?? []).filter { url in
        (try? url.resourceValues(forKeys: keys).isRegularFile) == true
    }.sorted { lhs, rhs in
        lhs.path.replacingOccurrences(of: rootURL.path, with: "")
            < rhs.path.replacingOccurrences(of: rootURL.path, with: "")
    }
    var hasher = SHA256()
    for fileURL in fileURLs
    {
        let relativePath = fileURL.path.replacingOccurrences(of: rootURL.path, with: "")
        hasher.update(data: Data(relativePath.utf8))
        let handle = try FileHandle(forReadingFrom: fileURL)
        defer { try? handle.close() }
        while let data = try handle.read(upToCount: 1_048_576), !data.isEmpty
        {
            hasher.update(data: data)
        }
    }
    return hasher.finalize().map { String(format: "%02x", $0) }.joined()
}

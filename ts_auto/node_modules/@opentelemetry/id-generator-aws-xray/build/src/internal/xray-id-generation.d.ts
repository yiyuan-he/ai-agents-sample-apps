export declare const TRACE_ID_BYTES = 16;
declare type RandomBytesGenerator = (numBytes: number) => string;
export declare function generateTraceId(generateRandomBytes: RandomBytesGenerator): string;
export declare function generateSpanId(generateRandomBytes: RandomBytesGenerator): string;
export {};
//# sourceMappingURL=xray-id-generation.d.ts.map
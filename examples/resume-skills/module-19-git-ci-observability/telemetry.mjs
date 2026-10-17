import { context, propagation, trace } from '@opentelemetry/api';
import { W3CTraceContextPropagator } from '@opentelemetry/core';
import { InMemorySpanExporter, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';

export function createTelemetry() {
  const exporter = new InMemorySpanExporter();
  const provider = new NodeTracerProvider({ spanProcessors: [new SimpleSpanProcessor(exporter)] });
  provider.register({ propagator: new W3CTraceContextPropagator() });
  return {
    tracer: provider.getTracer('placement-m19', '1.0.0'),
    spans: () => exporter.getFinishedSpans().map(span => ({
      name: span.name, kind: span.kind, trace_id: span.spanContext().traceId,
      span_id: span.spanContext().spanId, parent_span_id: span.parentSpanContext?.spanId ?? null,
      status: span.status.code, attributes: span.attributes,
      duration_ms: span.duration[0] * 1000 + span.duration[1] / 1e6,
    })),
    close: async () => { await provider.forceFlush(); await provider.shutdown(); context.disable(); propagation.disable(); trace.disable(); },
  };
}

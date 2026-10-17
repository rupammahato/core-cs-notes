export class AppError extends Error {
  constructor(status, code) {
    super(code);
    this.name = 'AppError';
    this.status = status;
    this.code = code;
  }
}

export function publicError(error) {
  if (error instanceof AppError) return { status: error.status, code: error.code };
  if (error?.type === 'entity.parse.failed') return { status: 400, code: 'invalid_json' };
  if (error?.type === 'entity.too.large') return { status: 413, code: 'body_too_large' };
  if (error?.type === 'encoding.unsupported' || error?.type === 'charset.unsupported') {
    return { status: 415, code: 'unsupported_encoding' };
  }
  if (error instanceof URIError) return { status: 400, code: 'invalid_path' };
  return { status: 500, code: 'internal_error' };
}

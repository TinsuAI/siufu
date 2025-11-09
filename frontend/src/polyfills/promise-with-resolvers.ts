// Polyfill for Promise.withResolvers to support Node.js < 22 runtimes
// inspired by https://tc39.es/ecma262/#sec-promise.withresolvers

if (typeof Promise.withResolvers !== 'function') {
  Promise.withResolvers = function withResolvers<T>() {
    let resolve!: (value: T | PromiseLike<T>) => void
    let reject!: (reason?: unknown) => void

    const promise = new Promise<T>((res, rej) => {
      resolve = res
      reject = rej
    })

    return { promise, resolve, reject }
  }
}

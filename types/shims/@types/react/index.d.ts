export namespace JSX {
  interface Element {}
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

export type ReactNode = any;
export type FC<P = {}> = (props: P) => any;

declare const React: {
  createElement: any;
  Fragment: any;
};

export default React;

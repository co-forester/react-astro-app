// src/global.d.ts

declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}
declare module 'react-dom/client';
declare module '*.png' {
  const value: string;
  export default value;
}
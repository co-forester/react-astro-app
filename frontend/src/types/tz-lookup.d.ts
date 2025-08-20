declare module 'tz-lookup' {
  const tzlookup: (lat: number, lon: number) => string;
  export default tzlookup;
}
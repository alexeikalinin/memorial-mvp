import {memorialPath} from '../navigation/links';
export function redirectSystemPath({path}:{path:string;initial:boolean}) {
  const memorial=memorialPath(path);
  if(memorial)return memorial;
  // Keep internal Router / Expo development paths intact; malformed external links go home.
  if(path.startsWith('/')&&!path.startsWith('//'))return path;
  return '/';
}

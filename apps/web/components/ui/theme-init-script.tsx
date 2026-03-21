export default function ThemeInitScript() {
  const script = `(function(){try{var s=localStorage.getItem('cleardrive-theme');var d=window.matchMedia('(prefers-color-scheme: dark)').matches;var t=(s==='light'||s==='dark')?s:(d?'dark':'light');if(t==='dark'){document.documentElement.classList.add('dark');}}catch(e){}})();`;

  return <script dangerouslySetInnerHTML={{ __html: script }} />;
}
